from flow_py_sdk import(
    flow_client,
    cadence,
    Tx,
    TransactionTemplates,
    ProposalKey,
)

import configparser
import asyncio
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from common.account_config import AccountConfig
from common import utils
from pathlib import Path

import logging

log = logging.getLogger(__name__)
utils.configureLogging()
# logging.basicConfig(level=logging.DEBUG)
# log.setLevel("DEBUG")

project_cwd = Path(os.getcwd())
config_path = project_cwd.joinpath("common", "config.ini")
config = configparser.ConfigParser()
config.read(config_path)

current_account_config = AccountConfig()

# Dictionary to control the project contracts to be deployed. The entries with the value = True are deployed, the ones with False are ignored.
project_files = {
    "BallotStandard" : True,
    "ElectionStandard": True,
    "VoteBoxStandard": True,
    "VoteBooth": True
}

# Use this dictionary to define which dependency contracts are to be deployed. Contracts whose value = True are deployed, other are ignored
project_dependencies = {
    "Crypto": True,
    "Burner": True,
    "MetadataViews": False,
    "NonFungibleToken": False,
    "ViewResolver": False,
    "FlowToken": False,
    "FlowServiceAccount": False,
    "FlowStorageFees": False,
    "RandomBeaconHistory": False,
    "FungibleToken": False,
    "FungibleTokenMetadataViews": False,
    "FlowExecutionParameters": False,
    "FlowFees": False
}

def test_stuff():
    log.info("Testing...")

class DeployContract():
    def __init__(self, contract_name: str, contract_source: str) -> None:
        super().__init__()
        
        # Allow only contract in the project files or dependencies to proceed
        if (project_files.__contains__(contract_name) or project_dependencies.__contains__(contract_name)):
            self.contract_name = contract_name
            self.contract_source = contract_source
        else:
            raise Exception("ERROR: Contract ", contract_name, " not found in this project!")

    async def run(self, ctx: AccountConfig):
        # Step 1: Create a client to connect to the Flow blockchain
        # flow_client function creates a client using the host and port configured in the AccountConfig object provided
        # Build the contract object as a dictionary entry
        contract = {
            "name": self.contract_name,
            "source": self.contract_source.read()
        }

        # Setup the hexadecimal version of the contract as well
        contract_source_hex = bytes(contract["source"], "UTF-8").hex()

        async with flow_client(
            host=ctx.access_node_host, port=ctx.access_node_port
        ) as client:
            signer_address = ctx.service_account["address"]
            signer_key_id = ctx.service_account["key_id"]
            signer = ctx.service_account["signer"]

            latest_block = await client.get_latest_block()
            proposer = await client.get_account_at_latest_block(
                address=signer_address.bytes
            )
            contract_name = cadence.String(contract["name"])
            contract_code = cadence.String(contract_source_hex)

            # Build the contract deploying transaction
            transaction = (
                Tx(
                    code=TransactionTemplates.addAccountContractTemplate,
                    reference_block_id=latest_block.id,
                    payer=signer_address,
                    proposal_key=ProposalKey(
                        key_address=signer_address,
                        key_id=signer_key_id,
                        key_sequence_number=proposer.keys[0].sequence_number
                    ),
                )
                .add_arguments(contract_name)
                .add_arguments(contract_code)
                .add_authorizers(signer_address)
                .with_envelope_signature(
                    signer_address,
                    signer_key_id,
                    signer
                )
            )

            # Submit transaction
            try:
                await client.execute_transaction(transaction)
                log.info(f"Contract {contract_name} successfully deployed to network at {ctx.access_node_host}:{ctx.access_node_port} for account {signer_address}")
            except Exception as deploy_ex:
                # Test if this Exception was due to an existing contract with the same name
                if (deploy_ex.args[0].__contains__("cannot overwrite existing contract")):
                    log.warning(f"Contract {contract_name} already exists in {ctx.service_account["address"]} account.")
                    # I need to update the proposer before attempting another transaction
                    latest_block = await client.get_latest_block()
                    proposer = await client.get_account_at_latest_block(
                        address=signer_address.bytes
                    )

                    transaction = (
                        Tx(
                            code=TransactionTemplates.updateAccountContractTemplate,
                            reference_block_id=latest_block.id,
                            payer=signer_address,
                            proposal_key=ProposalKey(
                                key_address=signer_address,
                                key_id=signer_key_id,
                                key_sequence_number=proposer.keys[0].sequence_number
                            ),
                        )
                        .add_arguments(contract_name)
                        .add_arguments(contract_code)
                        .add_authorizers(signer_address)
                        .with_envelope_signature(
                            signer_address,
                            signer_key_id,
                            signer
                        )
                    )
                    log.info("Trying an Update instead...")
                    try:
                        await client.execute_transaction(transaction)
                        log.info(f"Contract {contract_name} updated successfully to network at {ctx.access_node_host}:{ctx.access_node_port} for account {ctx.service_account["address"]}")
                    except Exception as update_ex:
                        log.error("Unable to update contract '{contract_name}' due to: ")
                        log.error(update_ex)
                        exit(-1 )

                else:
                    # The Exception was raised because of something else
                    log.error(f"Unable to deploy contract '{contract_name}' due to:")
                    log.error(deploy_ex)
                    exit(-1)


class DeleteContract():
    def __init__(self, contract_name: str) -> None:
        super().__init__()
        self.contract_name = contract_name

    # The contract removal function only needs the contract name
    async def run(self, ctx: AccountConfig):
        async with flow_client(
            host=ctx.access_node_host, port=ctx.access_node_port
        ) as client:
            signer_address = ctx.service_account["address"]
            signer_key_id = ctx.service_account["key_id"]
            signer = ctx.service_account["signer"]

            latest_block = await client.get_latest_block()
            proposer = await client.get_account_at_latest_block(
                address=signer_address.bytes
            )

            contract_name = cadence.String(self.contract_name)

            transaction = (
                Tx(
                    code=TransactionTemplates.removeAccountContractTemplate,
                    reference_block_id=latest_block.id,
                    payer=signer_address,
                    proposal_key=ProposalKey(
                        key_address=signer_address,
                        key_id=signer_key_id,
                        key_sequence_number=proposer.keys[0].sequence_number,
                    ),
                )
                .add_arguments(contract_name)
                .add_authorizers(signer_address)
                .with_envelope_signature(
                    signer_address,
                    signer_key_id,
                    signer,
                )
            )
            
            try:
                await client.execute_transaction(transaction)
            except Exception as e:
                log.error(f"Unable to delete contract '{contract_name}' due to:")
                log.error(e)
                exit(-1)


async def deployProjectDependencies():
    """
        Function to deploy (or update) all contract dependencies for the current project. The project dependencies are defined in the project_dependencies dictionary. The boolean value in each entry determines if the contract is to be deployed in the current run or not.
    """
    # Run through the set of contract dependencies and construct the project_dependencies_paths and project_dependencies_source dictionary
    project_dependencies_paths = {}
    project_dependencies_source = {}

    for dependency in project_dependencies:
        # If the contract flag is set to True, proceed with the rest
        if (project_dependencies[dependency]): 
            project_dependencies_paths[dependency] = Path(config.get("dependencies", dependency))
            project_dependencies_source[dependency] = open(project_dependencies_paths[dependency])

            current_dependency = DeployContract(contract_name=dependency, contract_source=project_dependencies_source[dependency])

            log.info(f"Deploying '{dependency}' dependency contract...")
            await current_dependency.run(ctx=current_account_config)
            log.info("Done!")


async def deployProjectContracts():
    """
        Function to deploy (or update) all project, i.e., non-dependency, contracts. The project contracts are defined in the project_files dictionary. The boolean value in each entry determines if the contract is to be deployed in the current run or not.
        NOTE: The project contracts have a rigid dependency structure that requires these to be deployed in the following order:
            BallotStandard -> ElectionStandard -> VoteBoxStandard -> VoteBooth
        As such, in order to guarantee this, I cannot deploy them in a for loop or something of the sort and I need to force the deployment order from above.
    """
    # 1. Deploy the base contract BallotStandard
    contract_path = Path(config.get("project", "BallotStandard"))
    contract_source = open(contract_path)

    ballot_standard_contract = DeployContract(contract_name="BallotStandard", contract_source=contract_source)

    log.info("1. Deploying the BallotStandard project contract...")
    try:
        await ballot_standard_contract.run(ctx=current_account_config)
        log.info("BallotStandard contract deployed successfully!")
    except Exception as e:
        log.error("Unable to deploy the BallotStandard contract: ")
        log.error(e)
        exit(-1)

    # 2. Deploy the base contract ElectionStandard
    contract_path = Path(config.get("project", "ElectionStandard"))
    contract_source = open(contract_path)

    election_standard_contract = DeployContract(contract_name="ElectionStandard", contract_source=contract_source)

    log.info("2. Deploying the ElectionStandard project contract...")
    try:
        await election_standard_contract.run(ctx=current_account_config)
        log.info("ElectionStandard contract deployed successfully!")
    except Exception as e:
        log.error("Unable to deploy the ElectionStandard contract: ")
        log.error(e)
        exit(-1)

    # 3. Deploy the base contract VoteBoxStandard
    contract_path = Path(config.get("project", "VoteBoxStandard"))
    contract_source = open(contract_path)

    votebox_standard_contract = DeployContract(contract_name="VoteBoxStandard", contract_source=contract_source)

    log.info("3. Deploying the VoteBoxStandard project contract...")
    try:
        await votebox_standard_contract.run(ctx=current_account_config)
        log.info("VoteBoxStandard contract deployed successfully!")
    except Exception as e:
        log.error("Unable to deploy the VoteBoxStandard contract: ")
        log.error(e)
        exit(-1)

    # 4. Deploy the base contract VoteBooth. This one needs an Bool argument provided to it as well
    contract_path = Path(config.get("project", "VoteBooth"))
    contract_source = open(contract_path)

    votebooth_contract = DeployContract(contract_name="VoteBooth", contract_source=contract_source)

    log.info("4. Deploying the VoteBooth project contract...")
    try:
        await votebooth_contract.run(ctx=current_account_config)
        log.info("VoteBooth contract deployed successfully!")
    except Exception as e:
        log.error("Unable to deploy the VoteBooth contract: ")
        log.error(e)
        exit(-1)


async def deployProject():
    """
    This function aggregates the DeployContract and UpdateContract (which I already combined into one) but to deploy all dependencies and all project contracts respective the defined order to produce a network environment ready to be used.
    """
    log.info(f"Deploying all project dependencies for network {current_account_config.access_node_host}:{current_account_config.access_node_port}...")
    await deployProjectDependencies()
    log.info("All project dependencies were deployed successfully!")

    log.info(f"Deploying all project contracts for network {current_account_config.access_node_host}:{current_account_config.access_node_port}...")
    await deployProjectContracts()
    log.info("All project contracts were deployed successfully!")


async def deleteProjectContracts():
    """
        Function to deploy all project contracts as defined in the project_files dictionary.
    """
    for project_contract in project_files:
        contract_to_delete = DeleteContract(contract_name=project_contract)

        log.info(f"Deleting '{project_contract}' from network {current_account_config.access_node_host}:{current_account_config.access_node_port} for account {current_account_config.service_account["address"]}")
        await contract_to_delete.run(ctx=current_account_config)
        log.info(f"Contract '{project_contract}' deleted successfully!")


async def deleteProjectDependencies():
    """
    Function to deploy all project dependencies as defined in the project_dependencies dictionary
    """
    for project_dependency in project_dependencies:
        dependency_to_delete = DeleteContract(contract_name=project_dependencies)

        log.info(f"Deleting '{project_dependency}' from network {current_account_config.access_node_host}:{current_account_config.access_node_port} for account {current_account_config.service_account["address"]}")

        await dependency_to_delete.run(ctx=current_account_config)
        log.info(f"Dependency '{project_dependency}' deleted successfully!")


async def resetNetwork():
    """
    This function aggregates the 'deleteProjectContracts' and 'deleteProjectDependencies' function to clear the configured network from all contracts and respective dependencies
    """
    log.info(f"Deleting all project contracts from network {current_account_config.access_node_host}:{current_account_config.access_node_port}...")
    await deleteProjectContracts()
    log.info("All project contracts deleted successfully!")

    # print(f"Deleting all project dependencies from network {current_account_config.access_node_host}:{current_account_config.access_node_port}...")
    # await deleteProjectDependencies()
    # print("All project dependencies deleted successfully!")


def main():
    # Grab argv 1 since 0 is the file's path
    option = sys.argv[1].lower().strip()

    if (option == "deploy"):
        log.info(f"Setting up network...")
        asyncio.run(deployProject())
        log.info(f"Project successfully set up!")
    elif (option == "clear"):
        log.info("Clearing up the network...")
        asyncio.run(resetNetwork())
        log.info(f"Project network cleared successfully!")
    else:
        if (option == ""):
            log.warning(f"Missing option", end="")
        else:
            log.warning(f"Unknown option: {option}", end="")
        
        log.warning("\nUsage: \n$python 01_contract_management.py <deploy|clear>")

main()
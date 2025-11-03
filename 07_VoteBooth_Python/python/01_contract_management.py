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
from pathlib import Path

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
    print("Testing...")

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
                print("Contract ", contract_name, " successfully deployed to network at ", ctx.access_node_host, ":", ctx.access_node_port, " for account ", signer_address)
            except Exception as ex:
                # Test if this Exception was due to an existing contract with the same name
                if (ex.args[0].__contains__("cannot overwrite existing contract")):
                    print("Contract ", contract_name, " already exists in ", ctx.service_account["address"], " account.")
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
                    print("Trying an Update instead...")
                    await client.execute_transaction(transaction)
                    print("Done!")


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

            await client.execute_transaction(transaction)


async def deployProjectDependencies():
    # Run through the set of contract dependencies and construct the project_dependencies_paths and project_dependencies_source dictionary
    project_dependencies_paths = {}
    project_dependencies_source = {}

    for dependency in project_dependencies:
        # If the contract flag is set to True, proceed with the rest
        if (project_dependencies[dependency]): 
            project_dependencies_paths[dependency] = Path(config.get("dependencies", dependency))
            project_dependencies_source[dependency] = open(project_dependencies_paths[dependency])

            current_dependency = DeployContract(contract_name=dependency, contract_source=project_dependencies_source[dependency])

            print("Deploying '", dependency, "' dependency contract...")
            asyncio.run(current_dependency.run(ctx=current_account_config))
            print("Done!")

async def deployProjectContracts():
    project_contract_paths = {}
    project_contract_source = {}

    for contract in project_files:
        if(project_files[contract]):
            project_contract_paths[contract] = Path(config.get("project", contract))
            project_contract_source[contract] = open(project_contract_paths[contract])

            current_contract = DeployContract(contract_name=contract, contract_source=project_contract_source[contract])

            print("Deploying '", contract, "' project contract...")
            asyncio.run(current_contract.run(ctx=current_account_config))
            print("Done!")


if __name__ == "__main__":
    print("MAIN: ")
    contract_name="BallotStandard"
    contract_path = Path(config.get("project", contract_name))
    contract_source = open(contract_path)
    deploy_contract = DeployContract(contract_name=contract_name, contract_source=contract_source)
    delete_contract = DeleteContract(contract_name=contract_name)

    print("Deleting ", contract_name, " contract...")
    asyncio.run(delete_contract.run(ctx=current_account_config))
    print("Done!")

    # print("Deploying ", contract_name, " contract...")
    # try:
    #     asyncio.run(deploy_contract.run(ctx=current_account_config))
    # except Exception as ex:
    #     print("WARNING: Contract '", contract_name, "' is already deployed into account ", current_account_config.service_account["address"])
    #     print(ex)
    # print("Done!")
    # asyncio.run(deployProjectDependencies())
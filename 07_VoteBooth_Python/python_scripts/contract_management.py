from flow_py_sdk import(
    flow_client,
    cadence,
    Tx,
    TransactionTemplates,
    ProposalKey,
    entities
)

import configparser
import asyncio
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from common.account_config import AccountConfig
from python_scripts.event_management import EventRunner
from python_scripts.cadence_scripts import ScriptRunner
from common import utils
from pathlib import Path
import time

import logging

log = logging.getLogger(__name__)
utils.configureLogging()
# logging.basicConfig(level=logging.DEBUG)
# log.setLevel("DEBUG")

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
    "ViewResolver": True,
    "FungibleToken": True,
    "NonFungibleToken": True,
    "MetadataViews": True,
    "FungibleTokenMetadataViews": True,
    "FlowToken": True,
    "RandomBeaconHistory": False,
    "FlowExecutionParameters": False,
    "FlowStorageFees": False,
    "FlowFees": False,
    "FlowServiceAccount": False,
}

contract_gas_limit: int = 100000

def test_stuff():
    log.info("Testing...")

class DeployContract():
    def __init__(self) -> None:
        super().__init__()
        
        # Allow only contract in the project files or dependencies to proceed
        self.ctx = AccountConfig()
        project_cwd: Path = Path(os.getcwd())
        config_path: Path = project_cwd.joinpath("common", "config.ini")
        self.config: configparser.ConfigParser = configparser.ConfigParser()
        self.config.read(config_path)

        self.event_runner: EventRunner = EventRunner()
        self.script_runner: ScriptRunner = ScriptRunner()
        self.encoding = self.config.get(section="encryption", option="encoding")

        
    async def run(self, contract_name: str, contract_source: str, update: bool) -> entities.TransactionResultResponse:
        # Validate the contract name at the top
        if (not project_files.__contains__(contract_name) or project_dependencies.__contains__(contract_name)):
            raise Exception(f"ERROR: Contract '{contract_name}' does not belong to the current project!")
        
        # Step 1: Create a client to connect to the Flow blockchain
        # flow_client function creates a client using the host and port configured in the AccountConfig object provided
        # Build the contract object as a dictionary entry
        contract = {
            "name": contract_name,
            "source": contract_source
        }

        # Setup the hexadecimal version of the contract as well
        contract_source_hex = bytes(contract["source"], self.encoding).hex()

        async with flow_client(
            host=self.ctx.access_node_host, port=self.ctx.access_node_port
        ) as client:
            signer_address = self.ctx.service_account["address"]
            signer_key_id = self.ctx.service_account["key_id"]
            signer = self.ctx.service_account["signer"]

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
                    address=signer_address,
                    key_id=signer_key_id,
                    signer=signer
                )
                .with_gas_limit(gas_limit=contract_gas_limit)
            )

            # Submit transaction
            try:
                tx_response: entities.TransactionResultResponse = await client.execute_transaction(transaction)
                log.info(f"Contract {contract_name} successfully deployed to network at {self.ctx.access_node_host}:{self.ctx.access_node_port} for account {signer_address}")

                return tx_response
            except Exception as deploy_ex:
                # Test if this Exception was due to an existing contract with the same name
                if (deploy_ex.args[0].__contains__("cannot overwrite existing contract")):
                    log.warning(f"Contract {contract_name} already exists in {self.ctx.service_account["address"]} account.")
                    # Check if the contract is set for update. Proceed if that is the case
                    if (update):
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
                                address=signer_address,
                                key_id=signer_key_id,
                                signer=signer
                            )
                            .with_gas_limit(gas_limit=contract_gas_limit)
                        )
                        log.info("Trying an Update instead...")
                        try:
                            tx_response: entities.TransactionResultResponse = await client.execute_transaction(transaction)
                            log.info(f"Contract {contract_name} updated successfully to network at {self.ctx.access_node_host}:{self.ctx.access_node_port} for account {self.ctx.service_account["address"]}")
                            return tx_response
                        
                        except Exception as update_ex:
                            log.error(f"Unable to update contract '{contract_name}' due to: ")
                            log.error(update_ex)
                            exit(-1 )
                    else:
                        # The contract already exists in the network and it is not supposed to be updated
                        log.info("Nothing else to do.")
                else:
                    # The Exception was raised because of something else
                    log.error(f"Unable to deploy contract '{contract_name}' due to:")
                    log.error(deploy_ex)
                    exit(-1)


    async def deployProjectDependencies(self):
        """
            Function to deploy (or update) all contract dependencies for the current project. The project dependencies are defined in the project_dependencies dictionary. The boolean value in each entry determines if the contract is to be deployed in the current run or not.
        """
        # Run through the set of contract dependencies and construct the project_dependencies_paths and project_dependencies_source dictionary
        project_dependencies_paths = {}
        project_dependencies_source = {}

        for dependency in project_dependencies:
            # If the contract flag is set to True, proceed with the rest. All dependencies can be processed through the same process, except for the FlowToken
            # contract. This one requires constructor arguments to be provided and that requires a special transaction.
            dependency_deployer: DeployContract = DeployContract()
            if (project_dependencies[dependency]): 
                project_dependencies_paths[dependency] = Path(self.config.get("dependencies", dependency))
                project_dependencies_source[dependency] = open(project_dependencies_paths[dependency])

                log.info(f"Deploying '{dependency}' dependency contract...")
                await dependency_deployer.run(contract_name=dependency, contract_source=project_dependencies_source[dependency].read(), update=False)
                log.info("Done!")


    async def deployProjectContracts(self, gas_results_file_path: Path = None, storage_results_file_path: Path = None) -> None:
        """
            Function to deploy (or update) all project, i.e., non-dependency, contracts. The project contracts are defined in the project_files dictionary. The boolean value in each entry determines if the contract is to be deployed in the current run or not.
            NOTE: The project contracts have a rigid dependency structure that requires these to be deployed in the following order:
                BallotStandard -> ElectionStandard -> VoteBoxStandard -> VoteBooth
            As such, in order to guarantee this, I cannot deploy them in a for loop or something of the sort and I need to force the deployment order from above.

            :param gas_results_file_path (pathlib.Path): A valid path to a file to where the gas calculations should be written into. If None is provided, the function skips the gas analysis.
            :param storage_results_file_path (pathlib.Path): A valid path to a file where the storage computations should be written into. If None is provided, the function skips the storage analysis.
        """
        # 1. Deploy the base contract BallotStandard
        contract_path = Path(self.config.get("project", "BallotStandard"))
        contract_source = open(contract_path)

        tx_response: entities.TransactionResultResponse = None
        tx_start: int = 0
        tx_end: int = 0

        log.info("1. Deploying the BallotStandard project contract...")
        try:
            if (storage_results_file_path):
                await self.script_runner.profile_all_accounts_csv(program_stage="BallotStandard - pre deploy", output_file_path=storage_results_file_path)
            tx_start = time.time_ns()
            tx_response = await self.run(contract_name="BallotStandard", contract_source=contract_source.read(), update=True)
            tx_end = time.time_ns()
            log.info("BallotStandard contract deployed successfully!")

            if (storage_results_file_path):
                await self.script_runner.profile_all_accounts_csv(program_stage="BallotStandard - post deploy", output_file_path=storage_results_file_path)
        except Exception as e:
            log.error("Unable to deploy the BallotStandard contract: ")
            log.error(e)
            exit(-1)

        tokens_withdrawn_events: list[dict] = await self.event_runner.getFungibleTokenWithdrawnEvents(tx_response=tx_response)
        fees_deducted_events: list[dict] = await self.event_runner.getFlowFeesFeesDeductedEvents(tx_response=tx_response)

        if (gas_results_file_path):
            utils.processTransactionData(fees_deducted_events=fees_deducted_events, tokens_withdrawn_events=tokens_withdrawn_events, elapsed_time=(tx_end - tx_start), tx_description="BallotStandard deployment", output_file_path=gas_results_file_path)

        # 2. Deploy the base contract ElectionStandard
        contract_path = Path(self.config.get("project", "ElectionStandard"))
        contract_source = open(contract_path)

        log.info("2. Deploying the ElectionStandard project contract...")
        try:
            if (storage_results_file_path):
                await self.script_runner.profile_all_accounts_csv(program_stage="ElectionStandard - pre deploy", output_file_path=storage_results_file_path)
            tx_start = time.time_ns()
            tx_response = await self.run(contract_name="ElectionStandard", contract_source=contract_source.read(), update=True)
            tx_end = time.time_ns()

            if (storage_results_file_path):
                await self.script_runner.profile_all_accounts_csv(program_stage="ElectionStandard - post deploy", output_file_path=storage_results_file_path)

            log.info("ElectionStandard contract deployed successfully!")
        except Exception as e:
            log.error("Unable to deploy the ElectionStandard contract: ")
            log.error(e)
            exit(-1)

        tokens_withdrawn_events: list[dict] = await self.event_runner.getFungibleTokenWithdrawnEvents(tx_response=tx_response)
        fees_deducted_events: list[dict] = await self.event_runner.getFlowFeesFeesDeductedEvents(tx_response=tx_response)

        if (gas_results_file_path):
            utils.processTransactionData(fees_deducted_events=fees_deducted_events, tokens_withdrawn_events=tokens_withdrawn_events, elapsed_time=(tx_end - tx_start), tx_description="ElectionStandard deployment", output_file_path=gas_results_file_path)

        # 3. Deploy the base contract VoteBoxStandard
        contract_path = Path(self.config.get("project", "VoteBoxStandard"))
        contract_source = open(contract_path)

        log.info("3. Deploying the VoteBoxStandard project contract...")
        try:
            if (storage_results_file_path):
                await self.script_runner.profile_all_accounts_csv(program_stage="VoteBoxStandard - pre deploy", output_file_path=storage_results_file_path)

            tx_start = time.time_ns()
            tx_response = await self.run(contract_name="VoteBoxStandard", contract_source=contract_source.read(), update=True)
            tx_end = time.time_ns()

            if (storage_results_file_path):
                await self.script_runner.profile_all_accounts_csv(program_stage="VoteBoxStandard - post deploy", output_file_path=storage_results_file_path)
            log.info("VoteBoxStandard contract deployed successfully!")
        except Exception as e:
            log.error("Unable to deploy the VoteBoxStandard contract: ")
            log.error(e)
            exit(-1)

        tokens_withdrawn_events: list[dict] = await self.event_runner.getFungibleTokenWithdrawnEvents(tx_response=tx_response)
        fees_deducted_events: list[dict] = await self.event_runner.getFlowFeesFeesDeductedEvents(tx_response=tx_response)

        if (gas_results_file_path):
            utils.processTransactionData(fees_deducted_events=fees_deducted_events, tokens_withdrawn_events=tokens_withdrawn_events, elapsed_time=(tx_end - tx_start), tx_description="VoteBoxStandard deployment", output_file_path=gas_results_file_path)

        # 4. Deploy the base contract VoteBooth. This one needs an Bool argument provided to it as well
        contract_path = Path(self.config.get("project", "VoteBooth"))
        contract_source = open(contract_path)

        log.info("4. Deploying the VoteBooth project contract...")
        try:
            if (storage_results_file_path):
                await self.script_runner.profile_all_accounts_csv(program_stage="VoteBooth - pre deploy", output_file_path=storage_results_file_path)

            tx_start = time.time_ns()
            tx_response: entities.TransactionResultResponse = await self.run(contract_name="VoteBooth", contract_source=contract_source.read(), update=True)
            tx_end = time.time_ns()

            if (storage_results_file_path):
                await self.script_runner.profile_all_accounts_csv(program_stage="VoteBooth - post deploy", output_file_path=storage_results_file_path)

            log.info("VoteBooth contract deployed successfully!")

            # After deploying the last contract of the project, I should run the EventRunner class constructor again to update the deployment addresses
            # that are needed to process the events properly. This needs to happen before running any of the event capturing routines or it will fail
            self.event_runner.configureDeployerAddress()

            election_index_created_events: list[dict] = await self.event_runner.getElectionIndexCreatedEvents(tx_response=tx_response)

            for election_index_created_event in election_index_created_events:
                log.info(f"ElectionIndex created for account {election_index_created_event["account_address"]}")

            votebooth_printer_admin_created_events: list[dict[str:str]] = await self.event_runner.getVoteBoothPrinterAdminCreatedEvents(tx_response=tx_response)
            
            for votebooth_printer_admin_created_event in votebooth_printer_admin_created_events:
                log.info(f"VoteBoothPrinterAdmin created for account {votebooth_printer_admin_created_event["account_address"]}")

            tokens_withdrawn_events: list[dict] = await self.event_runner.getFungibleTokenWithdrawnEvents(tx_response=tx_response)
            fees_deducted_events: list[dict] = await self.event_runner.getFlowFeesFeesDeductedEvents(tx_response=tx_response)

            if (gas_results_file_path):
                utils.processTransactionData(fees_deducted_events=fees_deducted_events, tokens_withdrawn_events=tokens_withdrawn_events, elapsed_time=(tx_end - tx_start), tx_description="VoteBooth deployment", output_file_path=gas_results_file_path)

        except Exception as e:
            log.error("Unable to deploy the VoteBooth contract: ")
            log.error(e)
            exit(-1)


    async def deployProject(self, gas_results_file_path: Path = None, storage_results_file_path: Path = None) -> dict[str: dict[str: dict]]:
        """
        This function aggregates the DeployContract and UpdateContract (which I already combined into one) but to deploy all dependencies and all project contracts respective the defined order to produce a network environment ready to be used.
        :param gas_results_file_path (pathlib.Path): A valid path to a file to where the gas calculations should be written into. If None is provided, the function skips the gas analysis.
        :param storage_results_file_path (pathlib.Path): A valid path to a file where the storage computations should be written into. If None is provided, the function skips the storage analysis.
        """
        log.info(f"Deploying all project contracts for network {self.ctx.access_node_host}:{self.ctx.access_node_port}...")
        await self.deployProjectContracts(gas_results_file_path=gas_results_file_path, storage_results_file_path=storage_results_file_path)
        log.info("All project contracts were deployed successfully!")
        

class DeleteContract():
    def __init__(self) -> None:
        super().__init__()
        
        self.ctx = AccountConfig()
        project_cwd: Path = Path(os.getcwd())
        config_path: Path = project_cwd.joinpath("common", "config.ini")
        self.config: configparser.ConfigParser = configparser.ConfigParser()
        self.config.read(config_path)

        self.event_runner: EventRunner = EventRunner()
        self.script_runner: ScriptRunner = ScriptRunner()

    # The contract removal function only needs the contract name
    async def run(self, contract_name: str) -> entities.TransactionResultResponse:
        async with flow_client(
            host=self.ctx.access_node_host, port=self.ctx.access_node_port
        ) as client:
            signer_address = self.ctx.service_account["address"]
            signer_key_id = self.ctx.service_account["key_id"]
            signer = self.ctx.service_account["signer"]

            latest_block = await client.get_latest_block()
            proposer = await client.get_account_at_latest_block(
                address=signer_address.bytes
            )

            contract_name = cadence.String(contract_name)

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
                    address=signer_address,
                    key_id=signer_key_id,
                    signer=signer,
                )
                .with_gas_limit(gas_limit=contract_gas_limit)
            )
            
            try:
                tx_response: entities.TransactionResultResponse = await client.execute_transaction(transaction)
                return tx_response
            except Exception as e:
                log.error(f"Unable to delete contract '{contract_name}' due to:")
                log.error(e)
                exit(-1)



    async def deleteProjectContracts(self, gas_results_file_path: Path = None, storage_results_file_path: Path = None) -> None:
        """
            Function to deploy all project contracts as defined in the project_files dictionary.
            :param gas_results_file_path (pathlib.Path): A valid path to a file to where the gas calculations should be written into. If None is provided, the function skips the gas analysis.
            :param storage_results_file_path (pathlib.Path): A valid path to a file where the storage computations should be written into. If None is provided, the function skips the storage analysis.
        """
        # Update the event_runner deployed addresses before attempting any event capture
        self.event_runner.configureDeployerAddress()
        tx_response: entities.TransactionResultResponse = None
        tx_start: int = 0
        tx_end: int = 0

        for project_contract in project_files:
            log.info(f"Deleting '{project_contract}' from network {self.ctx.access_node_host}:{self.ctx.access_node_port} for account {self.ctx.service_account["address"]}")
            
            if (storage_results_file_path):
                await self.script_runner.profile_all_accounts_csv(program_stage=f"{project_contract} - pre deletion", output_file_path=storage_results_file_path)
            
            tx_start = time.time_ns()
            tx_response = await self.run(contract_name=project_contract)
            tx_end = time.time_ns()

            if (storage_results_file_path):
                await self.script_runner.profile_all_accounts_csv(program_stage=f"{project_contract} - post deletion", output_file_path=storage_results_file_path)

            log.info(f"Contract '{project_contract}' deleted successfully!")


            tokens_withdrawn_events: list[dict] = await self.event_runner.getFungibleTokenWithdrawnEvents(tx_response=tx_response)
            fees_deducted_events: list[dict] = await self.event_runner.getFlowFeesFeesDeductedEvents(tx_response=tx_response)

            if (gas_results_file_path):
                utils.processTransactionData(fees_deducted_events=fees_deducted_events, tokens_withdrawn_events=tokens_withdrawn_events, elapsed_time=(tx_end - tx_start), tx_description=f"{project_contract} contract removal", output_file_path=gas_results_file_path)


    async def deleteProjectDependencies(self):
        """
        Function to deploy all project dependencies as defined in the project_dependencies dictionary
        """
        for project_dependency in project_dependencies:

            log.info(f"Deleting '{project_dependency}' from network {self.ctx.access_node_host}:{self.ctx.access_node_port} for account {self.ctx.service_account["address"]}")

            await self.run(contract_name=project_dependency)
            log.info(f"Dependency '{project_dependency}' deleted successfully!")


    async def resetNetwork(self, gas_results_file_path: Path = None, storage_results_file_path: Path = None) -> None:
        """
        This function aggregates the 'deleteProjectContracts' and 'deleteProjectDependencies' function to clear the configured network from all contracts and respective dependencies.
        :param gas_results_file_path (pathlib.Path): A valid path to a file to where the gas calculations should be written into. If None is provided, the function skips the gas analysis.
        :param storage_results_file_path (pathlib.Path): A valid path to a file where the storage computations should be written into. If None is provided, the function skips the storage analysis.
        """
        log.info(f"Deleting all project contracts from network {self.ctx.access_node_host}:{self.ctx.access_node_port}...")
        await self.deleteProjectContracts(gas_results_file_path=gas_results_file_path, storage_results_file_path=storage_results_file_path)
        log.info("All project contracts deleted successfully!")


        # print(f"Deleting all project dependencies from network {self.ctx.access_node_host}:{self.ctx.access_node_port}...")
        # await self.deleteProjectDependencies()
        # print("All project dependencies deleted successfully!")


async def main(op: str = "deploy", gas_results_file_path: Path = None, storage_results_file_path: Path = None) -> None:
    option = op
    if (len(sys.argv) > 1):
        try:
            # Grab argv 1 since 0 is the file's path
            option = sys.argv[1].lower().strip()
        except Exception:
            log.warning(f"No input arguments detected for this run. Defaulting to '{option}'")

    if (option == "deploy"):
        log.info(f"Setting up network...")
        contract_deployer: DeployContract = DeployContract()
        await contract_deployer.deployProject(gas_results_file_path=gas_results_file_path, storage_results_file_path=storage_results_file_path)
        log.info(f"Project successfully set up!")
    elif (option == "clear"):
        log.info("Clearing up the network...")
        contract_deleter: DeleteContract = DeleteContract()
        contract_deleter.event_runner.configureDeployerAddress()
        await contract_deleter.resetNetwork(gas_results_file_path=gas_results_file_path, storage_results_file_path=storage_results_file_path)
        log.info(f"Project network cleared successfully!")
    else:
        if (option == ""):
            log.warning(f"Missing option", end="")
        else:
            log.warning(f"Unknown option: {option}", end="")
        
        log.warning("\nUsage: \n$python 01_contract_management.py <deploy|clear>")


if __name__ == "__main__":
    asyncio.run(main())
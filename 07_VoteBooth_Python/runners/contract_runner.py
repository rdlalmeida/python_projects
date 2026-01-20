"""
Script to automate the deploy and removal of the contracts that compose this voting system backend.
"""
from flow_py_sdk import(
    entities,
    flow_client,
    cadence,
    Tx,
    TransactionTemplates,
    ProposalKey
)
import configparser
import asyncio
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from pathlib import Path
from python_scripts.cadence_scripts import ScriptRunner
from common.utils import Utils
from common.account_config import AccountConfig
from python_scripts.event_management import EventRunner
import time
import datetime

import logging
log = logging.getLogger(__name__)
Utils.configureLogging()

project_cwd = Path(os.getcwd())
config_path = project_cwd.joinpath("common", "config.ini")
config = configparser.ConfigParser()
config.read(config_path)

project_files = {
    "BallotStandard": True,
    "ElectionStandard": True,
    "VoteBoxStandard": True,
    "VoteBooth": True
}

contract_gas_limit: int = int(config.get(section="gas", option="limit"))
contract_encoding: str = config.get(section="encryption", option="encoding")

event_runner: EventRunner = EventRunner()
script_runner: ScriptRunner = ScriptRunner()

async def deploy_contract(contract_name: str, contract_source: str, update: bool, gas_results_file_path: Path = None, storage_results_file_path: Path = None) -> None:
    """
    Function to create (deploy) a new contract with the name and code provided as argument, to the network configured and into the address set as service account.
    
    :param contract_name (str): The name of the contract to create
    :param contract_source (str): The source code of the contract to deploy.
    :param update (bool): Set this flag to True to try and update the contract if the initial deploy fails. If set to False and the initial deploy fails, the function stops immediately.
    :param gas_results_file_path (Path): A valid path to a file to where the gas calculations should be written into. If None is provided, the function skips the gas analysis.
    :param storage_results_file_path (Path): A valid path to a file where the storage computations should be written into. If None is provided, the function skips the storage analysis.
    """
    # Validate the contract name at the top
    if (not project_files.__contains__(contract_name)):
        raise Exception(f"ERROR: Contract '{contract_name}' does not belong to the current project!")
    
    # Step 0: Get accounts
    ctx = AccountConfig()
    
    # Step 1: Create a client to connect to the Flow blockchain
    # flow_client function creates a client using the host and port configured in the AccountConfig object provided
    # Build the contract object as a dictionary entry
    contract = {
        "name": contract_name,
        "source": contract_source
    }
    tx_start: int = 0
    tx_end: int = 0

    # Setup the hexadecimal version of the contract as well
    contract_source_hex = bytes(contract["source"], contract_encoding).hex()

    async with flow_client(
        host=ctx.access_node_host, port=ctx.access_node_port
    ) as client:
        signer_address = ctx.service_account["address"]
        signer_key_id = ctx.service_account["key_id"]
        signer_object = ctx.service_account["signer"]

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
                signer=signer_object
            )
            .with_gas_limit(gas_limit=contract_gas_limit)
        )

        # Submit transaction
        try:
            if (storage_results_file_path):
                await script_runner.profile_all_accounts_csv(program_stage=f"{contract["name"]} - pre deploy", output_file_path=storage_results_file_path, account=signer_address.hex())

            tx_start = time.time_ns()
            tx_response: entities.TransactionResultResponse = await client.execute_transaction(transaction)
            tx_end = time.time_ns()

            if (storage_results_file_path):
                await script_runner.profile_all_accounts_csv(program_stage=f"{contract["name"]} - post deploy", output_file_path=storage_results_file_path, account=signer_address.hex())

            log.info(f"Contract {contract_name} successfully deployed to network at {ctx.access_node_host}:{ctx.access_node_port} for account {signer_address}")

            if (gas_results_file_path):
                # Grab the FeesDeducted and TokensWithdrawn events for further analysis
                tokens_withdrawn_events: list[dict] = await event_runner.getFungibleTokenWithdrawnEvents(tx_response=tx_response)
                fees_deducted_events: list[dict] = await event_runner.getFlowFeesFeesDeductedEvents(tx_response=tx_response)

                Utils.processTransactionData(fees_deducted_events=fees_deducted_events, tokens_withdrawn_events=tokens_withdrawn_events, elapsed_time=(tx_end - tx_start), tx_description=f"{contract["name"]} deployment", output_file_path=gas_results_file_path)

            return tx_response
        except Exception as deploy_ex:
            # Test if this Exception was due to an existing contract with the same name
            if (deploy_ex.args[0].__contains__("cannot overwrite existing contract")):
                log.warning(f"Contract {contract_name} already exists in {ctx.service_account["address"]} account.")
                # Check if the contract is set for update. Proceed if that is the case
                if (update):
                    # Close the old client because the update function creates a new one
                    client.channel.close()
                    await update_contract(contract_name=contract["name"], contract_source=contract["source"], gas_results_file_path=gas_results_file_path, storage_results_file_path=storage_results_file_path)
                else:
                    # The contract already exists in the network and it is not supposed to be updated
                    log.info("Nothing else to do.")
            else:
                # The Exception was raised because of something else
                log.error(f"Unable to deploy contract '{contract_name}' due to:")
                log.error(deploy_ex)
                exit(-1)


async def update_contract(contract_name: str, contract_source: str, gas_results_file_path: Path, storage_results_file_path: Path) -> None:
    """
    Function to update (re-deploy) a contract with the name and code provided as argument, to the network configured and into the address set as service account.
    
    :param contract_name (str): The name of the contract to update in the network.
    :param contract_source (str): The source code of the contract to update.
    :param gas_results_file_path (Path): A valid path to a file to where the gas calculations should be written into. If None is provided, the function skips the gas analysis.
    :param storage_results_file_path (Path): A valid path to a file where the storage computations should be written into. If None is provided, the function skips the storage analysis.
    """
    # Validate inputs
    if (not project_files.__contains__(contract_name)):
        raise Exception(f"ERROR: Contract '{contract_name}' does not belong to the current project!")
    
    # Get the context object
    ctx = AccountConfig()
    
    # Build the initial structures to submit a contract update
    contract = {
        "name": contract_name,
        "source": contract_source
    }

    contract_source_hex = bytes(contract["source"], contract_encoding).hex()
    tx_start: int = 0
    tx_end: int = 0

    async with flow_client(
        host=ctx.access_node_host, port=ctx.access_node_port
    ) as client:
        signer_address = ctx.service_account["address"]
        signer_key_id = ctx.service_account["key_id"]
        signer_object = ctx.service_account["signer"]

        latest_block = await client.get_latest_block()
        proposer = await client.get_account_at_latest_block(
            address=signer_address.bytes
        )

        contract_name = cadence.String(contract_name)
        contract_code = cadence.String(contract_source_hex)

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
                signer=signer_object
            )
            .with_gas_limit(gas_limit=contract_gas_limit)
        )
        log.info(f"Updating {contract["name"]} contract...")
        try:
            if (storage_results_file_path):
                await script_runner.profile_all_accounts_csv(program_stage=f"{contract["name"]} - pre update", output_file_path=storage_results_file_path, account=signer_address.hex())

            tx_start = time.time_ns()
            tx_response: entities.TransactionResultResponse = await client.execute_transaction(transaction)
            tx_end = time.time_ns()

            if (storage_results_file_path):
                await script_runner.profile_all_accounts_csv(program_stage=f"{contract["name"]} - post update", output_file_path=storage_results_file_path, account=signer_address.hex())

            if (gas_results_file_path):
                tokens_withdrawn_events: list[dict] = await event_runner.getFungibleTokenWithdrawnEvents(tx_response=tx_response)
                fees_deducted_events: list[dict] = await event_runner.getFlowFeesFeesDeductedEvents(tx_response=tx_response)

                Utils.processTransactionData(fees_deducted_events=fees_deducted_events, tokens_withdrawn_events=tokens_withdrawn_events, elapsed_time=(tx_end - tx_start), tx_description=f"{contract["name"]} Update", output_file_path=gas_results_file_path)

            log.info(f"Contract {contract["name"]} updated successfully to network at {ctx.access_node_host}:{ctx.access_node_port} for account {ctx.service_account["address"]}")
            return tx_response
        
        except Exception as update_ex:
            log.error(f"Unable to update contract '{contract["name"]}' due to: ")
            log.error(update_ex)
            exit(-1 )


async def delete_contract(contract_name: str, gas_results_file_path: Path = None, storage_results_file_path: Path = None) -> None:
    """
    Function to delete a contract with the name provided as argument, from the network configured and from the address set as service account.
    
    :param contract_name (str): The name of the contract to delete from the network.
    :param gas_results_file_path (Path): A valid path to a file to where the gas calculations should be written into. If None is provided, the function skips the gas analysis.
    :param storage_results_file_path (Path): A valid path to a file where the storage computations should be written into. If None is provided, the function skips the storage analysis.
    """
    if (not project_files.__contains__(contract_name)):
        raise Exception(f"ERROR: Contract '{contract_name}' does not belong to the current project!")
    
    # Get the current context
    ctx = AccountConfig()

    tx_start: int = 0
    tx_end: int = 0

    async with flow_client(
        host=ctx.access_node_host, port=ctx.access_node_port
    ) as client:
        signer_address = ctx.service_account["address"]
        signer_key_id = ctx.service_account["key_id"]
        signer_object = ctx.service_account["signer"]

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
                signer=signer_object,
            )
            .with_gas_limit(gas_limit=contract_gas_limit)
        )
        
        try:
            if (storage_results_file_path):
                await script_runner.profile_all_accounts_csv(program_stage=f"{contract_name} - pre deletion", output_file_path=storage_results_file_path, account=signer_address.hex())

            tx_start = time.time_ns()
            tx_response: entities.TransactionResultResponse = await client.execute_transaction(transaction)
            tx_end = time.time_ns()

            if (storage_results_file_path):
                await script_runner.profile_all_accounts_csv(program_stage=f"{contract_name} - post deletion", output_file_path=storage_results_file_path, account=signer_address.hex())

            if (gas_results_file_path):
                tokens_withdrawn_events: list[dict] = await event_runner.getFungibleTokenWithdrawnEvents(tx_response=tx_response)
                fees_deducted_events: list[dict] = await event_runner.getFlowFeesFeesDeductedEvents(tx_response=tx_response)

                Utils.processTransactionData(fees_deducted_events=fees_deducted_events, tokens_withdrawn_events=tokens_withdrawn_events, elapsed_time=(tx_end - tx_start), tx_description=f"{contract_name} Deletion", output_file_path=gas_results_file_path)
        except Exception as e:
            log.error(f"Unable to delete contract '{contract_name}' due to:")
            log.error(e)
            exit(-1)


if __name__ == "__main__":
    """
    Usage: python contract_runner <operation>
    :param operation (str): The operation to execute, namely, "deploy", "update", or "clear"
    """
    # Extract and validate the arguments from the command line
    if (len(sys.argv) < 2):
        raise Exception("ERROR: Please provide 'deploy', 'update', or 'clear' to continue")
    
    operation: str = sys.argv[1].lower().strip()

    if (operation != "deploy" and operation != "clear" and operation != "update"):
        raise Exception(f"ERROR: Invalid operation provided '{operation}'. Please provide 'deploy', 'update', or 'clear' to continue")
    
    ctx = AccountConfig()

    gas_results_file_name: str = f"{datetime.datetime.now().strftime("%d-%m-%yT%H:%M:%S")}_{ctx.service_account["address"].hex()}_{config.get(section="network", option="current")}_contract_{operation}_gas_results.csv"
    gas_results_file_path: Path = Path(os.getcwd()).joinpath("results", gas_results_file_name)

    storage_results_file_name: str = f"{datetime.datetime.now().strftime("%d-%m-%yT%H:%M:%S")}_{ctx.service_account["address"].hex()}_{config.get(section="network", option="current")}_contract_{operation}_storage_results.csv"
    storage_results_file_path: Path = Path(os.getcwd()).joinpath("results", storage_results_file_name)

    new_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(new_loop)

    if (operation == "deploy"):
        for contract_name in project_files:
            contract_path: Path = Path(config.get(section="project", option=contract_name))
            contract_source = open(contract_path)

            log.info(f"Deploying {contract_name}...")
            new_loop.run_until_complete(deploy_contract(contract_name=contract_name, contract_source=contract_source.read(), update=True, gas_results_file_path=gas_results_file_path, storage_results_file_path=storage_results_file_path))
    elif (operation == "update"):
        for contract_name in project_files:
            contract_path: Path = Path(config.get(section="project", option=contract_name))
            contract_source = open(contract_path)

            log.info(f"Updating {contract_name}...")
            new_loop.run_until_complete(update_contract(contract_name=contract_name, contract_source=contract_source.read(), gas_results_file_path=gas_results_file_path, storage_results_file_path=storage_results_file_path))
    else:
        # Operation = "clear"
        for contract_name in project_files:
            log.info(f"Deleting {contract_name}...")
            new_loop.run_until_complete(delete_contract(contract_name=contract_name, gas_results_file_path=gas_results_file_path, storage_results_file_path=storage_results_file_path))
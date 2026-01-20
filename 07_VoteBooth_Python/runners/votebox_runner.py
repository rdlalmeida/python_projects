"""
Script to create a new VoteBox resource, in an automated fashion.

"""
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from common.utils import Utils
from common.account_config import AccountConfig
import datetime
from pathlib import Path
import configparser
import logging
import asyncio
from python_scripts.cadence_transactions import TransactionRunner

log = logging.getLogger(__name__)
Utils.configureLogging()

project_cwd = Path(os.getcwd())
config_path = project_cwd.joinpath("common", "config.ini")
config = configparser.ConfigParser()
config.read(config_path)

tx_runner: TransactionRunner = TransactionRunner()

async def create_votebox(tx_signer_address: str = None, tx_proposer_address: str = None, tx_payer_address: str = None, tx_authorizer_address: list[str] = [], gas_results_file_path: Path = None, storage_results_file_path: Path = None) -> None:
    await tx_runner.createVoteBox(tx_signer_address=tx_signer_address, tx_proposer_address=tx_proposer_address, tx_payer_address=tx_payer_address, tx_authorizer_address=tx_authorizer_address, gas_results_file_path=gas_results_file_path, storage_results_file_path=storage_results_file_path)


async def delete_votebox(tx_signer_address: str = None, tx_proposer_address: str = None, tx_payer_address: str = None, tx_authorizer_address: list[str] = [], gas_results_file_path: Path = None, storage_results_file_path: Path = None) -> None:
    await tx_runner.deleteVoteBox(tx_signer_address=tx_signer_address, tx_proposer_address=tx_proposer_address, tx_payer_address=tx_payer_address, tx_authorizer_address=tx_authorizer_address, gas_results_file_path=gas_results_file_path, storage_results_file_path=storage_results_file_path)

if __name__ == "__main__":
    """
    Usage: python votebox_runner <operation> <address>
    :param operation (str): The operation to execute, namely, "create", or "destroy"
    :param address (str): If provided, this script creates a single VoteBox to the account address provided. If not, or if the address provided does not exists in the network, the script defaults to create a VoteBox to all accounts configured in flow.json, for the network active. The same logic applies to the 'destroy' operation.
    """
    # Validate that a proper operation was selected
    if (len(sys.argv) < 2):
        raise Exception("ERROR: Please provide 'create' or 'destroy' to continue")
    
    operation: str = sys.argv[1].lower().strip()

    if (operation != "create" and operation != "destroy"):
        raise Exception(f"ERROR: Invalid operation provided '{operation}'. Please provide 'create' or 'destroy' to continue")
    
    # Check if additional arguments were given
    input_addresses: list[str] = []

    for i in range(2, len(sys.argv)):
        # Remove the '0x' prefix, is one exists
        input_address: str = sys.argv[i].strip()

        if (input_address[0:2] == "0x"):
            input_address = input_address[2:]

        input_addresses.append(input_address)

    ctx = AccountConfig()

    gas_results_file_name: str = f"{datetime.datetime.now().strftime("%d-%m-%yT%H:%M:%S")}_{config.get(section="network", option="current")}_votebox_{operation}_gas_results.csv"
    gas_results_file_path: Path = Path(os.getcwd()).joinpath("results", gas_results_file_name)

    storage_results_file_name: str = f"{datetime.datetime.now().strftime("%d-%m-%yT%H:%M:%S")}_{config.get(section="network", option="current")}_votebox_{operation}_storage_results.csv"
    storage_results_file_path: Path = Path(os.getcwd()).joinpath("results", storage_results_file_name)

    new_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(new_loop)

    if (operation == "create"):
        if (len(input_addresses) > 0):
            for input_address in input_addresses:
                new_loop.run_until_complete(create_votebox(tx_signer_address=None, tx_proposer_address=input_address, tx_payer_address=ctx.service_account["address"].hex(), tx_authorizer_address=[input_address], gas_results_file_path=gas_results_file_path, storage_results_file_path=storage_results_file_path))
        else:
            active_addresses: list[str] = ctx.getAddresses()
            # Remove the service account from the set
            active_addresses.remove(ctx.service_account["address"].hex())
            for active_address in active_addresses:
                new_loop.run_until_complete(create_votebox(tx_signer_address=None, tx_proposer_address=active_address, tx_payer_address=ctx.service_account["address"].hex(), tx_authorizer_address=[active_address], gas_results_file_path=gas_results_file_path, storage_results_file_path=storage_results_file_path))
    else:
        # Operation = "destroy"
        if (len(input_addresses) > 0):
            for input_address in input_addresses:
                new_loop.run_until_complete(delete_votebox(tx_signer_address=None, tx_proposer_address=input_address, tx_payer_address=ctx.service_account["address"].hex(), tx_authorizer_address=[input_address], gas_results_file_path=gas_results_file_path, storage_results_file_path=storage_results_file_path))
        else:
            active_addresses: list[str] = ctx.getAddresses()
            # Remove the service account from the set
            active_addresses.remove(ctx.service_account["address"].hex())
            for active_address in active_addresses:
                new_loop.run_until_complete(delete_votebox(tx_signer_address=None, tx_proposer_address=active_address, tx_payer_address=ctx.service_account["address"].hex(), tx_authorizer_address=[active_address], gas_results_file_path=gas_results_file_path, storage_results_file_path=storage_results_file_path))
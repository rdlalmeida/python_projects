"""
Script to create a new Election resource, using one of the pre-defined election sets
"""
import asyncio
import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pathlib
from common.utils import Utils
from common.account_config import AccountConfig
import configparser
import datetime

import logging
log = logging.getLogger(__name__)
Utils.configureLogging()

from python_scripts.cadence_scripts import ScriptRunner
from python_scripts.cadence_transactions import TransactionRunner

script_runner: ScriptRunner = ScriptRunner()
tx_runner: TransactionRunner = TransactionRunner()


project_cwd = pathlib.Path(os.getcwd())
config_path = project_cwd.joinpath("common", "config.ini")
config = configparser.ConfigParser()
config.read(config_path)

election_names: list[str] = [
    "A. Bullfights",
    "B. Coconut Cake",
    "C. Basketball"
]

election_ballots: list[str] = [
    "A. How should Portugal deal with its bullfighting arenas?",
    "B. What is the best frosting for coconut cake?",
    "C. Which NBA team is going to win the 2025-25 championship?"
]

election_options: list[dict[int: str]] = [
    {
        1: "Burn them to the ground",
        2: "Bomb them from afar using military artillery",
        3: "Refit them into urban landfills",
        4: "Rebuild them as public spaces, as malls, gyms, theatres, etc.",
        5: "Rebuild them as free public veterinarian clinics and force bullfights to maintain them for free."
    },
    {
        1: "Powdered sugar",
        2: "Shredded coconut",
        3: "Tempered dark chocolate",
        4: "Butter-based frosting",
        5: "Nothing. Leave it as is"
    },
    {
        1: "Minnesota Timber Wolves",
        2: "Oklahoma City Thunder",
        3: "New York Knicks",
        4: "Cleveland Cavaliers",
        5: "None of the above"
    }
]

keys_dir: pathlib.Path = pathlib.Path(os.getcwd()).joinpath("keys")
election_public_encryption_keys: list[pathlib.Path] = [
    keys_dir.joinpath("rsa_public_1.key"),
    keys_dir.joinpath("rsa_public_2.key"),
    keys_dir.joinpath("rsa_public_3.key")
]

election_private_encryption_keys_filenames: list[str] = [
    "rsa_private_1.key",
    "rsa_private_2.key",
    "rsa_private_3.key"
]

election_storage_paths: list[str] = [
    "Election01",
    "Election02",
    "Election03"
]

election_public_paths: list[str] = [
    "PublicElection01",
    "PublicElection02",
    "PublicElection03"
]

async def create_election(election_index: int, free_election:bool, tx_signer_address: str, gas_results_file_path: pathlib.Path = None, storage_results_file_path: pathlib.Path = None) -> None:
    """
    Function to create a new Election into the main project. The new Election is available by retrieving its election_id from a "getActiveElections" script or something of the sort.

    :param election_name (str) The name of the election
    :param election_ballot (str) The ballot for the election
    :param election_options (dict)nt:str] - The set of valid options to set in the election.
    :param election_public_key (str) The public encryption key to be associated with the election
    :param election_storage_path (str) A UNIX-type path to indicate the storage path where the election resource is to be stored.
    :param election_public_path (str) A UNIX-type path to indicate the public path where the public capability for this election is to be stored to.
    :param free_election (bool): If True, this election is free, i.e., the service account pays for the transaction fees. If false, voters pay for transaction gas fees.
    :param tx_signer_address (str) The address for the account that can sign the transaction to create this election.
    :param gas_results_file_path (pathlib.Path): A valid path to a file to where the gas calculations should be written into. If None is provided, the function skips the gas analysis.
    :param storage_results_file_path (pathlib.Path): A valid path to a file where the storage computations should be written into. If None is provided, the function skips the storage analysis.
    """

    election_id: int = await tx_runner.createElection(
        election_name=election_names[election_index],
        election_ballot=election_ballots[election_index],
        election_options=election_options[election_index],
        election_public_key=open(election_public_encryption_keys[election_index]).read(),
        election_storage_path=election_storage_paths[election_index],
        election_public_path=election_public_paths[election_index],
        free_election=free_election,
        tx_signer_address=tx_signer_address,
        gas_results_file_path=gas_results_file_path,
        storage_results_file_path=storage_results_file_path
    )

    log.info(f"Successfully created Election with id {election_id} and name '{election_names[election_index]}'")


async def destroy_election(election_id: int, tx_signer_address: str, gas_results_file_path: pathlib.Path = None, storage_results_file_path: pathlib.Path = None):
    """
    Function to destroy the election currently associated to this class. This function fails if the self.election_id parameter for this class is still None.
    :param election_id (int): The election identifier for the Election resource to be destroyed.
    :param tx_signer_address (str) The address for the account that can sign the transaction to create this election.
    :param gas_results_file_path (pathlib.Path): A valid path to a file to where the gas calculations should be written into. If None is provided, the function skips the gas analysis.
    :param storage_results_file_path (pathlib.Path): A valid path to a file where the storage computations should be written into. If None is provided, the function skips the storage analysis.
    """
    # Grab the array with all the active Elections election_ids
    active_election_ids: list[int] = await script_runner.getActiveElections()

    if (election_id not in active_election_ids):
        raise Exception(f"ERROR: Election {election_id} is not among the active ones. Cannot continue!")

    await tx_runner.deleteElection(election_id=election_id, tx_signer_address=tx_signer_address, gas_results_file_path=gas_results_file_path, storage_results_file_path=storage_results_file_path)

async def list_active_elections() -> None:
    """
    Simple async function to print a list of all active elections in the network configured.
    """
    active_elections: dict[int:str] = await script_runner.getElectionsList()

    log.info(f"Currently active elections in {config.get(section="network", option="current")} network")

    for active_election in active_elections:
        log.info(f"Election {active_election}: {active_elections[active_election]}")

if __name__ == "__main__":
    """
    Usage: python election_runner <operation> <election_index | election_id> <free_election>
    :param operation (str): The operation to run, namely, "create", list, or destroy"
    :param election_index | election_id (int): If the operation is a 'create' one, this argument expects a election_index value to select which of the test sets is to be used to create the new Election. 
    'list' operation lists all active Elections in the active network.
    If the operation is 'destroy' instead, then this argument expects the election_id of the Election to destroy. I'm able to employ this argument duality due only to the fact that argv[2] needs to be an int in both operations considered.
    :param free_election (bool): Set this to True to have the service account to pay for all transaction fees, False set the voter to pay those instead.
    """
    # Extract and validate the arguments from the command line
    if (len(sys.argv) < 2):
        raise Exception("ERROR: Please provide 'deploy' or 'clear' to continue")
    
    operation: str = sys.argv[1].lower().strip()

    if (operation != "create" and operation != "destroy" and operation != "list"):
        raise Exception(f"ERROR Invalid operation provided: {operation}. Please provide 'create', list, or 'destroy' to continue")
    
    if (operation == "create"):
        # Validate the crate exclusive arguments, namely, the election_index and free_election
        if (len(sys.argv) < 3):
            raise Exception("ERROR: Please provide a valid election index to continue.")

        election_index: int = int(sys.argv[2].lower().strip())

        if (election_index < 0):
            raise Exception(f"Election create ERROR: Invalid election_index provided: {election_index}. Please provide a positive value to continue!")
        elif(election_index > len(election_names)):
            raise Exception(f"Election create ERROR: Invalid election_index provided: {election_index}. Please provide an index lower than {len(election_names)} to continue!")
        
        if (len(sys.argv) < 4):
            raise Exception("ERROR: Please provide a valid free election flag to continue.")
        
        free_election: bool = bool(sys.argv[3].lower().strip())
    elif (operation == "destroy"):
        if (len(sys.argv) < 3):
            raise Exception("ERROR: Please provide a valid election_id to continue.")
        # In this case, I expect the election_id is the sys.argv[2] positional argument as well
        election_id: int = int(sys.argv[2].lower().strip())

        if (election_id < 0):
            raise Exception(f"Election destroy ERROR: Invalid election_id provided: {election_id}. Please provide a positive value to continue!")
    
    # Grab a context object
    ctx = AccountConfig()
    
    # Create the output files. Note that both functions in this module need the service account signature to run
    gas_results_file_name: str = f"{datetime.datetime.now().strftime("%d-%m-%yT%H:%M:%S")}_{ctx.service_account["address"].hex()}_{config.get(section="network", option="current")}_election_gas_results.csv"
    gas_results_file_path: pathlib.Path = pathlib.Path(os.getcwd()).joinpath("results", gas_results_file_name)

    storage_results_file_name: str = f"{datetime.datetime.now().strftime("%d-%m-%yT%H:%M:%S")}_{ctx.service_account["address"].hex()}_{config.get(section="network", option="current")}_election_storage_results.csv"
    storage_results_file_path: pathlib.Path = pathlib.Path(os.getcwd()).joinpath("results", storage_results_file_name)

    # Launch the selected operation
    new_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(new_loop)

    if (operation == "create"):
        new_loop.run_until_complete(create_election(election_index=election_index, free_election=free_election, tx_signer_address=ctx.service_account["address"].hex(),gas_results_file_path=gas_results_file_path, storage_results_file_path=storage_results_file_path))
    elif(operation == "list"):
        new_loop.run_until_complete(list_active_elections())
    else:
        new_loop.run_until_complete(destroy_election(election_id=election_id, tx_signer_address=ctx.service_account["address"].hex(), gas_results_file_path=gas_results_file_path, storage_results_file_path=storage_results_file_path))

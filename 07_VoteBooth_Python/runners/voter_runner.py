"""
Script to automate the minting, cast, and submit Ballots from a single test accounts' VoteBox.
"""
import asyncio
import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pathlib
from common.utils import Utils
from common.account_config import AccountConfig
import configparser
import datetime
import time
import random
import base64

import logging
log = logging.getLogger(__name__)
Utils.configureLogging()

from python_scripts.cadence_scripts import ScriptRunner
script_runner: ScriptRunner = ScriptRunner()

from python_scripts.cadence_transactions import TransactionRunner
tx_runner: TransactionRunner = TransactionRunner()

from python_scripts.crypto_management import CryptoUtils

project_cwd = pathlib.Path(os.getcwd())
config_path = project_cwd.joinpath("common", "config.ini")
config = configparser.ConfigParser()
config.read(config_path)


async def process_ballot_account(voter_address: str, election_id: int = None, rounds: int = 10, max_delay: int = 10, gas_results_file_path: pathlib.Path = None, storage_results_file_path: pathlib.Path = None) -> None:
    """
    Simple function to abstract the minting, casting, and submission of ballots. The idea is to have this function running on a separate thread, casting ballots continuously from one account. 
    :param voter_address (str): The account address to use for this purpose.
    :param election_id (int): The Election identifier to the resource to use to mint and submit the Ballots in this process.
    :param rounds (int): The number of process cycles (votes) to execute with the account address provided.
    :param max_delay (int): The maximum number of seconds that each cycle must wait (to avoid concurrent and racing conditions) at the beginning of each cycle.
    :param gas_results_file_path (pathlib.Path): A valid path to a file to where the gas calculations should be written into. If None is provided, the function skips the gas analysis.
    :param storage_results_file_path (pathlib.Path): A valid path to a file where the storage computations should be written into. If None is provided, the function skips the storage analysis.
    """
    # Get the current account configuration
    ctx = AccountConfig()
    
    if (voter_address == ctx.service_account["address"].hex()):
        raise Exception(f"ERROR: Service account {ctx.service_account["address"].hex()} is not able to vote")
    
    if (rounds < 0):
        raise Exception(f"ERROR: Invalid number of rounds provided: {rounds}. Please provide a positive number to continue!")
    
    if (max_delay < 0):
        raise Exception(f"ERROR: Invalid maximum delay provided: {max_delay}. Please provide a positive number to continue!")
    
    # Test that at least one Election is active
    active_election_ids: list[int] = await script_runner.getActiveElections()

    if (len(active_election_ids) == 0):
        raise Exception("ERROR: No active Elections detected! Cannot continue.")
    
    default_election_id: int = active_election_ids[0]

    # Test if an election_id was provided.
    if (election_id != None):
        if (election_id not in active_election_ids):
            log.warning(f"WARNING: Election id provided '{election_id}' is not among the active election ids. Defaulting to '{default_election_id}'")
            election_id = default_election_id
    else:
        log.info(f"No election_id provided as argument. Defaulting to Election {default_election_id}...")
        election_id = default_election_id

    # Test that a proper election_id was set at this point
    if (election_id == None):
        raise Exception(f"ERROR: Unable to set a proper election_id...")
    
    # Set the thread to sleep for a random value between 0 and the max value provided
    # time.sleep(random.randint(a=0, b=max_delay))

    # Use the election_id provided to get a lot of useful parameters from the election in question
    free_election: bool = await script_runner.isElectionFree(election_id=election_id)
    election_options: list[dict] = await script_runner.getElectionOptions(election_id=election_id)
    election_public_encryption_key: str = await script_runner.getPublicEncryptionKey(election_id=election_id)

    # Get the option separator and encoding to use with the encrypted data
    option_separator: str = config.get(section="encryption", option="separator")
    option_encoding: str = config.get(section="encryption", option="encoding")

    # Setup the transaction signing parameters based on the election being free or not
    tx_signer_address: str = None
    tx_proposer_address: str = None
    tx_payer_address: str = None
    tx_authorizer_address: list[str] = []

    if (free_election):
        # In free elections, the service account pays for the transaction fees
        tx_proposer_address = voter_address
        tx_payer_address = ctx.service_account["address"].hex()
        tx_authorizer_address.append(voter_address)
    else:
        # If the election is not free, the voter pays for everything
        tx_signer_address = voter_address

    # Run this in a while loop
    while(rounds > 0):
#         time.sleep(random.randint(a=0, b=max_delay))
        
        # Mint a new ballot to the account. This transaction is solely from the service_account's responsibility, therefore this accounts pays for everything.
        await tx_runner.createBallot(election_id=election_id, recipient_address=voter_address, tx_signer_address=ctx.service_account["address"].hex(), gas_results_file_path=gas_results_file_path, storage_results_file_path=storage_results_file_path)

        # Cast the Ballot
        random_index: int = random.randint(a=1, b=len(election_options))
        random_option: dict[int:str] = election_options[random_index]

        # But the cast Ballot transaction gas expenses payment depend of the free state of the election. In this case, use the parameters set above
        option_salt: int = CryptoUtils.generate_random_salt()
        salted_option: str = random_option + option_separator + str(option_salt)
        encryption_key = CryptoUtils.load_public_key_from_string(key_string=election_public_encryption_key)

        # Encrypt the option
        encrypted_salted_option: str = CryptoUtils.encrypt_message(
            plaintext_message=salted_option,
            public_key=encryption_key
        )

        # Encode the result into a more data economical base64 encoding
        base64_option: str = base64.b64encode(encrypted_salted_option)

        # Cast the new option to the Ballot
        await tx_runner.castBallot(election_id=election_id, new_option=str(base64_option, encoding=option_encoding), tx_signer_address=tx_signer_address, tx_proposer_address=tx_proposer_address, tx_payer_address=tx_payer_address, tx_authorizer_address=tx_authorizer_address, gas_results_file_path=gas_results_file_path, storage_results_file_path=storage_results_file_path)
        

        # Submit the Ballot
        await tx_runner.submitBallot(election_id=election_id, tx_signer_address=tx_signer_address, tx_proposer_address=tx_proposer_address, tx_payer_address=tx_payer_address, tx_authorizer_address=tx_authorizer_address, gas_results_file_path=gas_results_file_path, storage_results_file_path=storage_results_file_path)

        # Set the ballot receipt to the voter account
        ctx.addReceipt(voter_address=voter_address, election_id=election_id, ballot_receipt=option_salt)
        # And add the receipt to the VoteBox also
        await tx_runner.addBallotReceipt(election_id=election_id, ballot_receipt=option_salt, tx_signer_address=None, tx_proposer_address=tx_proposer_address, tx_payer_address=tx_payer_address, tx_authorizer_address=tx_authorizer_address, gas_results_file_path=gas_results_file_path, storage_results_file_path=storage_results_file_path)

        # Inform the voter.
        log.info(f"Round {rounds}: Account {voter_address} successfully cast a Ballot to Election {election_id}")

        # Decrease the round number and go for another one, if needed.
        rounds -= 1
    
    # Voting done for this voter!
    log.info(f"Voter {voter_address} is finished for Election {election_id}")


async def main():
    """
    This is a simplified version of the "other" main function that simply runs the voting process, sequentially, for each of the test accounts configured in the active network.
    """
    ctx = AccountConfig()

    # Number of rounds to run this process with. This is the number of Ballots submitted by the account provided
    rounds: int = 25

    # Maximum number of seconds that this process can wait between rounds. The actual sleep value is a random one between 0 and the value set in the parameter
    max_delay: int = 10
    voter_addresses: list[str] = ctx.getAddresses()
    voter_addresses.remove(ctx.service_account["address"].hex())

    election_id: int = None

    # Launch the function
    for voter_address in voter_addresses:
        gas_results_file_name: str = f"{datetime.datetime.now().strftime("%d-%m-%yT%H:%M:%S")}_{voter_address}_{config.get(section="network", option="current")}_votebox_gas_results.csv"
        gas_results_file_path: pathlib.Path = pathlib.Path(os.getcwd()).joinpath("results", gas_results_file_name)

        storage_results_file_name: str = f"{datetime.datetime.now().strftime("%d-%m-%yT%H:%M:%S")}_{voter_address}_{config.get(section="network", option="current")}_votebox_storage_results.csv"
        storage_results_file_path: pathlib.Path = pathlib.Path(os.getcwd()).joinpath("results", storage_results_file_name)

        await process_ballot_account(voter_address=voter_address, election_id=election_id, rounds=rounds, max_delay=max_delay, gas_results_file_path=gas_results_file_path, storage_results_file_path=storage_results_file_path)


if __name__ == "__main__":
    """
    Usage: python voter_runner <address> <election_id>
    :param address (str): The voter account address to proceed with this process. The account must exist is the configured network, otherwise an Exception is raised instead.
    :param election_id (int): If provided, the process retrieves the Election reference to the Election in question, if it exits. If no election_id is provided, or the one provided does not exists, the process lists all current active Elections and selects the first one (index = 0) of the set returned. If not active Election are found, the process raises a proper Exception. 
    """

    asyncio.run(main())
    exit(0)

    ctx = AccountConfig()
    # Validate that a proper address was provided
    if (len(sys.argv) > 3):
        raise Exception("ERROR: Please provide a valid voter address to continue")
    
    voter_address: str = sys.argv[1].lower().strip()

    # Remove a "0x" prefix from the address string, if it was provided with it
    if (voter_address[0:2] == "0x"):
        voter_address = voter_address[2:]

    # Validate that the address points to a valid account and it is not the service account
    if (voter_address == ctx.service_account["address"].hex()):
        raise Exception(f"ERROR: Unable to run this process to the service account {voter_address}. Please select a new one!")

    account_addresses: list[str] = ctx.getAddresses()
    if (voter_address not in account_addresses):
        raise Exception(f"ERROR: Voter address provided '{voter_address}' is not among the active in '{config.get(section="network", option="current")}' network.")
    
    election_id: int = None
    # Validate if an election_id was provided. Replace the current id if so
    if (len(sys.argv) > 4):
        election_id = int(sys.argv[2].lower().strip())

    gas_results_file_name: str = f"{datetime.datetime.now().strftime("%d-%m-%yT%H:%M:%S")}_{voter_address}_{config.get(section="network", option="current")}_votebox_gas_results.csv"
    gas_results_file_path: pathlib.Path = pathlib.Path(os.getcwd()).joinpath("results", gas_results_file_name)

    storage_results_file_name: str = f"{datetime.datetime.now().strftime("%d-%m-%yT%H:%M:%S")}_{voter_address}_{config.get(section="network", option="current")}_votebox_storage_results.csv"
    storage_results_file_path: pathlib.Path = pathlib.Path(os.getcwd()).joinpath("results", storage_results_file_name)

    # Number of rounds to run this process with. This is the number of Ballots submitted by the account provided
    rounds: int = 10

    # Maximum number of seconds that this process can wait between rounds. The actual sleep value is a random one between 0 and the value set in the parameter
    max_delay: int = 10

    # Launch the function
    new_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(new_loop)

    new_loop.run_until_complete(process_ballot_account(voter_address=voter_address, election_id=election_id, rounds=rounds, max_delay=max_delay, gas_results_file_path=gas_results_file_path, storage_results_file_path=storage_results_file_path))
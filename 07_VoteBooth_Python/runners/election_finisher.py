"""
Script to finish an Election with the id provided as argument
"""
import asyncio
import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pathlib
from common.utils import Utils
from common.account_config import AccountConfig
import configparser
import base64
import datetime

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

option_separator: str = config.get(section="encryption", option="separator")
option_encoding: str = config.get(section="encryption", option="encoding")

async def tally_election(election_id: int, private_encryption_key_name: str, tx_signer_address: str, gas_results_file_path: pathlib.Path = None, storage_results_file_path: pathlib.Path = None) -> dict[str: int]:
        """
        Function to trigger the end of the election by processing their ballots, retrieving the ballot.options, decrypting and processing them, tallying the results and producing the winning option. This function also sets the function as finished.

        :param election_id (int): The election identifier for the Election instance to tally.
        :param private_encryption_key_path (str): The name of the file containing the private encryption key that can decrypt the ballot options. This filename should point to a file inside the '/keys' subfolder from this project directory. The key loading routine has this folder pre-configured. IMPORTANT: The correspondence between private and public keys used in this process is solely of the responsibility of the user. This process does not validates any keys at any point.
        :param tx_signer_address (str): The account address to use to digitally sign the transaction.
        :param gas_results_file_path (pathlib.Path): A valid path to a file to where the gas calculations should be written into. If None is provided, the function skips the gas analysis.
        :param storage_results_file_path (pathlib.Path): A valid path to a file where the storage computations should be written into. If None is provided, the function skips the storage analysis.
        :return (dict[str:int]): Returns the election tally as a dictionary with all the options as keys, and the votes received as values.
        """
        election_options: list[dict] = await script_runner.getElectionOptions(election_id=election_id)

        ballots_withdrawn_events = await tx_runner.tallyElection(election_id=election_id, tx_signer_address=tx_signer_address, gas_results_file_path=gas_results_file_path, storage_results_file_path=storage_results_file_path)

        for ballots_withdrawn_event in ballots_withdrawn_events:
            log.info(f"Election {ballots_withdrawn_event["election_id"]} tallied after processing {ballots_withdrawn_event["ballots_withdrawn"]} ballots.")

        # Fetch the election results, namely the array of encrypted ballot options
        encrypted_ballots: list[str] = await script_runner.getElectionEncryptedBallots(election_id=election_id)

        # Recover the private encryption key from the path provided
        private_key = CryptoUtils.load_private_key_from_file(private_encryption_key_name)

        # Decrypt the ballot options. These were base64 encoded initially, so they need to be decoded before decrypting
        decrypted_ballot_options: list[bytes] = []

        for encrypted_ballot in encrypted_ballots:
            # Decode the ballot option from a string first
            bytes_ballot_option: bytes = bytes(encrypted_ballot, encoding=option_encoding)
            decoded_ballot_option = base64.b64decode(bytes_ballot_option)

            decrypted_ballot_option: str = CryptoUtils.decrypt_message(ciphertext_message=decoded_ballot_option, private_key=private_key)

            decrypted_ballot_options.append(str(decrypted_ballot_option, encoding=option_encoding))
        
        # All the ballots are decrypted. Run another loop to split them from the salt, put it to another array and start counting options
        election_options_tally: dict[str:int] = {}
        # Pre-fill the election_options_tally with the current election options (values) as the keys for this dictionary and set each value, the vote counter
        # to 0 to start counting
        for election_option in election_options:
            election_options_tally[election_options[election_option]] = 0
        
        # Create an entry for invalid options as well
        election_options_tally["invalid"] = 0

        ballot_receipts: list[int] = []

        for decrypted_ballot_option in decrypted_ballot_options:
            # Split the decrypted ballot option by the character used to concatenate the option with the random salt
            option_elements: list[str] = decrypted_ballot_option.split(option_separator)

            # I expect 2 and exactly 2 elements from the string split before. Anything different than that is a problem!
            if (len(option_elements) != 2):
                log.error(f"ERROR: Found a illegally formatted ballot option: {decrypted_ballot_option}! Unable to process it further. Skipping...")
                continue

            # If the current option retrieved is among the ones in the tally dictionary
            if (option_elements[0] in election_options_tally):
                # Increase the tally by 1
                election_options_tally[option_elements[0]] += 1
            else:
                # Count it as an "invalid" one and log its contents for debug purposes
                election_options_tally["invalid"] += 1
                log.warning("CAUTION: Retrieved a Ballot with an invalid option: {option}. Ballot counted as 'invalid'")

            # Put the receipts in another return array
            ballot_receipts.append(int(option_elements[1]))

        # Done. Return the results
        return (election_options_tally, ballot_receipts)


async def validate_receipts(voter_address: str, election_id: int, election_ballot_receipts: list[int]) -> None:
    """
    This function validates all the ballot receipts retrieved from a VoteBox from the account with the address provided as input, under the election_id also provided as input. A ballot receipt is valid if the same number is in the VoteBox resource and the list provided, since this list was extracted from the encrypted ballot options.
    
    :param voter_address(str): The address for the account to use to validate the ballot with.
    :param election_id (int): The election identifier value for the Election instance that produced the ballot receipts list provided.
    :param ballot_receipts list[int]: A list with the random integers used to obfuscate the Election's Ballot options.
    """
    # Grab the list of ballot receipts from the votebox side.
    votebox_ballot_receipts: list[int] = await script_runner.getBallotReceipts(voter_address=voter_address, election_id=election_id)
    
    # Validate the receipts
    for ballot_receipt in votebox_ballot_receipts:
        if (ballot_receipt in election_ballot_receipts):
            log.info(f"Receipt '{ballot_receipt}' from account {voter_address} is valid.")
        else:
            log.info(f"Receipt '{ballot_receipt}' from account {voter_address} is invalid!")



async def finish_election(election_id: int, election_results: dict, ballot_receipts: list[int], tx_signer_address: str, gas_results_file_path: pathlib.Path = None, storage_results_file_path: pathlib.Path = None) -> None:
    """Function to finish this election by setting the election results computed into the resource instance itself, and setting its electionFinished flag to true, thus preventing this election from accepting any more ballots. This election instance must have had the election_results parameter set before.

    :param election_id (int): The election identifier for the Election to terminate.
    :param election_results (dict): A dictionary with the election results from the election with the id provided.
    :param ballot_receipts list[int]: A list with the random integers used to obfuscate the election options.
    :param tx_signer_address (str): The account address of the account that has the election in question stored in its storage account area.
    :param gas_results_file_path (pathlib.Path): A valid path to a file to where the gas calculations should be written into. If None is provided, the function skips the gas analysis.
    :param storage_results_file_path (pathlib.Path): A valid path to a file where the storage computations should be written into. If None is provided, the function skips the storage analysis.
    """    
    # Set the election to finish with the election_results previously set in this class instance. There are no events emitted with this transaction so
    # there's no immediate point in capturing the transaction response
    await tx_runner.finishElection(election_id=election_id, election_results=election_results, ballot_receipts=ballot_receipts, tx_signer_address=tx_signer_address, gas_results_file_path=gas_results_file_path, storage_results_file_path=storage_results_file_path)

    log.info(f"\nElection {election_id} is finished.")
    
    log.info("\nResults: ")
    for election_result in election_results:
        log.info(f"{election_result}: {election_results[election_result]} votes")

async def terminate_election(election_id: int, private_encryption_key_name: str, tx_signer_address: str, gas_results_file_path: pathlib.Path = None, storage_results_file_path: pathlib.Path = None) -> None:
    """
        This function aggregates the workings of the previous functions, in one single, asyncio runnable, function

        :param election_id (int): The election identifier for the Election instance to tally.
        :param private_encryption_key_path (str): The name of the file containing the private encryption key that can decrypt the ballot options. This filename should point to a file inside the '/keys' subfolder from this project directory. The key loading routine has this folder pre-configured. IMPORTANT: The correspondence between private and public keys used in this process is solely of the responsibility of the user. This process does not validates any keys at any point.
        :param tx_signer_address (str): The account address to use to digitally sign the transaction.
        :param gas_results_file_path (pathlib.Path): A valid path to a file to where the gas calculations should be written into. If None is provided, the function skips the gas analysis.
        :param storage_results_file_path (pathlib.Path): A valid path to a file where the storage computations should be written into. If None is provided, the function skips the storage analysis.
        :return (dict[str:int]): Returns the election tally as a dictionary with all the options as keys, and the votes received as values.
    """
    # The sub functions already validate all inputs and then some. Proceed with the calculations
    (election_results, election_ballot_receipts) = await tally_election(election_id=election_id, private_encryption_key_name=private_encryption_key_name, tx_signer_address=tx_signer_address, gas_results_file_path=gas_results_file_path, storage_results_file_path=storage_results_file_path)

    # Validate the ballot receipts for each account
    ctx: AccountConfig = AccountConfig()

    voter_addresses: list[str] = ctx.getAddresses()
    voter_addresses.remove(ctx.service_account["address"].hex())

    for voter_address in voter_addresses:
        await validate_receipts(voter_address=voter_address, election_id=election_id, election_ballot_receipts=election_ballot_receipts)

    # Finish the election by setting the election results and ballot receipts to the resource
    await finish_election(election_id=election_id, election_results=election_results, ballot_receipts=election_ballot_receipts, tx_signer_address=tx_signer_address, gas_results_file_path=gas_results_file_path, storage_results_file_path=storage_results_file_path)

if __name__ == "__main__":
    """
    Usage: python election_finisher <election_id> <election_index>
    :param election_id (int): The election identifier for the instance to finish, i.e., proceed with the tallying and publishing of results
    :param election_index (int): The index used to create the Election, which is needed here to retrieve the encryption key used in the process. 
    """
    # Extract and validate the arguments from the command line
    if (len(sys.argv) < 2):
        raise Exception("ERROR: Please provide a valid election_id to continue.")
        # In this case, I expect the election_id is the sys.argv[2] positional argument as well
    
    election_id: int = int(sys.argv[1].lower().strip())

    if (election_id < 0):
        raise Exception(f"Election destroy ERROR: Invalid election_id provided: {election_id}. Please provide a positive value to continue!")
    
    try:
        election_index: int = int(sys.argv[2])
    except Exception:
        raise Exception("ERROR: Please provide a valid election index to continue")
    
    ctx = AccountConfig()

    # Create the output files. Note that both functions in this module need the service account signature to run
    gas_results_file_name: str = f"{datetime.datetime.now().strftime("%d-%m-%yT%H:%M:%S")}_{ctx.service_account["address"].hex()}_{config.get(section="network", option="current")}_election_{election_id}_finishing_gas_results.csv"
    gas_results_file_path: pathlib.Path = pathlib.Path(os.getcwd()).joinpath("results", gas_results_file_name)

    storage_results_file_name: str = f"{datetime.datetime.now().strftime("%d-%m-%yT%H:%M:%S")}_{ctx.service_account["address"].hex()}_{config.get(section="network", option="current")}_election_{election_id}_finishing_storage_results.csv"
    storage_results_file_path: pathlib.Path = pathlib.Path(os.getcwd()).joinpath("results", storage_results_file_name)

    new_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(new_loop)

    new_loop.run_until_complete(terminate_election(election_id=election_id, private_encryption_key_name=election_private_encryption_keys_filenames[election_index], tx_signer_address=ctx.service_account["address"].hex(), gas_results_file_path=gas_results_file_path, storage_results_file_path=storage_results_file_path))
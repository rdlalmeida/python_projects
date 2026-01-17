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

async def tally_election(self, private_encryption_key_name: str, tx_signer_address: str, gas_results_file_path: pathlib.Path = None, storage_results_file_path: pathlib.Path = None) -> dict[str: int]:
        """
        Function to trigger the end of the election by processing their ballots, retrieving the ballot.options, decrypting and processing them, tallying the results and producing the winning option. This function also sets the function as finished.

        :param private_encryption_key_path (str): The name of the file containing the private encryption key that can decrypt the ballot options. This filename should point to a file inside the '/keys' subfolder from this project directory. The key loading routine has this folder pre-configured. IMPORTANT: The correspondence between private and public keys used in this process is solely of the responsibility of the user. This process does not validates any keys at any point.
        :param tx_signer_address (str): The account address to use to digitally sign the transaction.
        :param gas_results_file_path (pathlib.Path): A valid path to a file to where the gas calculations should be written into. If None is provided, the function skips the gas analysis.
        :param storage_results_file_path (pathlib.Path): A valid path to a file where the storage computations should be written into. If None is provided, the function skips the storage analysis.
        :return (dict[str:int]): Returns the election tally as a dictionary with all the options as keys, and the votes received as values.
        """
        if (self.election_id == None):
            raise Exception(f"ERROR: This Election instance does not have an active election yet!")
        
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


async def finish_election(self, election_id: int, election_results: dict, ballot_receipts: list[int], tx_signer_address: str, gas_results_file_path: pathlib.Path = None, storage_results_file_path: pathlib.Path = None) -> None:
    """Function to finish this election by setting the election results computed into the resource instance itself, and setting its electionFinished flag to true, thus preventing this election from accepting any more ballots. This election instance must have had the election_results parameter set before.

    :param election_id (int): The election identifier for the Election to terminate.
    :param election_results (dict): A dictionary with the election results from the election with the id provided.
    :param ballot_receipts list[int]: A list with the random integers used to obfuscate the election options.
    :param tx_signer_address (str): The account address of the account that has the election in question stored in its storage account area.
    :param gas_results_file_path (pathlib.Path): A valid path to a file to where the gas calculations should be written into. If None is provided, the function skips the gas analysis.
    :param storage_results_file_path (pathlib.Path): A valid path to a file where the storage computations should be written into. If None is provided, the function skips the storage analysis.
    """
    # TODO: continue adapting this shit and finish this crap once and for all!!!!    
    
    # Set the election to finish with the election_results previously set in this class instance. There are no events emitted with this transaction so
    # there's no immediate point in capturing the transaction response
    await self.tx_runner.finishElection(election_id=self.election_id, election_results=self.election_results, ballot_receipts=self.ballot_receipts, tx_signer_address=tx_signer_address, gas_results_file_path=gas_results_file_path, storage_results_file_path=storage_results_file_path)

    # Check that the election was indeed finished
    election_finished = await self.script_runner.isElectionFinished(election_id=self.election_id)

    if (not election_finished):
        raise Exception(f"ERROR: Election {self.election_id} failed to finish. The finished flag was not properly set.")
    
    # Retrieve the election winning option
    winning_options: dict[str:int] = await self.script_runner.getElectionWinner(election_id=self.election_id)

    log.info(f"Election {self.election_id} is finished. \nWinning option(s): ")
    for winning_option in winning_options:
        log.info(f"'{winning_option}' with {winning_options[winning_option]} votes")







if __name__ == "__main__":
    """
    Usage: python election_finisher <election_id>
    :param election_id (int): The election identifier for the instance to finish, i.e., proceed with the tallying and publishing of results 
    """
    # Extract and validate the arguments from the command line
    if (len(sys.argv) < 2):
        raise Exception("ERROR: Please provide a valid election_id to continue.")
        # In this case, I expect the election_id is the sys.argv[2] positional argument as well
    
    election_id: int = int(sys.argv[1].lower().strip())

    if (election_id < 0):
        raise Exception(f"Election destroy ERROR: Invalid election_id provided: {election_id}. Please provide a positive value to continue!")

    # Grab a context object
    ctx = AccountConfig()

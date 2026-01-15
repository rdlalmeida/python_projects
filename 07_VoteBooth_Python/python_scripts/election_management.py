import os, pathlib
from python_scripts.cadence_scripts import ScriptRunner
from python_scripts.cadence_transactions import TransactionRunner
from python_scripts.event_management import EventRunner
from python_scripts import crypto_management
from common import utils
import configparser
import base64
from flow_py_sdk import cadence


import logging
log = logging.getLogger(__name__)
utils.configureLogging()

config = configparser.ConfigParser()
config.read(pathlib.Path(os.getcwd()).joinpath("common", "config.ini"))

class Election(object):
    def __init__(self) -> None:
        super().__init__()

        self.election_id: int = None
        self.election_public_encryption_key: str = None
        self.election_options: dict[int:str] = None
        self.election_results: dict[str:int] = None
        self.ballot_receipts: list[int] = None
        self.option_separator = config.get(section="encryption", option="separator")
        self.encoding = config.get(section="encryption", option="encoding")
        self.free = False

        self.tx_runner = TransactionRunner()
        self.script_runner = ScriptRunner()
        self.event_runner = EventRunner()
        self.event_runner.configureDeployerAddress()

    async def create_election(
            self,
            new_election_name: str,
            new_election_ballot: str,
            new_election_options: dict[int, str],
            new_election_public_key: str,
            new_election_storage_path: str,
            new_election_public_path: str,
            free_election: bool,
            new_tx_signer_address: str,
            gas_results_file_path: pathlib.Path = None,
            storage_results_file_path: pathlib.Path = None
        ) -> int:
        """Function to create a new Election into this class, if none is set so far. This class admits one and only one election per class instance. If the class's self.election_id is not None, this function fails to prevent it from replacing an active election.

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
        :return (int): If successful, this function returns the electionId of the new resource created
        """
        # Only one active election per class is allowed 
        if (self.election_id != None):
            raise Exception(f"ERROR: This object already has an active election with id {self.election_id}")
        
        log.info(f"Creating a new election for {new_election_name}...")

        election_id: int = await self.tx_runner.createElection(
            election_name=new_election_name,
            election_ballot=new_election_ballot,
            election_options=new_election_options,
            election_public_key=new_election_public_key,
            election_storage_path=new_election_storage_path,
            election_public_path=new_election_public_path,
            tx_signer_address=new_tx_signer_address,
            gas_results_file_path=gas_results_file_path,
            storage_results_file_path=storage_results_file_path
        )


        log.info(f"Successfully created Election with id {election_id} and name '{new_election_name}'")
        
        self.election_id = election_id
        self.free = free_election

        # Set the election_public_encryption_key internally as well for easier retrieval
        self.election_public_encryption_key = new_election_public_key

        # The election options also
        self.election_options = new_election_options

        return election_id
    

    async def destroy_election(self, tx_signer_address: str, gas_results_file_path: pathlib.Path = None, storage_results_file_path: pathlib.Path = None) -> list[dict]:
        """
        Function to destroy the election currently associated to this class. This function fails if the self.election_id parameter for this class is still None.
        :param gas_results_file_path (pathlib.Path): A valid path to a file to where the gas calculations should be written into. If None is provided, the function skips the gas analysis.
        :param storage_results_file_path (pathlib.Path): A valid path to a file where the storage computations should be written into. If None is provided, the function skips the storage analysis.
        :return (list[dict]): Returns the ElectionStandard.ElectionDestroyed event parameters in the format
        {
            "election_id": int,
            "ballots_stored": int
        }
        """
        if (self.election_id == None):
            raise Exception("ERROR: Election no longer exists!")
        
        log.info(f"Destroying election {self.election_id}...")
        
        election_destroyed_events = await self.tx_runner.deleteElection(
            election_id=self.election_id,
            tx_signer_address=tx_signer_address,
            gas_results_file_path=gas_results_file_path,
            storage_results_file_path=storage_results_file_path
        )

        for election_destroyed_event in election_destroyed_events:
            log.info(f"Successfully destroyed Election with id {election_destroyed_event["election_id"]}. It had {election_destroyed_event["ballots_stored"]} ballots in it")
        
        # Election destroyed. Set the internal election_id to None and return the old value back
        self.election_id = None

        return election_destroyed_events
    

    async def create_votebox(self, tx_signer_address: str = None, tx_proposer_address: str = None, tx_payer_address: str = None, tx_authorizer_address: list[str] = None, gas_results_file_path: pathlib.Path = None, storage_results_file_path: pathlib.Path = None) -> list[dict]:
        """
        Function to create a new VoteBox resource in the tx_signer_address account provided.

        :param tx_signer_address (str): The account address to use to digitally sign the transaction.
        :param tx_proposer_address (str): The address of the account that proposes the transaction.
        :param tx_payer_address (str): The address of the account that pays for the network and gas fees for the transaction.
        :param tx_authorizer_address (list[str]): The list of addresses for the accounts that provide the authorizations defined in the "prepare" block of the transaction.
        :return (list[dict]): Returns the VoteBoxStandard.VoteBoxCreated event parameters in the format
        {
            "voter_address": str
        }
        """
        voter_address: str = (tx_signer_address or tx_proposer_address)
        log.info(f"Creating a new VoteBox for account {voter_address}")
        
        votebox_created_events = await self.tx_runner.createVoteBox(tx_signer_address=tx_signer_address, tx_proposer_address=tx_proposer_address, tx_payer_address=tx_payer_address, tx_authorizer_address=tx_authorizer_address, gas_results_file_path=gas_results_file_path, storage_results_file_path=storage_results_file_path)

        for votebox_created_event in votebox_created_events:
            log.info(f"Successfully created a VoteBox for account {votebox_created_event["voter_address"]}")
        
        return votebox_created_events

    
    async def destroy_votebox(self, tx_signer_address: str = None, tx_proposer_address: str = None, tx_payer_address: str = None, tx_authorizer_address: list[str] = None, gas_results_file_path: pathlib.Path = None, storage_results_file_path: pathlib.Path = None) -> list[dict]:
        """
        Function to destroy a VoteBox resource from the account in the tx_signer_address account provided.

        :param tx_signer_address (str): The account address to use to digitally sign the transaction.
        :param tx_proposer_address (str): The address of the account that proposes the transaction.
        :param tx_payer_address (str): The address of the account that pays for the network and gas fees for the transaction.
        :param tx_authorizer_address (list[str]): The list of addresses for the accounts that provide the authorizations defined in the "prepare" block of the transaction.        :param gas_results_file_path (pathlib.Path): A valid path to a file to where the gas calculations should be written into. If None is provided, the function skips the gas analysis.
        :param storage_results_file_path (pathlib.Path): A valid path to a file where the storage computations should be written into. If None is provided, the function skips the storage analysis.
        :return (list[dict]): Returns the event parameters in the format
        {
            "voter_address": str
        }
        """
        votebox_destroyed_events = await self.tx_runner.deleteVoteBox(tx_signer_address=tx_signer_address, tx_proposer_address=tx_proposer_address, tx_payer_address=tx_payer_address, tx_authorizer_address=tx_authorizer_address, gas_results_file_path=gas_results_file_path, storage_results_file_path=storage_results_file_path)
        
        for votebox_destroyed_event in votebox_destroyed_events:
            log.info(f"Successfully deleted a VoteBox for account {votebox_destroyed_event["voter_address"]}, with {votebox_destroyed_event["active_ballots"]} active ballots still in it. This VoteBox was used to vote in {len(votebox_destroyed_event["elections_voted"])} elections:")
        
            index: int = 0
            for active_election_id in votebox_destroyed_event["elections_voted"]:
                log.info(f"Election #{index}: {active_election_id}")
                index += 1
        
        return votebox_destroyed_events

    
    async def mint_ballot_to_votebox(self, votebox_address: str, tx_signer_address: str, gas_results_file_path: pathlib.Path = None, storage_results_file_path: pathlib.Path = None) -> list[dict]:
        """Function to mint a new Ballot for the VoteBox resource in the account with the address provided as tx_signer_address. If the Election class in question does not have an active election in it, this function raises an Exception.

        :param votebox_address (str): The account address to where the new Ballot is to be deposited to. This account should have a VoteBox resource already configured in it.
        :param tx_signer_address (str): The account address to use to digitally sign the transaction.
        :param gas_results_file_path (pathlib.Path): A valid path to a file to where the gas calculations should be written into. If None is provided, the function skips the gas analysis.
        :param storage_results_file_path (pathlib.Path): A valid path to a file where the storage computations should be written into. If None is provided, the function skips the storage analysis.
        :return (list[dict]): Returns the BallotStandard.BallotCreated event parameters in the format
        {
            "ballot_id": int,
            "linked_election_id": int
        }
        """
        if (self.election_id == None):
            raise Exception(f"ERROR: This Election instance does not have an active election in it!")
        
        try:
            ballot_created_events = await self.tx_runner.createBallot(election_id=self.election_id, recipient_address=votebox_address, tx_signer_address=tx_signer_address, gas_results_file_path=gas_results_file_path, storage_results_file_path=storage_results_file_path)

            for ballot_created_event in ballot_created_events:
                log.info(f"Successfully created Ballot with id {ballot_created_event["ballot_id"]} attached to Election {ballot_created_event["linked_election_id"]} for account {votebox_address}")
            
            return ballot_created_events
        except Exception as e:
            log.error(f"Unable to create a new Ballot to {votebox_address}: ")
            log.error(e)

    
    async def cast_ballot(self, option_to_set: str, tx_signer_address: str = None, tx_proposer_address: str = None, tx_payer_address: str = None, tx_authorizer_address: list[str] = None, gas_results_file_path: pathlib.Path = None, storage_results_file_path: pathlib.Path = None) -> int:
        """Function to cast a Ballot stored in the VoteBox resource in the account from the tx_signer_address provided with the encrypted and salted version of the option provided, as long as a Ballot exists for the election_id configured in the current Election object. This function also salts and encrypts the option provided before setting it in the Ballot.option in question.
        :param option_to_set (str): The option to set the Ballot to, as defined in the election options set values.
        :param tx_signer_address (str): The account address to use to digitally sign the transaction.
        :param tx_proposer_address (str): The address of the account that proposes the transaction.
        :param tx_payer_address (str): The address of the account that pays for the network and gas fees for the transaction.
        :param tx_authorizer_address (list[str]): The list of addresses for the accounts that provide the authorizations defined in the "prepare" block of the transaction.
        :param gas_results_file_path (pathlib.Path): A valid path to a file to where the gas calculations should be written into. If None is provided, the function skips the gas analysis.
        :param storage_results_file_path (pathlib.Path): A valid path to a file where the storage computations should be written into. If None is provided, the function skips the storage analysis.
        :return (int): If successful, this function returns the random salt used to obfuscate the Ballot option.
        """
        if (self.election_id == None):
            raise Exception(f"ERROR: This Election instance does not have an active election yet!")
        elif (self.election_public_encryption_key == None):
            raise Exception(f"ERROR: This Election class does not have a public encryption key set yet!")
        
        voter_address: str = (tx_signer_address or tx_proposer_address)
        
        # Generate a random value between the limits defined in the config file
        option_salt: int = crypto_management.generate_random_salt()

        # Append the generated random to the option to set
        salted_option: str = option_to_set + self.option_separator + str(option_salt)

        # Encrypt this option with the public encryption key set in this class instance
        # Retrieve the RSAPublicKey object from the public key string
        current_public_key = crypto_management.load_public_key_from_string(key_string=self.election_public_encryption_key)

        # Use the reconstructed key to encrypt the salted option
        encrypted_salted_option: str = crypto_management.encrypt_message(
            plaintext_message=salted_option,
            public_key=current_public_key
        )

        base64_option: str = base64.b64encode(encrypted_salted_option)

        await self.tx_runner.castBallot(election_id=self.election_id, new_option=str(base64_option, encoding=self.encoding), tx_signer_address=tx_signer_address, tx_proposer_address=tx_proposer_address, tx_payer_address=tx_payer_address, tx_authorizer_address=tx_authorizer_address, gas_results_file_path=gas_results_file_path, storage_results_file_path=storage_results_file_path)

        log.info(f"Successfully cast a Ballot for account {voter_address} and for election {self.election_id}")

        # Return the random salt back to the function caller so it can be processed properly
        return option_salt
    

    async def submit_ballot(self, tx_signer_address: str = None, tx_proposer_address: str = None, tx_payer_address: str = None, tx_authorizer_address: list[str] = None, gas_results_file_path: pathlib.Path = None, storage_results_file_path: pathlib.Path = None) -> None:
        """
        Function to submit a previously cast Ballot from the VoteBox from the tx_signer_address account. This sends the Ballot to the Election configured in it (this one) to be tallied at a future date.

        :param tx_signer_address (str): The account address to use to digitally sign the transaction.
        :param tx_proposer_address (str): The address of the account that proposes the transaction.
        :param tx_payer_address (str): The address of the account that pays for the network and gas fees for the transaction.
        :param tx_authorizer_address (list[str]): The list of addresses for the accounts that provide the authorizations defined in the "prepare" block of the transaction.
        """
        if (self.election_id == None):
            raise Exception(f"ERROR: This Election instance does not have an active election yet!")
        
        # The submitBallot function can trigger either a BallotSubmitted or a BallotReplaced event depending on the current state 
        ballot_submitted_events = await self.tx_runner.submitBallot(election_id=self.election_id, tx_signer_address=tx_signer_address, tx_proposer_address=tx_proposer_address, tx_payer_address=tx_payer_address, tx_authorizer_address=tx_authorizer_address, gas_results_file_path=gas_results_file_path, storage_results_file_path=storage_results_file_path)

        voter_address: str = (tx_signer_address or tx_proposer_address)

        for ballot_submitted_event in ballot_submitted_events:
            # Test the dictionary structure returned to determine which event was triggered
            if "ballot_id" in ballot_submitted_event:
                # If this element exists, I got a BallotSubmitted
                log.info(f"Voter {voter_address} successfully submitted ballot {ballot_submitted_event["ballot_id"]} to election {ballot_submitted_event["election_id"]}")

            elif "old_ballot_id" in ballot_submitted_event:
                # If this element is present, I got a BallotReplaced instead
                log.info(f"Voter {voter_address} successfully replaced ballot {ballot_submitted_event["old_ballot_id"]} with ballot {ballot_submitted_event["new_ballot_id"]} for election {ballot_submitted_event["election_id"]}")
            else:
                # If both above verifications failed, raise an Exception because something else must have gone wrong.
                raise Exception("ERROR: Submitted a ballot but it did not triggered a BallotSubmitted nor a BallotReplaced event!")
    

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
        
        if (self.election_options == None):
            raise Exception(f"ERROR: Unable to tally Election {self.election_id} without a set of valid election options defined first.")

        ballots_withdrawn_events = await self.tx_runner.tallyElection(election_id=self.election_id, tx_signer_address=tx_signer_address, gas_results_file_path=gas_results_file_path, storage_results_file_path=storage_results_file_path)

        for ballots_withdrawn_event in ballots_withdrawn_events:
            log.info(f"Election {ballots_withdrawn_event["election_id"]} tallied after processing {ballots_withdrawn_event["ballots_withdrawn"]} ballots.")

        # Fetch the election results, namely the array of encrypted ballot options
        encrypted_ballots: list[str] = await self.script_runner.getElectionEncryptedBallots(election_id=self.election_id)

        # Recover the private encryption key from the path provided
        private_key = crypto_management.load_private_key_from_file(private_encryption_key_name)

        # Decrypt the ballot options. These were base64 encoded initially, so they need to be decoded before decrypting
        decrypted_ballot_options: list[bytes] = []

        for encrypted_ballot in encrypted_ballots:
            # Decode the ballot option from a string first
            bytes_ballot_option: bytes = bytes(encrypted_ballot, encoding=self.encoding)
            decoded_ballot_option = base64.b64decode(bytes_ballot_option)

            decrypted_ballot_option: str = crypto_management.decrypt_message(ciphertext_message=decoded_ballot_option, private_key=private_key)

            decrypted_ballot_options.append(str(decrypted_ballot_option, encoding=self.encoding))
        
        # All the ballots are decrypted. Run another loop to split them from the salt, put it to another array and start counting options
        election_options_tally: dict[str:int] = {}
        # Pre-fill the election_options_tally with the current election options (values) as the keys for this dictionary and set each value, the vote counter
        # to 0 to start counting
        for election_option in self.election_options:
            election_options_tally[self.election_options[election_option]] = 0
        
        # Create an entry for invalid options as well
        election_options_tally["invalid"] = 0

        ballot_receipts: list[int] = []

        for decrypted_ballot_option in decrypted_ballot_options:
            # Split the decrypted ballot option by the character used to concatenate the option with the random salt
            option_elements: list[str] = decrypted_ballot_option.split(self.option_separator)

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

        # Set this election instance election_results parameter with the results computed so far before returning the results
        self.election_results = election_options_tally

        # Same for the ballot receipts
        self.ballot_receipts = ballot_receipts

        # Done. Return the results
        return election_options_tally
    

    async def finish_election(self, tx_signer_address: str, gas_results_file_path: pathlib.Path = None, storage_results_file_path: pathlib.Path = None) -> None:
        """Function to finish this election by setting the election results computed into the resource instance itself, and setting its electionFinished flag to true, thus preventing this election from accepting any more ballots. This election instance must have had the election_results parameter set before.

        :param tx_signer_address (str): The account address of the account that has the election in question stored in its storage account area.
        :param gas_results_file_path (pathlib.Path): A valid path to a file to where the gas calculations should be written into. If None is provided, the function skips the gas analysis.
        :param storage_results_file_path (pathlib.Path): A valid path to a file where the storage computations should be written into. If None is provided, the function skips the storage analysis.
        """
        if (self.election_id == None):
            raise Exception(f"ERROR: This Election instance does not have an active election yet!")
        
        if (self.election_results == None):
            raise Exception(f"ERROR: Election {self.election_id} is not tallied yet. Cannot finish it!")
        
        if (self.ballot_receipts == None):
            raise Exception(f"ERROR: Election {self.election_id} does not have any ballot receipts yet. Cannot finish it!")
                
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


    async def get_active_elections(self, votebox_address: str = None) -> None:
        """Function to return the list of currently active elections. This function prints a list with all active election ids.

        :param (optional) votebox_address (str): If provided, this function retrieves the data from a unauthorized reference for the VoteBox in the account provided. If omitted, the data is retrieved from the election resource directly.
        """
        if (votebox_address == None):
            active_elections_from_election: list[int] = await self.script_runner.getActiveElections()
            
            log.info(f"Active elections retrieved from an Election resource: ")
            for active_election in active_elections_from_election:
                log.info(f"{active_election}")
        
        else:
            active_elections_from_votebox: list[int] = await self.script_runner.getActiveElections(votebox_address=votebox_address)

            log.info(f"Active elections retrieved from a VoteBox resource: ")
            for active_votebox_election in active_elections_from_votebox:
                log.info(f"{active_votebox_election}")


    async def get_election_name(self, votebox_address: str = None) -> None:
        """Function to print the name of the current election.

        :param (optional) votebox_address (str): If provided, this function retrieves the data from a unauthorized reference for the VoteBox in the account provided. If omitted, the data is retrieved from the election resource directly.
        """
        if (votebox_address == None):
            election_name_from_election: str = await self.script_runner.getElectionName(election_id=self.election_id)
                        
            log.info(f"Election {self.election_id} name: {election_name_from_election}")
        else:
            election_name_from_votebox: str = await self.script_runner.getElectionName(election_id=self.election_id, votebox_address=votebox_address)
            
            log.info(f"Election {self.election_id} name: {election_name_from_votebox}")


    async def get_election_ballot(self, votebox_address: str = None) -> None:
        """Function to print the ballot of the current election.

        :param (optional) votebox_address (str): If provided, this function retrieves the data from a unauthorized reference for the VoteBox in the account provided. If omitted, the data is retrieved from the election resource directly.
        """
        if (votebox_address == None):
            election_ballot_from_election: str = await self.script_runner.getElectionBallot(election_id=self.election_id)
            log.info(f"Election {self.election_id} name: {election_ballot_from_election}")

        else:
            election_ballot_from_votebox: str = await self.script_runner.getElectionBallot(election_id=self.election_id, votebox_address=votebox_address)
            log.info(f"Election {self.election_id} name: {election_ballot_from_votebox}")


    async def get_election_options(self, votebox_address: str = None) -> None:
        """Function to print the options available to the current election.

        :param (optional) votebox_address (str): If provided, this function retrieves the data from a unauthorized reference for the VoteBox in the account provided. If omitted, the data is retrieved from the election resource directly.
        """
        if (votebox_address == None):
            election_options_from_election: dict[int:str] = await self.script_runner.getElectionOptions(election_id=self.election_id)
            
            log.info(f"Election options from Election Resource: ")
            for election_option in election_options_from_election:
                log.info(f"Option {election_option}: {election_options_from_election[election_option]}")
        else:
            election_options_from_votebox: dict[int:str] = await self.script_runner.getElectionOptions(election_id=self.election_id, votebox_address=votebox_address)
            
            log.info(f"Election options from VoteBox Resource: ")
            for election_option in election_options_from_votebox:
                log.info(f"Option {election_option}: {election_options_from_votebox[election_option]}")


    async def get_election_id(self, votebox_address: str = None) -> None:
        """Function to print the election_id associated to the current election.

        :param (optional) votebox_address (str): If provided, this function retrieves the data from a unauthorized reference for the VoteBox in the account provided. If omitted, the data is retrieved from the election resource directly.
        """
        if (votebox_address == None):
            election_id_from_election: int = await self.script_runner.getElectionId(election_id=self.election_id)
            log.info(f"Election id returned from the Election: {election_id_from_election}")

        else:
            election_id_from_votebox: int = await self.script_runner.getElectionId(election_id=self.election_id, votebox_address=votebox_address)
            log.info(f"Election id returned from the VoteBox: {election_id_from_votebox}")


    async def get_election_public_encryption_key(self, votebox_address: str = None) -> None:
        """Function to print the public encryption key associated to the current election.

        :param (optional) votebox_address (str): If provided, this function retrieves the data from a unauthorized reference for the VoteBox in the account provided. If omitted, the data is retrieved from the election resource directly.
        """
        if (votebox_address == None):
            public_encryption_key_from_election: str = await self.script_runner.getPublicEncryptionKey(election_id=self.election_id)
            log.info(f"Public encryption key returned from the Election resource: {public_encryption_key_from_election}")
        else:
            public_encryption_key_from_votebox: list[int] = await self.script_runner.getPublicEncryptionKey(election_id=self.election_id, votebox_address=votebox_address)
            log.info(f"Public encryption key returned from the VoteBox resource: {public_encryption_key_from_votebox}")


    async def get_election_capability(self, votebox_address: str = None) -> None:
        """Function to print the public capability associated to the current election.

        :param (optional) votebox_address (str): If provided, this function retrieves the data from a unauthorized reference for the VoteBox in the account provided. If omitted, the data is retrieved from the election resource directly.
        """
        if (votebox_address == None):
            election_capability_from_election: cadence.Capability = await self.script_runner.getElectionCapability(election_id=self.election_id)
            log.info(f"Election capability returned from the Election resource: {election_capability_from_election.__str__()}")
        else:
            election_capability_from_votebox: cadence.Capability = await self.script_runner.getElectionCapability(election_id=self.election_id, votebox_address=votebox_address)
            log.info(f"Election capability returned from the VoteBox resource: {election_capability_from_votebox.__str__()}")


    async def get_election_totals(self, votebox_address: str = None) -> None:
        """Function to print the total ballots minted and submitted to the current election.

        :param (optional) votebox_address (str): If provided, this function retrieves the data from a unauthorized reference for the VoteBox in the account provided. If omitted, the data is retrieved from the election resource directly.
        """
        if (votebox_address == None):
            election_totals_from_election: dict[str:int] = await self.script_runner.getElectionTotals(election_id=self.election_id)
            log.info(f"Election totals retrieved from the Election resource: {election_totals_from_election}")

        else:
            election_totals_from_votebox: dict[str:int] = await self.script_runner.getElectionTotals(election_id=self.election_id, votebox_address=votebox_address)
            log.info(f"Election totals retrieved from the VoteBox resource: {election_totals_from_votebox}")


    async def get_election_storage_path(self) -> None:
        """Function to print the storage path where the current election resource is stored.
        """
        election_storage_path: str = await self.script_runner.getElectionStoragePath(election_id=self.election_id)
        log.info(f"Election {self.election_id} stored at path {election_storage_path}")


    async def get_election_public_path(self) -> None:
        """Function to print the public path where the current election public capability is published.
        """
        election_public_path: str = await self.script_runner.getElectionPublicPath(election_id=self.election_id)
        log.info(f"Election {self.election_id} published at path {election_public_path}")


    async def get_elections_list(self) -> None:
        """Function to print current active elections as retrieved from the VoteBooth ElectionIndex resource.
        """
        election_list: dict[int:str] = await self.script_runner.getElectionsList()

        log.info(f"Current active Elections, as retrieved from the VoteBooth.ElectionIndex resource: ")
        log.info(election_list)


    async def get_ballot_option(self, votebox_address: str = None) -> None:
        """Function to print the current option set for the ballot in the VoteBox resource in the account for the address provided.

        :param votebox_address (str): The address from where the the VoteBox resource reference is to be retrieved 
        """
        ballot_option: str = await self.script_runner.getBallotOption(election_id=self.election_id, votebox_address=votebox_address)
        log.info(f"Ballot option for election {self.election_id} and user {votebox_address}: {ballot_option}")


    async def get_ballot_id(self, votebox_address: str = None) -> None:
        """Function to print the ballot it for the ballot in the VoteBox resource in the account for the address provided.

        :param votebox_address (str): The address from where the the VoteBox resource reference is to be retrieved 
        """
        ballot_id: int = await self.script_runner.getBallotId(election_id=self.election_id, votebox_address=votebox_address)
        
        if (ballot_id != 0):

            log.info(f"Ballot id for election {self.election_id} and user {votebox_address}: {ballot_id}")


    async def get_election_results(self) -> None:
        """Function to print out the election results for the current election.
        """
        election_results: dict[str:int] = await self.script_runner.getElectionResults(election_id=self.election_id)
        log.info(f"Election {self.election_id} results: {election_results}")


    async def is_election_finished(self) -> None:
        """Function to print out the running state of the present election.
        """
        election_finished: bool = await self.script_runner.isElectionFinished(election_id=self.election_id)

        if (election_finished):
            log.info(f"Election {self.election_id} is finalized!")
        else:
            log.info(f"Election {self.election_id} is still running!")


    async def get_election_winner(self) -> None:
        """Function to print out the winner of the current election, if set.
        """
        election_winner: dict[str:int] = await self.script_runner.getElectionWinner(election_id=self.election_id)

        if (len(election_winner) > 0):
            log.info(f"Election {self.election_id} winning options: ")
            for option in election_winner:
                log.info(f"Option '{option}': {election_winner[option]} votes!")
        else:
            log.info(f"Election {self.election_id} is not yet tallied!")


    async def get_account_balance(self, account_address: str) -> None:
        """Function to print out account balances, in FLOW tokens, for the account with the address provided.

        :param account_address (str): The address of the account whose balance is to retrieve.
        """
        current_account_balance: float = await self.script_runner.getAccountBalance(recipient_address=account_address)

        log.info(f"Account {account_address} FLOW balance: {current_account_balance}")

    
    async def deleteVoteBox(self, tx_signer_address: str = None, tx_proposer_address: str = None, tx_payer_address: str = None, tx_authorizer_address: str = None, gas_results_file_path: pathlib.Path = None, storage_results_file_path: pathlib.Path = None) -> list[dict]:
        """
        Function to destroy a VoteBox resource from the account whose address is provided in the tx_signer_address argument.

        :param tx_signer_address (str): The address of the account that has the VoteBox resource stored in their account and can digitally sign the transaction to delete it.
        :param tx_proposer_address (str): The address of the account that proposes the transaction.
        :param tx_payer_address (str): The address of the account that pays for the network and gas fees for the transaction.
        :param tx_authorizer_address (list[str]): The list of addresses for the accounts that provide the authorizations defined in the "prepare" block of the transaction.
        :param gas_results_file_path (pathlib.Path): A valid path to a file to where the gas calculations should be written into. If None is provided, the function skips the gas analysis.
        :param storage_results_file_path (pathlib.Path): A valid path to a file where the storage computations should be written into. If None is provided, the function skips the storage analysis.
        :return (list[dict]): Returns the event parameters in the format
        {
            "voter_address": str
        }
        """
        votebox_deleted_events = await self.tx_runner.deleteVoteBox(tx_signer_address=tx_signer_address, tx_proposer_address=tx_proposer_address, tx_payer_address=tx_payer_address, tx_authorizer_address=tx_authorizer_address, gas_results_file_path=gas_results_file_path, storage_results_file_path=storage_results_file_path)

        for votebox_deleted_event in votebox_deleted_events:
            log.info(f"Successfully deleted a VoteBox for account {votebox_deleted_event["voter_address"]} with {votebox_deleted_event["active_ballots"]} active ballots still in it. This VoteBox was used to vote in {len(votebox_deleted_event["elections_voted"])} elections")
        
        return votebox_deleted_events

    
    async def deleteVoteBooth(self, tx_signer_address: str = None, gas_results_file_path: pathlib.Path = None, storage_results_file_path: pathlib.Path = None) -> None:
        """
        Function to clean the storage account for the tx_signer_address parameter provided, namely, to destroy the ElectionIndex and VoteBoothBallotPrinterAdmin resources.

        :param tx_signer_address (str): The address of the account that has the VoteBooth related resources in the storage account.
        :param tx_proposer_address (str): The address of the account that proposes the transaction.
        :param tx_payer_address (str): The address of the account that pays for the network and gas fees for the transaction.
        :param tx_authorizer_address (list[str]): The list of addresses for the accounts that provide the authorizations defined in the "prepare" block of the transaction.
        :param gas_results_file_path (pathlib.Path): A valid path to a file to where the gas calculations should be written into. If None is provided, the function skips the gas analysis.
        :param storage_results_file_path (pathlib.Path): A valid path to a file where the storage computations should be written into. If None is provided, the function skips the storage analysis.
        """

        await self.tx_runner.cleanupVoteBooth(tx_signer_address=tx_signer_address, gas_results_file_path=gas_results_file_path, storage_results_file_path=storage_results_file_path)

        log.info(f"Successfully cleaned up the VoteBooth contract from account {tx_signer_address}")
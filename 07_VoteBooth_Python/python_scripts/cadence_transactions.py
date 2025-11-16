from flow_py_sdk import (
    flow_client,
    cadence,
    Tx,
    ProposalKey,
    entities
)

import configparser
from common import utils, account_config
import pathlib
import os

from python_scripts.event_management import EventRunner
from python_scripts.cadence_scripts import ScriptRunner

# Setup logging capabilities
import logging
log = logging.getLogger(__name__)
utils.configureLogging()

class TransactionError(Exception):
    """Custom Exception to be raised when a Flow transaction was not properly executed.

    Attributes:
        tx_name: The name of the transaction that failed to execute.
    """

    def __init__(self, tx_name: str) -> None:
        config = configparser.ConfigParser()
        config.read(pathlib.Path(os.getcwd()).joinpath("common", "config.ini"))
        network = config.get(section="network", option="current")
        host = config.get(section=network, option="host")
        port = config.get(section=network, option="port")

        self.message = f"Transaction '{tx_name}' di not execute in network {host}:{port}"

        super().__init__(self.message)


class TransactionRunner():
    def __init__(self) -> None:
        super().__init__()
        self.ctx = account_config.AccountConfig()
        self.project_cwd = pathlib.Path(os.getcwd())

        config_path = self.project_cwd.joinpath("common", "config.ini")
        self.config = configparser.ConfigParser()
        self.config.read(config_path)

        self.event_runner = EventRunner()
        self.script_runner = ScriptRunner()

    
    async def getTransaction(self, tx_name: str, tx_arguments: list, tx_signer_address: str) -> Tx:
        """
        Simple internal function to abstract the logic of reading the config file, grab the transaction file, read it, and building the Tx object.

        @param tx_name: str - The name of the transaction file to retrieve and process.
        @param tx_arguments: list - A list with all the arguments to set to the transaction object to return.
        @param tx_signer_address: str - The address for the account to use to digitally sign the transaction object.

        @return Tx If successful, this function returns a configured Tx object ready to execute.
        """
        # Use this function to set up the self.event_runner object properly. Unfortunately I need to do this in an async function outside
        # of the class constructor
        if (self.event_runner.deployer_address == None):
            # This instruction either sets the event_runner.deployer_address to a proper address string, or raise an Exception if this
            # address string was not retrievable
            self.event_runner.configureDeployerAddress()

        try:
            tx_path = pathlib.Path(self.config.get(section="transactions", option=tx_name))
        except configparser.NoOptionError:
            log.error(f"No transaction file named '{tx_name}' configured for this project!")
            exit(-2)
        except Exception as e:
            log.error(f"Unable to retrieve a valid path for transaction '{tx_name}': ")
            exit(-1)

        # Use the beginning of this routine to also check if the signer address provided is properly configured, i.e., it belongs to an active account
        # in the current network. Set all the parameter to return as None initially to detect if a proper account match was found or not
        signer_address = None
        signer_key_id = None
        signer = None

        if (tx_signer_address == self.ctx.service_account["address"].hex()):
            signer_address = self.ctx.service_account["address"]
            signer_key_id = self.ctx.service_account["key_id"]
            signer = self.ctx.service_account["signer"]
        else:
            # I need to check with every one of the user accounts and see if the provided address matches any of the configured ones
            for account in self.ctx.accounts:
                # If a match is found, fill out the required parameters
                if (tx_signer_address == account["address"].hex()):
                    signer_address = account["address"]
                    signer_key_id = account["key_id"]
                    signer = account["signer"]

        # Check if a valid signer account was found in the meantime
        if (signer_address == None and signer_key_id == None and signer == None):
            raise Exception(f"Unable to configure a signer object for account {tx_signer_address}. The account is not configured for network {self.ctx.access_node_host}:{self.ctx.access_node_port}")

        # Get the transaction text to a variable
        tx_code = open(tx_path).read()

        async with flow_client(
            host=self.ctx.access_node_host, port=self.ctx.access_node_port
        ) as client:

            # Use the flow_client to retrieve the proposer object from the address provided
            latest_block = await client.get_latest_block()
            proposer = await client.get_account_at_latest_block(
                address=signer_address.bytes
            )

            # Begin the construction of the Tx object
            tx_object = Tx(
                code=tx_code,
                reference_block_id=latest_block.id,
                payer=signer_address,
                proposal_key=ProposalKey(
                    key_address=signer_address,
                    key_id=signer_key_id,
                    key_sequence_number=proposer.keys[0].sequence_number
                ),
            )

            # Run a loop to add all the arguments provided to the tx_object. This arguments need to be provided already in the expected "cadence" format that 
            # the transaction script expects. This function does not have the necessary context to make this determination.
            for argument in tx_arguments:
                tx_object = tx_object.add_arguments(argument)
            
            # Finish the object by adding the authorizers and envelope signature objects to it
            tx_object = tx_object.add_authorizers(signer_address)
            tx_object = tx_object.with_envelope_signature(
                signer_address,
                signer_key_id,
                signer
            )

            # Done. Return it

            return tx_object
    
    async def submitTransaction(self, tx_object: Tx) -> entities.TransactionResultResponse:
        """
        Simple internal function to abstract all the logic to submit a transaction for execution and process any raised errors. This is always the same process for most transactions, therefore it is best to encode it into a single function.

        @param tx_object: Tx - This function requires a previously prepared Tx-type object.

        @returns TransactionResultResponse An object that encapsules all the state changes related to the transaction executed, including events.
        """
        try:
            async with flow_client(
                host=self.ctx.access_node_host, port=self.ctx.access_node_port
            ) as client:
                tx_response: entities.TransactionResultResponse = await client.execute_transaction(tx=tx_object, wait_for_seal=True)

                return tx_response
        except Exception as e:
            log.error(f"Unable to execute transaction from account {tx_object.payer.hex()}: ")
            log.error(e)
            # Propagate the Exception upwards for additional treatment
            raise e


    async def createElection(self, election_name: str, election_ballot: str, election_options: dict[int: str], election_public_key: str, election_storage_path: str, election_public_path: str, tx_signer_address: str) -> list[dict]:
        """Function to create a new Election in the project environment.

        @param election_name: str - The name of election to create
        @param election_ballot: str - The election ballot to use in the election.
        @param election_options: dict[int: str] - A dictionary with the available options for the election just created.
        @param public_key: str - The public encryption key associated to the election created.
        @param election_storage_path: str - The storage path to where the election created should be saved to.
        @param election_public_path: str - The public path to where the public election capability should be published to.

        @return dict If successful, this function returns a dictionary with the ElectionCreated event parameters:
        {
            "election_id": int,
            "election_name": str
        }
        """
        
        tx_name: str = "01_create_election"
        # Prepare the arguments in a format that Cadence expects
        cadence_election_name = cadence.String(election_name)
        cadence_election_ballot = cadence.String(election_ballot)

        # Need to encode the election options dictionary into the corresponding Cadence value.
        # In Cadence, Dictionaries are built from lists of KeyValuePair objects. I need to process each of the election_options entry individually
        current_options: list[cadence.KeyValuePair] = []

        for option in election_options:
            # Into a cadence.KeyValuePair
            current_option = cadence.KeyValuePair(
                key=cadence.UInt8(option),
                value=cadence.String(election_options[option])
            )

            current_options.append(current_option)
        
        # And finally, build the Dictionary from the List[KeyValuePair], as indicated in the module code (check types.py)
        cadence_election_options: cadence.Dictionary = cadence.Dictionary(value=current_options)

        cadence_election_public_key: cadence.String = cadence.String(value=election_public_key)
        cadence_election_storage_path: cadence.Path = cadence.Path(domain="storage", identifier=election_storage_path)
        cadence_election_public_path: cadence.Path = cadence.Path(domain="public", identifier=election_public_path)

        tx_arguments: list = [
            cadence_election_name, 
            cadence_election_ballot,
            cadence_election_options,
            cadence_election_public_key,
            cadence_election_storage_path,
            cadence_election_public_path
        ]

        tx_object: Tx = await self.getTransaction(tx_name=tx_name, tx_arguments=tx_arguments, tx_signer_address=tx_signer_address)

        tx_response: entities.TransactionResultResponse = await self.submitTransaction(tx_object=tx_object)

        # Grab only the latest ElectionCreated event
        election_created_events: list[dict] = await self.event_runner.getElectionCreatedEvents(tx_response=tx_response)

        return election_created_events
    

    async def deleteElection(self, election_id: int, tx_signer_address: str) -> list[dict[str:int]]:
        """Function to delete an election identified by the id provided from the current environment.

        @param election_id: int - The identifier for the election to delete
        @param tx_signer_address: str - The account address to use to digitally sign the transaction.

        @return dict[str:int] The function returns the parameters from the ElectionDestroyed event in the format
        {
            "election_id": int,
            "ballots_stored": int
        }
        """
        tx_name: str = "07_destroy_election"

        #prepare the arguments in the Cadence format
        tx_arguments: list = [cadence.UInt64(election_id)]

        tx_object: Tx = await self.getTransaction(tx_name=tx_name, tx_arguments=tx_arguments, tx_signer_address=tx_signer_address)

        tx_response: entities.TransactionResultResponse = await self.submitTransaction(tx_object=tx_object)

        election_destroyed_events: list[dict] = await self.event_runner.getElectionDestroyedEvents(tx_response=tx_response)

        return election_destroyed_events
    

    async def createVoteBox(self, tx_signer_address: str) -> list[dict[str:str]]:
        """Function to create a votebox resource into the the account that is supposed to sign this transaction.

        @param tx_signer_address: str - The address of the account that is going to digitally sign this transaction.

        @return dict[str:str] The function returns the parameters from the VoteBoxCreated event in the format
        {
            "voter_address": str
        }
        """
        tx_name: str = "02_create_vote_box"
        # This transaction needs no arguments to run
        tx_arguments: list = []

        tx_object: Tx = await self.getTransaction(tx_name=tx_name, tx_arguments=tx_arguments, tx_signer_address=tx_signer_address)

        tx_response: entities.TransactionResultResponse = await self.submitTransaction(tx_object=tx_object)
        
        # Grab the VoteBoxCreated event list
        votebox_created_events: list[dict[str:str]] = await self.event_runner.getVoteBoxCreatedEvents(tx_response=tx_response)

        return votebox_created_events
    

    async def deleteVoteBox(self, tx_signer_address: str) -> list[dict[str:str]]:
        """Function to delete a votebox resource from the account storage for the user that digitally signs this transaction.

        @param tx_signer_address: str - The address of the account that is going to digitally sign this transaction.

        @return dict[str:str] The function returns the parameters from the VoteBoxDestroyed event in the format
        {
            "elections_voted": list[int],
            "active_ballots": int,
            "voter_address": str
        }
        """
        tx_name: str = "08_destroy_votebox"

        # No arguments needed for this one as well
        tx_arguments: list = []

        tx_object: Tx = await self.getTransaction(tx_name=tx_name, tx_arguments=tx_arguments, tx_signer_address=tx_signer_address)

        tx_response: entities.TransactionResultResponse = await self.submitTransaction(tx_object=tx_object)

        votebox_destroyed_event:dict = await self.event_runner.getVoteBoxDestroyedEvents(tx_response=tx_response)

        return votebox_destroyed_event
    

    async def createBallot(self, election_id: int, recipient_address: str, tx_signer_address: str) -> list[dict[str:int]]:
        """Function to create and deposit a ballot resource into the votebox in the account identified by the recipient address.

        @param election_id: int - The identifier for the Election that this Ballot should be associated to.
        @param recipient_address: str - The address of the account where the VoteBox where this Ballot should be deposited into.
        @param tx_signer_address: str - The address of the account that can authorize this transaction with a digital signature.

        @return dict[str:int] The function returns the parameters from the BallotCreated event in the format
        {
            "ballot_id": int,
            "linked_election_id": int
        }
        """
        tx_name: str = "03_create_ballot"
        tx_arguments: list = [
            cadence.UInt64(election_id),
            cadence.Address.from_hex(recipient_address)
        ]

        tx_object: Tx = await self.getTransaction(tx_name=tx_name, tx_arguments=tx_arguments, tx_signer_address=tx_signer_address)

        tx_response: entities.TransactionResultResponse = await self.submitTransaction(tx_object=tx_object)

        ballot_created_event: dict[str:int] = await self.event_runner.getBallotCreatedEvents(tx_response=tx_response)

        return ballot_created_event
    

    async def castBallot(self, election_id: int, new_option: str, tx_signer_address: str) -> None:
        """Function to set the option provided as the 'new_option' argument in a Ballot cast for the Election identified with the election_id provided, for a VoteBox in the account that digitally signs this transaction.

        @param election_id: int - The election identifier to select the ballot to cast.
        @param new_option: str -The new value to set the ballot's option to.
        @param tx_signer_address: str - The address of the account that can authorize this transaction with a digital signature.
        """
        tx_name: str = "04_cast_ballot"
        tx_arguments: list = [
            cadence.UInt64(election_id),
            cadence.String(new_option)
        ]

        tx_object: Tx = await self.getTransaction(tx_name=tx_name, tx_arguments=tx_arguments, tx_signer_address=tx_signer_address)

        await self.submitTransaction(tx_object=tx_object)

        log.info(f"Voter {tx_signer_address} cast a new option for election {election_id}")

    
    async def submitBallot(self, election_id: int, tx_signer_address: str) -> list[dict[str:int]]:
        """Function to submit a ballot in votebox from  the transaction signer address to the election with the id provided as argument.

        @param election_id: int - The election identifier to select the ballot to submit.
        @tx_signer_address: str - The address of the account that can authorize this transaction with a digital signature.

        @return dict[str:int] The function returns the parameters from the BallotSubmitted event in the format
        {
            "ballot_id": int,
            "election_id": int
        }
        """
        tx_name: str = "05_submit_ballot"
        tx_arguments: list = [
            cadence.UInt64(election_id)
        ]

        tx_object: Tx = await self.getTransaction(tx_name=tx_name, tx_arguments=tx_arguments, tx_signer_address=tx_signer_address)

        tx_response: entities.TransactionResultResponse = await self.submitTransaction(tx_object=tx_object)

        # This transaction can trigger either a BallotSubmitted or a BallotReplaced event depending on the state of the user's VoteBox.
        # If no Ballots exist for the current_election_id, this submission triggers the BallotSubmitted event. But if this Ballot
        # replaces a previously submitted one, then this transaction triggers the BallotReplaced instead

        # Start by grabbing the BallotSubmitted event for this transaction
        ballot_submitted_events: list[dict[str:int]] = await self.event_runner.getBallotSubmittedEvents(tx_response=tx_response)

        # And the respective BallotReplaced event as well. If all goes well, I should have only one item in either one of these lists.
        ballot_replaced_events: list[dict[str:int]] = await self.event_runner.getBallotReplacedEvents(tx_response=tx_response)

        # Case 1: I have one BallotSubmitted event and 0 BallotReplaced. The transaction submitted the first Ballot to the VoteBox resource
        if (len(ballot_submitted_events) > 0 and len(ballot_replaced_events) == 0):
            # All OK. Return the BallotSubmitted event details
            return ballot_submitted_events
        
        # Case 2: I have 0 BallotSubmitted events and at least one BallotReplaced event. The transaction replaces an previously submitted Ballot.
        elif (len(ballot_submitted_events) == 0 and len(ballot_replaced_events) > 0):
            return ballot_replaced_events
        # Any other case is an error. Raise the respective Exception
        elif (len(ballot_submitted_events) > 0 and len(ballot_replaced_events) > 0):
            # Got both events at once. This is an Error
            raise Exception(f"ERROR: Transaction triggered {len(ballot_submitted_events)} BallotSubmitted events and {len(ballot_replaced_events)} BallotReplaced events! One of these needs to be 0!")
        elif (len(ballot_submitted_events) == 0 and len(ballot_replaced_events) == 0):
            # And in this case, I got no events back! This is a problem as well!
            raise Exception(f"ERROR: Transaction did not triggered any BallotSubmitted or BallotReplaced events!")
        else:
            # Something else happened
            raise Exception(f"ERROR: Ballot submission for account {tx_signer_address} failed!")
        
    
    async def tallyElection(self, election_id: int, tx_signer_address: str) -> dict[str:int]:
        """Function to trigger the end of a running Election, the withdrawal of all submitted Ballots, and the computation of results.

        @param election_id: int - The election identifier for the election to be tallied.

        @return dict Returns the winning election option (or options in the case of a tie) in the format:
        {
            <election_option>: <vote_count>
        }
        """
        # TODO: FIX THIS TO DEAL WITH THE ENCRYPTED STUFF
        tx_name: str = "06_tally_election"
        tx_arguments: list = [cadence.UInt64(election_id)]
        tx_object: Tx = await self.getTransaction(tx_name=tx_name, tx_arguments=tx_arguments, tx_signer_address=tx_signer_address)

        tx_response: entities.TransactionResultResponse = await self.submitTransaction(tx_object=tx_object)

        ballots_withdrawn_events: list[dict[str:int]] = await self.event_runner.getBallotsWithdrawnEvents(tx_response=tx_response)

        if (len(ballots_withdrawn_events) > 0):
            return ballots_withdrawn_events[0]
        
    
    async def cleanupVoteBooth(self, tx_signer_address: str) -> None:
        """Function to delete every resource and active capability currently stored and active in the tx_signer_address account. This includes all Elections, active and otherwise, BallotPrinterAdmin, and Election index.

        @param tx_signer_address: str - The address of the account that can authorize this transaction with a digital signature.
        @return None This function should trigger a series of events, namely, ElectionIndexDestroyed, VoteBoothPrinterAdminDestroyed, and a series of ElectionDestroyed as well. As such, all the result printing happens at the end of this function, to prevent having to return a weird compounded dictionary.
        """
        tx_name: str = "09_cleanup_votebooth"
        tx_arguments: list = []
        tx_object: Tx = await self.getTransaction(tx_name=tx_name, tx_arguments=tx_arguments, tx_signer_address=tx_signer_address)

        tx_response: entities.TransactionResultResponse = await self.submitTransaction(tx_object=tx_object)

        # Grab all the events
        election_destroyed_events: dict[str:int] = await self.event_runner.getElectionDestroyedEvents(tx_response=tx_response)
        election_index_destroyed_events: dict[str:str] = await self.event_runner.getElectionIndexDestroyedEvents(tx_response=tx_response)
        votebooth_printer_admin_destroyed: dict[str:str] = await self.event_runner.getVoteBoothPrinterAdminDestroyedEvents(tx_response=tx_response)

        # It is easier to do all the log.info printing from this side
        log.info(f"Successfully deleted {len(election_destroyed_events)} Elections from the VoteBooth contract in account {tx_signer_address}:")
        for election_destroyed_event in election_destroyed_events:
            log.info(election_destroyed_event["election_id"])

        log.info(f"Successfully destroyed the ElectionIndex from account {election_index_destroyed_events[0]["account_address"]}")
        log.info(f"Successfully destroyed the VoteBoothPrinterAdmin from account {votebooth_printer_admin_destroyed[0]["account_address"]}")

    
    async def fundAllAccounts(self, amount: float, recipients: list[str], tx_signer_address: str) -> None:
        """Function to deposit the amount provided in the argument to each of the accounts included in the recipient address list.

        @param amount: float - The amount of FLOW token to transfer from the service account into each of the accounts in the recipient list.
        @param recipients: list[str] - The list of addresses for the accounts to transfer funds to.
        @param tx_signer_address: str - The address of the account that can authorize this transactions with a digital signature and with enough funds in its balance to execute this transaction.

        @return None Similar to other complex functions, the return dictionary for this one is not trivial as well. As such, all the log.info printing and event capturing happens in this one.
        """
        # Validate the amount provided
        if (amount < 0):
            raise Exception(f"ERROR: Invalid FLOW amount provided: {amount}. Please provide a positive float value for this parameter!")
        

        tx_name = "00_fund_all_accounts"
        tx_arguments: list = [cadence.UFix64(amount)]
        addresses: list[cadence.Address] = []

        for recipient in recipients:
            # NOTE: The "address" parameter in the user account list is already in the expected cadence.Address format.
            addresses.append(cadence.Address.from_hex(recipient))

        tx_arguments.append(cadence.Array(addresses))

        tx_object: Tx = await self.getTransaction(tx_name=tx_name, tx_arguments=tx_arguments, tx_signer_address=tx_signer_address)

        tx_response: entities.TransactionResultResponse = await self.submitTransaction(tx_object=tx_object)

        token_deposited_events: list[dict] = await self.event_runner.getTokensDepositedEvents(tx_response=tx_response)

        # Run the script to get the balance of all accounts, including the service_account
        current_accounts: dict = {
            "emulator_account": {
                "address": self.ctx.service_account["address"].hex(),
                "balance": await self.script_runner.getAccountBalance(account_address=self.ctx.service_account["address"].hex())
            }
        }

        for user_account in self.ctx.accounts:
            current_accounts[user_account["name"]] = {
                "address": user_account["address"].hex(),
                "balance": await self.script_runner.getAccountBalance(account_address=user_account["address"].hex())
            }

        for token_deposited_event in token_deposited_events:
            log.info(f"Successfully funded {token_deposited_event["amount"]} FLOW tokens into account {token_deposited_event["to"]}")

        for account in current_accounts:
            log.info(f"Account '{account}' ({current_accounts[account]["address"]}) balance = {current_accounts[account]["balance"]} FLOW")

    
    async def destroyVoteBoxBallot(self, election_id: int, tx_signer_address: str) -> dict[str:int]:
        """Function to destroy a single Ballot from a VoteBox in the tx_signer_address account, stored internally under the election_id key provided.

        @param election_id: int - The identifier for the Election that this Ballot should be associated to.
        @param tx_signer_address: str - The address of the account that can authorize this transaction with a digital signature.

        @return dict[str:int] The function returns the parameters from the BallotBurned event emitted in the format
        {
            "ballot_id": int,
            "linked_election_id": int
        }
        """
        tx_name: str = "10_destroy_votebox_ballot"
        tx_arguments: list = [cadence.UInt64(election_id)]
        tx_object: Tx = await self.getTransaction(tx_name=tx_name, tx_arguments=tx_arguments, tx_signer_address=tx_signer_address)

        tx_response: entities.TransactionResultResponse = await self.submitTransaction(tx_object=tx_object)

        ballots_burned_events: list[dict[str:int]] = await self.event_runner.getBallotBurnedEvents(tx_response=tx_response)

        for ballot_burned_event in ballots_burned_events:
            log.info(f"Ballot {ballot_burned_event["ballot_id"]} attached to election {ballot_burned_event["linked_election_id"]}")


    async def cleanupVoteBox(self, tx_signer_address: str) -> list[dict[str:int]]:
        """Function to cleanup the VoteBox resource retrieved from the account that signs the transaction. What this function does is to check the list of activeElectionIds from the ElectionIndex in the VoteBooth contract and validate that every Ballot currently stored in the VoteBox matched an active election. Does that don't are considered inactive and are burned on the spot.

        @param tx_signer_address - The address of the account that can authorize this transaction with a digital signature.

        @return list[dict[str:int]] The function returns a list with the parameters for all the BallotBurned events emitted during the cleanup process in the format
        [
        {
            "ballot_id": int,
            "linked_election_id": int
        }
        ] 
        """
        tx_name: str = "11_cleanup_votebox"
        tx_arguments: list = []
        tx_object: Tx = await self.getTransaction(tx_name=tx_name, tx_arguments=tx_arguments, tx_signer_address=tx_signer_address)

        tx_response: entities.TransactionResultResponse = await self.submitTransaction(tx_object=tx_object)

        ballot_burned_events: list[dict[str:int]] = await self.event_runner.getBallotBurnedEvents(tx_response=tx_response)

        for ballot_burned_event in ballot_burned_events:
            log.info(f"Ballot {ballot_burned_event["ballot_id"]} attached to election {ballot_burned_event["linked_election_id"]}")
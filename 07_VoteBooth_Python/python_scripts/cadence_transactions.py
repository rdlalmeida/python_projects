from flow_py_sdk import (
    flow_client,
    cadence,
    Tx,
    ProposalKey
)

import configparser
from common import utils, account_config
import pathlib
import os

from python_scripts.event_management import EventRunner

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

    
    async def getTransaction(self, tx_name: str, tx_arguments: list, tx_signer_address: str) -> Tx:
        """
        Simple internal function to abstract the logic of reading the config file, grab the transaction file, read it, and building the Tx object.

        @param tx_name: str - The name of the transaction file to retrieve and process.
        @param tx_arguments: list - A list with all the arguments to set to the transaction object to return.
        @param tx_signer_address: str - The address for the account to use to digitally sign the transaction object.

        @return Tx If successful, this function returns a configured Tx object ready to execute.
        """
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

        if (tx_signer_address.hex() == self.ctx.service_account["address"].hex()):
            signer_address = self.ctx.service_account["address"]
            signer_key_id = self.ctx.service_account["key_id"]
            signer = self.ctx.service_account["signer"]
        else:
            # I need to check with every one of the user accounts and see if the provided address matches any of the configured ones
            for account in self.ctx.accounts:
                # If a match is found, fill out the required parameters
                if (tx_signer_address.hex() == account["address"].hex()):
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
    
    async def submitTransaction(self, tx_object: Tx) -> None:
        """
        Simple internal function to abstract all the logic to submit a transaction for execution and process any raised errors. This is always the same process for most transactions, therefore it is best to encode it into a single function.

        @param tx_object: Tx - This function requires a previously prepared Tx-type object.
        """
        try:
            async with flow_client(
                host=self.ctx.access_node_host, port=self.ctx.access_node_port
            ) as client:
                await client.execute_transaction(tx=tx_object)
        except Exception as e:
            log.error(f"Unable to execute transaction from account {tx_object.payer.hex()}: ")
            log.error(e)
            exit(-1)


    async def createElection(self, election_name: str, election_ballot: str, election_options: dict[int: str], election_public_key: list[int], election_storage_path: str, election_public_path: str, tx_signer_address: str) -> int:
        """Function to create a new Election in the project environment.

        @param election_name: str - The name of election to create
        @param election_ballot: str - The election ballot to use in the election.
        @param election_options: dict[int: str] - A dictionary with the available options for the election just created.
        @param public_key: list[int] - The public encryption key associated to the election created.
        @param election_storage_path: str - The storage path to where the election created should be saved to.
        @param election_public_path: str - The public path to where the public election capability should be published to.

        @return int If successful, this function returns the election id of the Election resource created.
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

        # Same logic applies to cadence. Array. I need to encode each of the initial array elements into the expected cadence type from the contract 
        # or transaction. In this case, the createElection contract method expects a [UInt8] as election public key

        cadence_value_list: list[cadence.UInt8] = []
        for element in election_public_key:
            cadence_value_list.append(cadence.UInt8(element))

        # Done. Cast the array of cadence.UInt8 into a proper cadence.Array

        cadence_election_public_key: cadence.Array = cadence.Array(value=cadence_value_list)
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

        await self.submitTransaction(tx_object=tx_object)

        # Grab only the latest ElectionCreated event
        election_created_events: list[dict] = await self.event_runner.getElectionCreatedEvents(event_num=1)

        election_id: int = election_created_events[0]["election_id"]

        return election_id
    

    async def deleteElection(self, election_id: int, tx_signer_address: str) -> int:
        """Function to delete an election identified by the id provided from the current environment.

        @param election_id: int - The identifier for the election to delete
        @param tx_signer_address: str - The account address to use to digitally sign the transaction.

        @return int If the function is successful, it returns back the id from the delete election, as retrieved from a ElectionDestroyed event
        """
        tx_name: str = "07_destroy_election"

        #prepare the arguments in the Cadence format
        tx_arguments: list = [cadence.UInt64(election_id)]

        tx_object: Tx = await self.getTransaction(tx_name=tx_name, tx_arguments=tx_arguments, tx_signer_address=tx_signer_address)

        await self.submitTransaction(tx_object=tx_object)

        election_destroyed_events: list[dict] = await self.event_runner.getElectionDestroyedEvents(event_num=1)

        election_id: int = election_destroyed_events[0]["election_id"]

        return election_id
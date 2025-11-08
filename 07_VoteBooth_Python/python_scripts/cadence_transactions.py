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


class RunTransaction():
    def __init__(self) -> None:
        super().__init__()
        self.ctx = account_config.AccountConfig()
        self.project_cwd = pathlib.Path(os.getcwd())

        config_path = self.project_cwd.joinpath("common", "config.ini")
        self.config = configparser.ConfigParser()
        self.config.read(config_path)

        self.client = flow_client(host=self.ctx.access_node_host, port=self.ctx.access_node_port)

    
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

        # Use the flow_client to retrieve the proposer object from the address provided
        latest_block = await self.client.get_latest_block()
        proposer = await self.client.get_account_at_latest_block(
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
        # TODO
    

    async def fundAllAccounts(self, amount_to_transfer: float, tx_signer_address: str) -> None:
        """Function to transfer <amount_to_transfer> FLOW tokens from the service account and into each of the configured user accounts for the current network.

        @param amount_to_transfer: float - The number of FLOW tokens to transfer from the service account and into each of the remaining network accounts.
        @param tx_signer_address: str - The address for the account that is going to digitally sign this transaction
        """
        name = "00_fund_all_accounts"
        arguments = [cadence.UFix64(amount_to_transfer)]

        tx_object = self.getTransaction(tx_name=name, tx_arguments=arguments, tx_signer_address=tx_signer_address)



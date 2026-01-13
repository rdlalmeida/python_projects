import json
import logging
from pathlib import Path
import configparser
import os
from common import utils

from flow_py_sdk.cadence import Address
from flow_py_sdk.signer import InMemorySigner, HashAlgo, SignAlgo
from flow_py_sdk import flow_client


log = logging.getLogger(__name__)
utils.configureLogging()

project_cwd = Path(os.getcwd())
config_path = project_cwd.joinpath("common", "config.ini")

config = configparser.ConfigParser()
config.read(config_path)
network=config.get("network", "current")
flow_json_file=config.get("flow.json", "location")

class AccountConfig(object):
    def __init__(self) -> None:
        super().__init__()

        # Set the account access details at the start of the module
        self.access_node_host: str = config.get(network, "host")
        self.access_node_port: int = int(config.get(network, "port"))

        self.accounts = []

        # noinspection PyBroadException
        try:
            # Load the contents of this project's flow.json to a handy variable. Grab the location of the file from the configuration file
            json_file = open(Path(flow_json_file))
            data = json.load(json_file)
        except Exception:
            log.warning(
                f"Cannot open {flow_json_file}, using default settings",
                exc_info=True,
                stack_info=True,
            )

        for account in data["accounts"]:
            # Load the required parameters while testing the formatting of the JSON file
            if (data["accounts"][account]["key"]["hashAlgorithm"]):
                hash_algorithm = HashAlgo.from_string(data["accounts"][account]["key"]["hashAlgorithm"])
            else: 
                hash_algorithm = HashAlgo.from_string("SHA_256")

            if (data["accounts"][account]["key"]["signatureAlgorithm"]):
                signature_algorithm = SignAlgo.from_string(data["accounts"][account]["key"]["signatureAlgorithm"])
            else:
                signature_algorithm = SignAlgo.from_string("ECDSA_P256")

            if (data["accounts"][account]["key"]["location"]):
                private_key = open(data["accounts"][account]["key"]["location"]).readline()
            else:
                private_key = data["accounts"][account]["key"]

            # Turns out that the constructor for the InMemorySigner class does not like hexadecimal values prefixed with the usual '0x'
            # I need to test the current format of the private_key string and remove these characters if they are present
            if (private_key[0:2] == "0x"):
                # Skip the first 2 characters of the key string
                private_key = private_key[2:]
            
            # Repeat the process for the account addresses as well
            account_address = data["accounts"][account]["address"]

            if (account_address[0:2] == "0x"):
                account_address = account_address[2:]

            if (account == "emulator-account"):
                # If the account in question is the emulator account, set this one apart from the rest as the service account
                self.service_account = {
                    "name": account,
                    "address": Address.from_hex(account_address),
                    "key_id": 0,
                    "signer": InMemorySigner(
                        hash_algo=hash_algorithm,
                        sign_algo=signature_algorithm,
                        private_key_hex=private_key
                    )
                }
            elif (not account.__contains__("flow_test")):
                # Otherwise set it as another "normal" account.
                # NOTE: The key_id field refers to the index of the key in question, given that accounts can have multiple encryption keys stored. But 
                # the first key, as it is this case, has index = 0.
                # NOTE: The user accounts have an additional "receipts" dictionary to be filled with a format {election_id: [random_vals]} where, for each 
                # election voted, this parameter keeps a record of all the random values used to add salt to the Ballot option, which is also used to 
                # verify Ballots. I'm keeping these in an array because, for testing purposes only, at some point I want users to be able to submit
                # multiple ballots into a single election. But in regular operation, there should be only one item per one of these arrays
                self.accounts.append(
                    {
                        "name": account,
                        "address": Address.from_hex(data["accounts"][account]["address"]),
                        "key_id": 0,
                        "signer": InMemorySigner(
                            hash_algo=hash_algorithm,
                            sign_algo=signature_algorithm,
                            private_key_hex=private_key
                        ),
                        "receipts": {}
                    }
                )
    
    def addReceipt(self, voter_address: str, election_id: int, ballot_receipt: int) -> None:
        """This function adds a ballot receipt, which is the random value used as salt for encrypting the Ballot option, to the entry of the voter that cast the ballot in the first place. This function detects if the current user entry already has a key for the election_id provided or not. If so, it appends the provided ballot_receipt to it. Otherwise it creates a new one. If the voter_address provided does not exists in the current account list, this function raises and exception.

        @param voter_address: str The address of the account that submitted the Ballot.
        @param election_id: int The election identifier for the election where the ballot was submitted to.
        @param ballot_receipt: int The random value that was appended to the Ballot.option before encrypting it to be used as salt.
        """
        # Validate that the voter_address provided corresponds to one of the configured account
        for account in self.accounts:
            if (account["address"].hex() == voter_address):
                # Found a matching account. Add the new record to it.
                if (election_id in account["receipts"]):
                    # The election record already exists. Append the new receipt to it
                    account["receipts"][election_id].append(ballot_receipt)
                else:
                    # In this case, I need to create a new entry key as well
                    account["receipts"][election_id] = [ballot_receipt]

                # All done. Finish this
                return
        
        # If the for cycle finishes without finding a match to the voter_address provided, the account is not configured in this network yet
        raise Exception(f"ERROR: Voter address provided {voter_address} does not exist in the current account configuration!")

    
    def removeReceipt(self, voter_address: str, election_id: int, ballot_receipt: int) -> int:
        """And this function removes a given receipt from an existing set.
        
        @param voter_address: str The address of the account that has the receipt in it.
        @param election_id: int The election identifier for the election where the ballot was submitted to.
        @param ballot_receipt: int The receipt to be removed from the account's internal storage array.

        @returns int: If successful, this function returns the receipt removed from the account list.
        """
        # This function is very similar to the previous one to an extent
        for account in self.accounts:
            if (account["address"].hex() == voter_address):
                if (election_id in account["receipts"]):
                    # The election in question also exists. Continue.
                    try:
                        receipt_to_remove: int = account["receipts"][election_id].remove(ballot_receipt)

                        # Return the removed item. This is how this function exits successfully. Any other path raises an exception
                        return receipt_to_remove
                    except ValueError:
                        raise ValueError(f"ERROR: Receipt {ballot_receipt} is not among the receipts for election {election_id} for account {voter_address}!")
                else:
                    raise ValueError(f"ERROR: Voter {voter_address} has never voted for election {election_id}")

        raise Exception(f"ERROR: Voter address provided {voter_address} does not exist in the current account configuration!")
    

    def countReceipts(self, voter_address: str, election_id: int) -> int:
        """This function returns the number of receipts a giver voter identified with the voter_address provided currently stored under the election_id provided.

        @param voter_address: str The address of the account that has the receipt list in it.
        @param election_id: int The election identifier for the election where the ballots were submitted into.

        @returns int Returns the number of ballots for the election entry.
        """

        for account in self.accounts:
            if (account["address"].hex() == voter_address):
                if (election_id in account["receipts"]):
                    # All good. Count the number of receipt and return it
                    return len(account["receipts"][election_id])
                else:
                    raise Exception(f"ERROR: Voter {voter_address} has never voted for election {election_id}")
        
        raise Exception(f"ERROR: Voter address provided {voter_address} does not exist in the current account configuration!")
    

    def removeElectionReceipt(self, voter_address: str, election_id: int) -> dict[int:list[int]]:
        """This function removes the whole election entry from the account["receipts"] section and returns it back, if it exists.
        
        @param voter_address: str The address of the account that should have the election_id entry in it.
        @param election_id: int The election identifier for the election where the ballots where submitted into.

        @returns dict[int:list[int]] Returns the whole entry from the account["receipts"] that matches the election_id provided, if it exists.
        """
        for account in self.accounts:
            if (account["address"].hex() == voter_address):
                if (election_id in account["receipts"]):
                    # Grab the entry to delete to an independent variable
                    entry_to_return: dict[int:list[int]] = {election_id: account["receipts"][election_id]}

                    # Remove the whole entry from the internal dictionary
                    del account["receipts"][election_id]

                    # Return the entry removed
                    return entry_to_return
                else:
                    raise Exception(f"ERROR: Voter {voter_address} has never voted for election {election_id}")

        raise Exception(f"ERROR: Voter address provided {voter_address} does not exists in the current account configuration!")


    def getFlowClient() -> flow_client:
        new_client = flow_client(
            host=AccountConfig.access_node_host,
            port=AccountConfig.access_node_port
        )

        return new_client
    

    def getAccounts(self) -> dict[str:str]:
        """
        Simple function to return a digested version of the accounts configured for the current active network

        @return dict[str:str] This function returns a simple dictionary in the format {<accountName>: <accountAddress>}
        """

        network_accounts = {}

        network_accounts["emulator"] = self.service_account["address"].hex()

        for account in self.accounts:
            network_accounts[account["name"]] = account["address"].hex()
        
        return network_accounts
    
def getFlowClient(ctx:AccountConfig) -> flow_client:
    new_client = flow_client(
        host=ctx.access_node_host, port=ctx.access_node_port
    )

    return new_client


class GetServiceAccountDetails():
    """
    Helper to characterise the service account configured. This function logs out the account address, the account balance, deployed contracts, and configured keys.
    """
    def __init__(self) -> None:
        super().__init__()
        self.ctx = AccountConfig()

    async def run(self):
        async with flow_client(
            host=self.ctx.access_node_host, port=self.ctx.access_node_port 
        ) as client:

            service_account = await client.get_account_at_latest_block(
                address=self.ctx.service_account["address"].hex()
            )

            log.info(f"Service account address: {service_account.address.hex()}")
            log.info(f"Service account balance: {service_account.balance} FLOW")
            log.info(f"Service account deployed has {len(service_account.contracts)} contracts deployed: ")
            
            index = 0

            for contract in service_account.contracts:
                log.info(f"Contract ${index}: {contract}")
                index += 1
            
            log.info(f"Service Account has {len(service_account.keys)} public keys configured: ")
            index = 0
            for key in service_account.keys:
                log.info(f"Public Key #{index}: {key.hex()}")
                index += 1


class GetAccountDetails():
    """
    Helper characterise an account whose address is provided as input argument. Like the previous function, this one also prints out the account balance, account address, deployed contracts, and configured keys.
    """
    def __init__(self) -> None:
        super().__init__()
        self.ctx: AccountConfig = AccountConfig()

        self.user_accounts: list[str] = []

        for account in self.ctx.accounts:
            self.user_accounts.append(account["address"].hex())

    async def run(self, account_address: str) -> None:
        if (not self.user_accounts.__contains__(account_address.hex())):
            raise Exception(f"ERROR: Address provided : {account_address} is not configured in this project!")

        async with flow_client(
            host=self.ctx.access_node_host, port=self.ctx.access_node_port
        ) as client:
            
            # Get the account
            current_account = await client.get_account_at_latest_block(
                address=account_address.hex()
            )

            log.info(f"Account {account_address} address: {current_account.address.hex()}")
            log.info(f"Account {account_address} balance: {current_account.balance} FLOW")
            log.info(f"Account {account_address} deployed has {len(current_account.contracts)} contracts deployed!")
            index = 0

            for contract in current_account.contracts:
                log.info(f"Contract ${index}: {contract}")
                index += 1

            log.info(f"Account {account_address} has {len(current_account.keys)} public keys configured: ")

            index = 0
            for key in current_account.keys:
                log.info(f"Public Key #{index}: {key.hex()}")
                index+=1
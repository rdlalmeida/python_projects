import json
import logging
from pathlib import Path
import configparser
import os
from common import utils

from flow_py_sdk.cadence import Address
from flow_py_sdk.signer import InMemorySigner, HashAlgo, SignAlgo
from flow_py_sdk import flow_client

import aiohttp

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

        index = 1

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
            else: 
                # Otherwise set it as another "normal" account
                key_id = index
                index += 1

                self.accounts.append(
                    {
                        "name": account,
                        "address": Address.from_hex(data["accounts"][account]["address"]),
                        "key_id": key_id,
                        "signer": InMemorySigner(
                            hash_algo=hash_algorithm,
                            sign_algo=signature_algorithm,
                            private_key_hex=private_key
                        )
                    }
                )


    def getFlowClient() -> flow_client:
        new_client = flow_client(
            host=AccountConfig.access_node_host,
            port=AccountConfig.access_node_port
        )

        return new_client
    
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
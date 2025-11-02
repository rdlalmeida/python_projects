import json
import logging
from pathlib import Path
import configparser
import os

from flow_py_sdk.cadence import Address
from flow_py_sdk.signer import InMemorySigner, HashAlgo, SignAlgo


log = logging.getLogger(__name__)

config = configparser.ConfigParser()
config.read("./common/config.ini")
network=config.get("network", "current")

class Config(object):
    def __init__(self, flow_json_location: Path) -> None:
        super().__init__()

        # Set the account access details at the start of the module
        self.access_node_host: str = config.get(network, "host")
        self.access_node_port: int = int(config.get(network, "port"))

        self.accounts = []

        # noinspection PyBroadException
        try:
            # Load the contents of this project's flow.json to a handy variable
            json_file = open(flow_json_location)
            data = json.load(json_file)
        except Exception:
            log.warning(
                f"Cannot open {flow_json_location}, using default settings",
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

            self.accounts.append(
                {
                    "name": account,
                    "address": Address.from_hex(data["accounts"][account]["address"]),
                    "signer": InMemorySigner(
                        hash_algo=hash_algorithm,
                        sign_algo=signature_algorithm,
                        private_key_hex=private_key
                    )
                }
            )
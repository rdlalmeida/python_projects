import asyncio
import flow_py_sdk
from common import utils, account_config
from python_scripts.cadence_scripts import ScriptRunner
from python_scripts.cadence_transactions import TransactionRunner
import os, pathlib
import configparser
from python_scripts import contract_management

import logging
log = logging.getLogger(__name__)
utils.configureLogging()

project_cwd = pathlib.Path(os.getcwd())
config_path = project_cwd.joinpath("common", "config.ini")
config = configparser.ConfigParser()
config.read(config_path)

ctx = account_config.AccountConfig()

accounts = ctx.getAccounts()

election_names: list[str] = [
    "A. Bullfights",
    "B. Coconut Cake",
    "C. Basketball"
]

election_ballots: list[str] = [
    "A. What should happen to all bullfighters once we finally ban this retarded practice all over Portugal?",
    "B. What is the best frosting for coconut cake?",
    "C. Which NBA team is going to win the 2025-25 championship?"
]

election_options: list[dict[int: str]] = [
    {
        1: "Starve them to death",
        2: "Trick them into a shipping container and drop it into the ocean",
        3: "Enslave them and force them to build and clean animal shelters for the rest of their miserable life",
        4: "Process them into animal feed",
        5: "Tax them into poverty and use the money collected to open and finance public veterinarian clinics."
    },
    {
        1: "Powdered sugar",
        2: "Shredded coconut",
        3: "Tempered dark chocolate",
        4: "Butter-based frosting",
        5: "Nothing. Leave it as is"
    },
    {
        1: "Minnesota Timber Wolves",
        2: "Oklahoma City Thunder",
        3: "New York Knicks",
        4: "Cleveland Cavaliers",
        5: "None of the above"
    }
]

election_public_keys: list[list[int]] = [
    [87, 174, 84, 18, 106, 155, 246, 129, 83, 78, 24, 168, 183, 53, 39, 121, 60, 186, 137, 156, 247, 185, 9, 137, 100, 151, 208, 113, 59, 191, 26, 118],
    [51, 171, 190, 97, 148, 77, 139, 219, 238, 108, 187, 103, 11, 17, 101, 98, 82, 99, 198, 155, 229, 236, 199, 71, 83, 213, 183, 240, 193, 220, 78, 239],
    [2, 164, 77, 118, 115, 138, 60, 142, 115, 146, 41, 115, 4, 36, 56, 23, 183, 225, 212, 85, 28, 203, 62, 60, 162, 113, 133, 116, 215, 163, 53, 79]
]

election_storage_paths: list[str] = [
    "Election01",
    "Election02",
    "Election03"
]

election_public_paths: list[str] = [
    "PublicElection01",
    "PublicElection02",
    "PublicElection03"
]

async def main() -> None:
    """
    Main entry point for this project
    """
    # 0. Setup the project contracts
    # await contract_management.main(op="deploy")

    # Create a transaction runner
    tx_runner = TransactionRunner()

    election_index: int = 0

    temp_election_id: int = 157230162771973

    # 1. Setup an election with the data from the config file
    if (False): 
        election_id: int = await tx_runner.createElection(
            election_name=election_names[election_index],
            election_ballot=election_ballots[election_index],
            election_options=election_options[election_index],
            election_public_key=election_public_keys[election_index],
            election_storage_path=election_storage_paths[election_index],
            election_public_path=election_public_paths[election_index],
            tx_signer_address=ctx.service_account["address"]
        )

        log.info(f"Successfully created Election with id {election_id}")
    else:
        new_election_id: int = await tx_runner.deleteElection(election_id=temp_election_id, tx_signer_address=ctx.service_account["address"])

        log.info(f"Successfully deleted Election with id {new_election_id}")

    

if __name__ == "__main__":
    asyncio.run(main())
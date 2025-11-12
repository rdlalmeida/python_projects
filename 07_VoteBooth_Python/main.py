import asyncio
from common import utils, account_config
from python_scripts.cadence_scripts import ScriptRunner
from python_scripts.cadence_transactions import TransactionRunner
from python_scripts.event_management import EventRunner
from python_scripts import contract_management
import os, pathlib
import configparser
import random

import logging
log = logging.getLogger(__name__)
utils.configureLogging()

project_cwd = pathlib.Path(os.getcwd())
config_path = project_cwd.joinpath("common", "config.ini")
config = configparser.ConfigParser()
config.read(config_path)

ctx = account_config.AccountConfig()

accounts = ctx.getAccounts()

script_runner = ScriptRunner()
tx_runner = TransactionRunner()
event_runner = EventRunner()

# TODO: Implement the Ballot revoke mechanics
# TODO: Modify project/contracts to allow multiple votes per account (add entropy to the index string to submit to the Election resource) to allow 
# bulk submissions of ballots and test this project for bottlenecks. Otherwise I need to create a new account per new vote, which is not ideal.

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
    if(True):
        log.info("Rebuilding project contracts...")
        await contract_management.main(op="deploy")
        # log.info("Done!")

    # Create an event runner
    await event_runner.configureDeployerAddress()
    
    # Use this selector to chose between the pre-made elections in this file
    election_index: int = 0
    # Keep the id of the election in question for this process
    current_election_id: int = None

    # 0.1. Fund all test accounts
    if (True):
        amount: float = 10.4
        recipients: list[str] = []

        for user_account in ctx.accounts:
            recipients.append(user_account["address"].hex())

        result: dict[str:int] = await tx_runner.fundAllAccounts(amount=amount, recipients=recipients, tx_signer_address=ctx.service_account["address"].hex())

        log.info("OK!")


    # 1. Setup an election with the data from the config file
    if (False):
        log.info("Creating a new election...")

        election_created_event: dict = await tx_runner.createElection(
            election_name=election_names[election_index],
            election_ballot=election_ballots[election_index],
            election_options=election_options[election_index],
            election_public_key=election_public_keys[election_index],
            election_storage_path=election_storage_paths[election_index],
            election_public_path=election_public_paths[election_index],
            tx_signer_address=ctx.service_account["address"].hex()
        )

        current_election_id = election_created_event["election_id"]
        log.info(f"Successfully created Election with id {current_election_id} and name '{election_created_event["election_name"]}'")
    
    # 1.1 Destroy the current election
    if (False):
        log.info(f"Destroying election {current_election_id}...")
        election_destroyed_event: dict[str:int] = await tx_runner.deleteElection(
            election_id=current_election_id,
            tx_signer_address=ctx.service_account["address"].hex()
        )

        log.info(f"Successfully destroyed Election with id {election_destroyed_event["election_id"]}. It had {election_destroyed_event["ballots_stored"]} ballots in it")

    # 2. Create a VoteBox into each of the user accounts inside a loop
    if (False):
        for user_account in ctx.accounts:
            votebox_created_event: dict[str:str] = await tx_runner.createVoteBox(tx_signer_address=user_account["address"].hex())
            
            log.info(f"Successfully created a VoteBox for account {votebox_created_event["voter_address"]}")

    # 2.1 Destroy the VoteBox from the transaction signer's account
    if (False):
        votebox_destroyed_event: dict = await tx_runner.deleteVoteBox(tx_signer_address=ctx.accounts[0]["address"].hex())
        log.info(f"Successfully deleted a VoteBox for account {votebox_destroyed_event["voter_address"]}, with {votebox_destroyed_event["active_ballots"]} active ballots still in it. This VoteBox was used to vote in {len(votebox_destroyed_event["elections_voted"])} elections:")
        
        index: int = 0
        for active_election_id in votebox_destroyed_event["elections_voted"]:
            log.info(f"Election #{index}: {active_election_id}")
            index += 1

    # 3. Mint a blank Ballot into the account provided, for the election in question
    if (False):
        for user_account in ctx.accounts:
            ballot_created_event: dict[str:int] = await tx_runner.createBallot(election_id=current_election_id, recipient_address=user_account["address"].hex(), tx_signer_address=ctx.service_account["address"].hex())

            log.info(f"Successfully created Ballot with id {ballot_created_event["ballot_id"]} attached to Election {ballot_created_event["linked_election_id"]} for account {user_account["address"].hex()}")
        
        if (False):
            # Mint another round of Ballots just to be sure that this blows up
            for user_account in ctx.accounts:
                try:
                    ballot_created_event: dict[str:int] = await tx_runner.createBallot(election_id=current_election_id, recipient_address=user_account["address"].hex(), tx_signer_address=ctx.service_account["address"].hex())

                    log.info(f"Successfully created another Ballot with id {ballot_created_event["ballot_id"]} attached to Election {ballot_created_event["linked_election_id"]} for account {user_account["address"].hex()}")
                except Exception as e:
                    log.warning(f"WARNING: User {user_account["address"].hex()} already has a Ballot in store for election {current_election_id}")
    
    # 4. Cast the ballots for each of the user accounts to a random option from within the ones available for the election
    if (False):
        for user_account in ctx.accounts:
            random_index: int = random.randint(a=1, b=len(election_options[election_index]))
            # TODO: ADD THE ENCRYPTION AND RANDOM LOGIC HERE!
            random_option: str = election_options[election_index][random_index]

            # Cast the ballot
            await tx_runner.castBallot(election_id=current_election_id, new_option=random_option, tx_signer_address=user_account["address"].hex())
        

    # 5. Submit the cast ballots to the election
    if (False):
        for user_account in ctx.accounts:
            # The submitBallot function can trigger either a BallotSubmitted or a BallotReplaced event depending on the current state 
            ballot_event: dict[str:int] = await tx_runner.submitBallot(election_id=current_election_id, tx_signer_address=user_account["address"].hex())

            # Test the dictionary structure returned to determine which event was triggered
            if "ballot_id" in ballot_event:
                # If this element exists, I got a BallotSubmitted
                log.info(f"Voter {user_account["address"].hex()} successfully submitted ballot {ballot_event["ballot_id"]} to election {ballot_event["election_id"]}")

            elif "old_ballot_id" in ballot_event:
                # If this element is present, I got a BallotReplaced instead
                log.info(f"Voter {user_account["address"].hex()} successfully replaced ballot {ballot_event["old_ballot_id"]} with ballot {ballot_event["new_ballot_id"]} for election {ballot_event["election_id"]}")
            else:
                # If both above verifications failed, raise an Exception because something else must have gone wrong.
                raise Exception("ERROR: Submitted a ballot but it did not triggered a BallotSubmitted nor a BallotReplaced event!")


    # 6. Mint another round of Ballots to the user accounts, cast them again using a random option, and re-submit them to trigger the BallotReplaced event
    if (False):
        # Mint a new round of Ballots
        for user_account in ctx.accounts:
            ballot_created_event: dict[str:int] = await tx_runner.createBallot(election_id=current_election_id, recipient_address=user_account["address"].hex(), tx_signer_address=ctx.service_account["address"].hex())

            log.info(f"Successfully created another Ballot with id {ballot_created_event["ballot_id"]} to election {ballot_created_event["linked_election_id"]} for account {user_account["address"].hex()}")

        # Cast the randomly as well
        for user_account in ctx.accounts:
            random_index: int = random.randint(a=1, b=len(election_options[election_index]))
            random_option: str = election_options[election_index][random_index]

            # Cast the ballot
            await tx_runner.castBallot(election_id=current_election_id, new_option=random_option, tx_signer_address=user_account["address"].hex())

        # Submit the new round of ballots and test that the BallotReplaced event was triggered
        for user_account in ctx.accounts:
            ballot_event: dict[str:int] = await tx_runner.submitBallot(election_id=current_election_id, tx_signer_address=user_account["address"].hex())

            # Test the event returned
            if "ballot_id" in ballot_event:
                log.info(f"Voter {user_account["address"].hex()} successfully submitted ballot {ballot_event["ballot_id"]} to election {ballot_event["election_id"]}")

            elif "old_ballot_id" in ballot_event:
                log.info(f"Voter {user_account["address"].hex()} successfully replaced ballot {ballot_event["old_ballot_id"]} with ballot {ballot_event["new_ballot_id"]} for election {ballot_event["election_id"]}")
            else:
                raise Exception("ERROR: Submitted a ballot but it did not triggered a BallotSubmitted nor a BallotReplaced event!")

    # 7. Test out all the scripts just to be sure they work
    # Lemme create a handy dictionary to control the rest of this flow

    # 7.1 - 02_get_active_elections
    if(False):
        scripts_to_run: dict[str:bool] = {
            "02_get_active_elections": True,
            "03_get_election_name": True,
            "04_get_election_ballot": True,
            "05_get_election_options": True,
            "06_get_election_id": True,
            "07_get_public_encryption_key": True,
            "08_get_election_capability": True,
            "09_get_election_totals": True,
            "10_get_election_storage_path": True,
            "11_get_election_public_path": True,
            "12_get_elections_list": True,
            "13_get_ballot_option": True,
            "14_get_ballot_id": True,
            "15_get_election_results": True,
            "16_is_election_finished": True
        }

        if (scripts_to_run["02_get_active_elections"]):
            active_elections_from_votebox: list[int] = await script_runner.getActiveElections(votebox_address=ctx.accounts[1]["address"].hex())
            active_elections_from_election: list[int] = await script_runner.getActiveElections()

            for active_votebox_election in active_elections_from_votebox:
                if (not active_elections_from_election.__contains__(active_votebox_election)):
                    raise Exception(f"ERROR: Data mismatch detected. Election {active_votebox_election} is not among the ones retrieved from the election index resource.")
            
            for active_election in active_elections_from_election:
                if (not active_elections_from_election.__contains__(active_election)):
                    raise Exception(f"ERROR: Data mismatch detected. Election {active_election} is not among the ones retrieved from the votebox resource!")

            log.info(f"Elections currently active: ")
            for election_id in active_elections_from_election:
                log.info(f"{election_id}")            

    # 8. Withdraw ballots and compute tally

    # 9. Clean up project from network
    if (False):
        # Destroy the VoteBoxes in each of the user accounts
        for user_account in ctx.accounts:
            votebox_deleted_event: dict[str:str] = await tx_runner.deleteVoteBox(tx_signer_address=user_account["address"].hex())

            log.info(f"Successfully deleted a VoteBox for account {votebox_deleted_event["voter_address"]} with {votebox_deleted_event["active_ballots"]} active ballots still in it. This VoteBox was used to vote in {len(votebox_deleted_event["elections_voted"])} elections")
        
        # Destroy the resources from the VoteBooth contract
        await tx_runner.cleanupVoteBooth(tx_signer_address=ctx.service_account["address"].hex())

        log.info(f"Successfully cleaned up the VoteBooth contract from account {ctx.service_account["address"].hex()}")

    
if __name__ == "__main__":
    new_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(new_loop)
    new_loop.run_until_complete(main())
    # asyncio.run(main())
    
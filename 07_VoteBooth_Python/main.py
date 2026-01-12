import asyncio
from common import utils, account_config
from python_scripts.cadence_scripts import ScriptRunner
from python_scripts.cadence_transactions import TransactionRunner
from python_scripts.event_management import EventRunner
from python_scripts.election_management import Election
from python_scripts import contract_management, set_cadence_environment
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

# TODO: Implement the Ballot revoke mechanics by processing Ballots set with "default" as the option
# TODO: Modify project/contracts to allow multiple votes per account (add entropy to the index string to submit to the Election resource) to allow 
# bulk submissions of ballots and test this project for bottlenecks. Otherwise I need to create a new account per new vote, which is not ideal.

election_names: list[str] = [
    "A. Bullfights",
    "B. Coconut Cake",
    "C. Basketball"
]

election_ballots: list[str] = [
    "A. How should Portugal deal with its bullfighting arenas?",
    "B. What is the best frosting for coconut cake?",
    "C. Which NBA team is going to win the 2025-25 championship?"
]

election_options: list[dict[int: str]] = [
    {
        1: "Burn them to the ground",
        2: "Bomb them from afar using military artillery",
        3: "Refit them into urban landfills",
        4: "Rebuild them as public spaces, as malls, gyms, theatres, etc.",
        5: "Rebuild them as free public veterinarian clinics and force bullfights to maintain them for free."
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

async def main(election_index: int = 0) -> None:
    """
    Main entry point for this project
    """

    current_election: Election = Election()
    ctx = account_config.AccountConfig()

    new_election: bool = True
    # Set this flag to test the election with all the costs being paid by the service account
    free_election: bool = True

    # 0. Setup the project contracts
    if(False):
        print(f"0.1 Accounts before contract deployment ")
        await script_runner.profile_all_accounts(program_stage="pre contract deployment")

        log.info("Rebuilding project contracts...")
        await contract_management.main(op="clear")

        log.info("Re-deploying project contracts...")
        await contract_management.main(op="deploy")
        # log.info("Done!")

        print(f"0.2 Accounts after contract deployment ")
        await script_runner.profile_all_accounts(program_stage="post contract deployment")


    # 0.1. Fund all test accounts
    if (False):
        amount: float = 10.4
        recipients: list[str] = []

        for user_account in ctx.accounts:
            recipients.append(user_account["address"].hex())

        await tx_runner.fundAllAccounts(amount=amount, recipients=recipients, tx_signer_address=ctx.service_account["address"].hex())

    # 1. Setup an election with the data from the config file
    if (False):
        if (new_election):

            # current_election.election_id = 241892558110722
            # current_election.election_public_encryption_key = open(election_public_encryption_keys[election_index]).read()

            await current_election.create_election(
                new_election_name=election_names[election_index],
                new_election_ballot=election_ballots[election_index],
                new_election_options=election_options[election_index],
                new_election_public_key=open(election_public_encryption_keys[election_index]).read(),
                new_election_storage_path=election_storage_paths[election_index],
                new_election_public_path=election_public_paths[election_index],
                new_tx_signer_address=ctx.service_account["address"].hex()
            )
        else:
            current_active_elections: list[int] = await script_runner.getActiveElections()

            if (len(current_active_elections) > 1):
                log.warning(f"Multiple active elections found! Adopting the most recent one...")
            elif(len(current_active_elections) == 1):
                log.info(f"Loading Election {current_active_elections[0]} from the network...")
            else:
                raise Exception("Unable to load an active election from the network. There are no active elections left!")

            current_election.election_id = current_active_elections.pop()

            current_election.election_public_encryption_key = await script_runner.getPublicEncryptionKey(election_id=current_election.election_id)
        

        await script_runner.profile_all_accounts(program_stage="after election creation")

    # 1.1 Destroy the current election
    if (False):
        await current_election.destroy_election(tx_signer_address=ctx.service_account["address"].hex())

    # 2. Create a VoteBox into each of the user accounts inside a loop
    if (False):
        if (free_election):
            for user_account in ctx.accounts:
                await current_election.create_votebox(tx_signer_address=None, tx_proposer_address=user_account["address"].hex(), tx_payer_address=ctx.service_account["address"].hex(), tx_authorizer_address=[user_account["address"].hex()])
        else:
            for user_account in ctx.accounts:
                await current_election.create_votebox(tx_signer_address=user_account["address"].hex())

    # 2.1 Destroy the VoteBox from the transaction signer's account
    if (False):
        if (free_election):
            for user_account in ctx.accounts:
                await current_election.destroy_votebox(tx_signer_address=None, tx_proposer_address=user_account["address"].hex(), tx_payer_address=ctx.service_account["address"].hex(), tx_authorizer_address=[user_account["address"].hex()])
        else:
            for user_account in ctx.accounts:
                await current_election.destroy_votebox(tx_signer_address=user_account["address"].hex())


    # 3. Mint a blank Ballot into the account provided, for the election in question
    if (False):
        for user_account in ctx.accounts:
            await current_election.mint_ballot_to_votebox(votebox_address=user_account["address"].hex(), tx_signer_address=ctx.service_account["address"].hex())
    
    # 4. Cast the ballots for each of the user accounts to a random option from within the ones available for the election
    if (False):
        for user_account in ctx.accounts:
            random_index: int = random.randint(a=1, b=len(election_options[election_index]))
            random_option: dict[int:str] = election_options[election_index][random_index]
            
            if (free_election):
                receipt: int = await current_election.cast_ballot(option_to_set=random_option, tx_signer_address=None, tx_proposer_address=user_account["address"].hex(), tx_payer_address=ctx.service_account["address"].hex(), tx_authorizer_address=[user_account["address"].hex()])
            else:
                # Cast the ballot and save the int ballot receipt returned
                receipt: int = await current_election.cast_ballot(option_to_set=random_option, tx_signer_address=user_account["address"].hex())
            
            # Set the ballot receipt received to the user account object
            ctx.addReceipt(voter_address=user_account["address"].hex(),election_id=current_election.election_id, ballot_receipt=receipt)

            log.info(f"Voter {user_account["address"].hex()} ballot receipt for election {current_election.election_id} is '{receipt}'")
        

    # 5. Submit the cast ballots to the election
    if (False):
        if (free_election):
            for user_account in ctx.accounts:
                await current_election.submit_ballot(tx_signer_address=None, tx_proposer_address=user_account["address"].hex(), tx_payer_address=ctx.service_account["address"].hex(), tx_authorizer_address=[user_account["address"].hex()])
        else:
            for user_account in ctx.accounts:
                await current_election.submit_ballot(tx_signer_address=user_account["address"].hex())

    # 5.1 Do the creating, casting, and submitting of ballots in one single configurable cycle. This one does the combined stuff from steps 3, 4, and 5 before.
    if (False):
        rounds: int = 20

        while (rounds > 0):
            log.info(f"ROUND #{rounds}")
            # Create Ballots
            for user_account in ctx.accounts:
                await current_election.mint_ballot_to_votebox(votebox_address=user_account["address"].hex(), tx_signer_address=ctx.service_account["address"].hex())

            await script_runner.profile_all_accounts(program_stage="5.1. Accounts after ballot creation")

            # Cast Ballots
            for user_account in ctx.accounts:
                random_index: int = random.randint(a=1, b=len(election_options[election_index]))
                random_option: dict[int:str] = election_options[election_index][random_index]
                
                if (free_election):
                    # Cast the ballot and let the service account pay for it
                    receipt: int = await current_election.cast_ballot(option_to_set=random_option, tx_signer_address=None, tx_proposer_address=user_account["address"].hex(), tx_payer_address=ctx.service_account["address"].hex(), tx_authorizer_address=[user_account["address"].hex()])
                else:
                    # Cast the ballot and save the int ballot receipt returned
                    receipt: int = await current_election.cast_ballot(option_to_set=random_option, tx_signer_address=user_account["address"].hex())
                
                # Set the ballot receipt received to the user account object
                ctx.addReceipt(voter_address=user_account["address"].hex(),election_id=current_election.election_id, ballot_receipt=receipt)

                log.info(f"Voter {user_account["address"].hex()} ballot receipt for election {current_election.election_id} is '{receipt}'")
            
            await script_runner.profile_all_accounts(program_stage="5.2. Accounts after casting ballots")

            # Submit Ballots
            for user_account in ctx.accounts:
                if (free_election):
                    await current_election.submit_ballot(tx_signer_address=None, tx_proposer_address=user_account["address"].hex(), tx_payer_address=ctx.service_account["address"].hex(), tx_authorizer_address=[user_account["address"].hex()])
                else:
                    await current_election.submit_ballot(tx_signer_address=user_account["address"].hex())

            await script_runner.profile_all_accounts(program_stage="5.3. Accounts after submitting ballots")
                
            rounds -= 1


    # 6. Mint another round of Ballots to the user accounts, cast them again using a random option, and re-submit them to trigger the BallotReplaced event
    if (False):
        # Mint a new round of Ballots
        for user_account in ctx.accounts:
            await current_election.mint_ballot_to_votebox(votebox_address=user_account["address"].hex(), tx_signer_address=ctx.service_account["address"].hex())

        # Cast the randomly as well
        for user_account in ctx.accounts:
            random_index: int = random.randint(a=1, b=len(election_options[election_index]))
            random_option: str = election_options[election_index][random_index]

            if (free_election):
                # Cast the ballot and let the service account pay for it
                receipt: int = await current_election.cast_ballot(option_to_set=random_option, tx_signer_address=None, tx_proposer_address=user_account["address"].hex(), tx_payer_address=ctx.service_account["address"].hex(), tx_authorizer_address=[user_account["address"].hex()])
            else:
                # Cast the ballot and save the int ballot receipt returned
                receipt: int = await current_election.cast_ballot(option_to_set=random_option, tx_signer_address=user_account["address"].hex())
            
            ctx.addReceipt(voter_address=user_account["address"].hex(), election_id=current_election.election_id, ballot_receipt=receipt)

            log.info(f"Voter {user_account["address"].hex()} new ballot receipt for election {current_election.election_id} is '{receipt}'")

        # Submit the new round of ballots and test that the BallotReplaced event was triggered
        for user_account in ctx.accounts:
            await current_election.submit_ballot(tx_signer_address=user_account["address"].hex())

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
            "16_is_election_finished": True,
            "17_get_account_balance": True,
            "18_get_election_winner": True
        }

        # selected_user: int = 1
        # temp_election_id: int = 178120883699712
        # temp_election_id: int = current_election_id
        # votebox_address = ctx.accounts[0]["address"].hex()
        votebox_address = None

        # 02_get_active_elections
        if (scripts_to_run["02_get_active_elections"]):
            await current_election.get_active_elections(votebox_address=votebox_address)


        # 17_get_account_balance
        if (scripts_to_run["17_get_account_balance"]):
            for user_account in ctx.accounts:
                await current_election.get_account_balance(account_address=user_account["address"].hex())


        # 03_get_election_name
        if (scripts_to_run["03_get_election_name"]):
            await current_election.get_election_name(votebox_address=votebox_address)


        # 04_get_election_ballot
        if (scripts_to_run["04_get_election_ballot"]):
            await current_election.get_election_ballot(votebox_address=votebox_address)            
        

        # 05_get_election_options
        if (scripts_to_run["05_get_election_options"]):
            await current_election.get_election_options(votebox_address=votebox_address)


        # 06_get_election_id
        if (scripts_to_run["06_get_election_id"]):
            await current_election.get_election_id(votebox_address=votebox_address)        


        # 07_get_public_encryption_key
        if (scripts_to_run["07_get_public_encryption_key"]):
            await current_election.get_election_public_encryption_key(votebox_address=votebox_address)
        

        # 08_get_election_capability
        if (scripts_to_run["08_get_election_capability"]):
            await current_election.get_election_capability(votebox_address=votebox_address)


        # 09_get_election_totals
        if (scripts_to_run["09_get_election_totals"]):
            await current_election.get_election_totals(votebox_address=votebox_address)


        # 10_get_election_storage_path
        if (scripts_to_run["10_get_election_storage_path"]):
            await current_election.get_election_storage_path()


        # 11_get_election_public_path
        if (scripts_to_run["11_get_election_public_path"]):
            await current_election.get_election_public_path()

        
        # 12_get_election_list
        if (scripts_to_run["12_get_elections_list"]):
            await current_election.get_elections_list()


        # 13_get_ballot_option
        if (scripts_to_run["13_get_ballot_option"]):
            # Run this for every user_account
            for user_account in ctx.accounts:
                await current_election.get_ballot_option(votebox_address=user_account["address"].hex())
        

        # 14_get_ballot_id
        if (scripts_to_run["14_get_ballot_id"]):
            for user_account in ctx.accounts:
                await current_election.get_ballot_id(votebox_address=user_account["address"].hex())

        # 15_get_election_results
        if (scripts_to_run["15_get_election_results"]):
            await current_election.get_election_results()


        # 16_is_election_finished
        if (scripts_to_run["16_is_election_finished"]):
            await current_election.is_election_finished()
            

        # 18_get_election_winner
        if (scripts_to_run["18_get_election_winner"]):
            await current_election.get_election_winner()

    # 8. Withdraw ballots and compute tally
    if (False):
        await script_runner.profile_all_accounts(program_stage="8.1. Accounts before tallying the election")

        election_results = await current_election.tally_election(private_encryption_key_name=election_private_encryption_keys_filenames[election_index], tx_signer_address=ctx.service_account["address"].hex())

        log.info(f"Election {current_election.election_id} results: ")
        for result in election_results:
            log.info(f"Option '{result}': {election_results[result]} votes")

        await script_runner.profile_all_accounts(program_stage="8.2. Accounts before finishing the election")
        
        # Set the election results to the election to finish it properly first
        await current_election.finish_election(tx_signer_address=ctx.service_account["address"].hex())

        await script_runner.profile_all_accounts(program_stage="8.3. Accounts  after finishing the election")
        
        for user_account in ctx.accounts:
            for election_id in user_account["receipts"]:
                for receipt in user_account["receipts"][election_id]:
                    receipt_status: bool = await script_runner.isBallotReceiptValid(election_id=current_election.election_id, ballot_receipt=receipt)
                    if (receipt_status):
                        log.info(f"Ballot with receipt {receipt} from voter {user_account["address"].hex()} is valid!")
                    else:
                        log.warning(f"WARNING: Ballot with receipt {receipt} from voter {user_account["address"].hex()} is not among the ballot receipt list returned!")
        
    
    # 9. Check that the election is tallied but not yet finished
    if (False):
        election_finished: bool = await script_runner.isElectionFinished(election_id=current_election.election_id)

        if (election_finished):
            log.warning(f"WARNING: Election {current_election.election_id} has been tallied but is not yet finished!")
        else:
            log.info(f"Election {current_election.election_id} is awaiting finish!")

    # 10. Finish the election 
    if (False):
        await current_election.finish_election(tx_signer_address=ctx.service_account["address"].hex())

    # 11. Clean up project from network
    if (False):
        # Destroy the VoteBoxes in each of the user accounts
        for user_account in ctx.accounts:
            await current_election.deleteVoteBox(tx_signer_address=user_account["address"].hex())

        # Destroy the resources from the VoteBooth contract
        await current_election.deleteVoteBooth(tx_signer_address=ctx.service_account["address"].hex())


    
if __name__ == "__main__":
    new_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(new_loop)
    new_loop.run_until_complete(main(election_index=2))
    # asyncio.run(main())
    
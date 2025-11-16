import os, pathlib
from python_scripts.cadence_scripts import ScriptRunner
from python_scripts.cadence_transactions import TransactionRunner
from python_scripts.event_management import EventRunner
from python_scripts import contract_management
from common import utils, account_config
import configparser
import random


import logging
log = logging.getLogger(__name__)
utils.configureLogging()

config = configparser.ConfigParser()
config.read(pathlib.Path(os.getcwd()).joinpath("common", "config.ini"))

class Election(object):
    def __init__(self) -> None:
        super().__init__()

        self.election_id: int = None
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
            new_tx_signer_address: str
        ) -> None:
        """Function to create a new Election into this class, if none is set so far. This class admits one and only one election per class instance. If the class's self.election_id is not None, this function fails to prevent it from replacing an active election.

        @param election_name: str - The name of the election
        @param election_ballot: str - The ballot for the election
        @param election_options: dict[int:str] - The set of valid options to set in the election.
        @param election_public_key: str - The public encryption key to be associated with the election
        @param election_storage_path: str - A UNIX-type path to indicate the storage path where the election resource is to be stored.
        @param election_public_path: str - A UNIX-type path to indicate the public path where the public capability for this election is to be stored to.
        @param tx_signer_address: str - The address for the account that can sign the transaction to create this election.
        """
        # Only one active election per class is allowed 
        if (self.election_id != None):
            raise Exception(f"ERROR: This object already has an active election with id {self.election_id}")
        
        log.info(f"Creating a new election for {new_election_name}...")

        election_created_events: list[dict] = await self.tx_runner.createElection(
            election_name=new_election_name,
            election_ballot=new_election_ballot,
            election_options=new_election_options,
            election_public_key=new_election_public_key,
            election_storage_path=new_election_storage_path,
            election_public_path=new_election_public_path,
            tx_signer_address=new_tx_signer_address
        )

        for election_created_event in election_created_events:
            log.info(f"Successfully created Election with id {election_created_event["election_id"]} and name '{election_created_event["election_name"]}'")
        
        self.election_id = election_created_event["election_id"]
    

    async def destroy_election(self, tx_signer_address: str) -> None:
        """Function to destroy the election currently associated to this class. This function fails if the self.election_id parameter for this class is still None.
        """
        if (self.election_id == None):
            raise Exception("ERROR: Election no longer exists!")
        
        log.info(f"Destroying election {self.election_id}...")
        
        election_destroyed_events: list[dict[str:int]] = await self.tx_runner.deleteElection(
            election_id=self.election_id,
            tx_signer_address=tx_signer_address
        )
        
        election_id_destroyed: int = self.election_id

        for election_destroyed_event in election_destroyed_events:
            log.info(f"Successfully destroyed Election with id {election_destroyed_event["election_id"]}. It had {election_destroyed_event["ballots_stored"]} ballots in it")
        
        # Election destroyed. Set the internal election_id to None and return the old value back
        self.election_id = None
    

    async def create_votebox(self, tx_signer_address) -> None:
        """Function to create a new VoteBox resource in the tx_signer_address account provided.

        @param tx_signer_address: str The account address to use to digitally sign the transaction.
        """
        log.info(f"Creating a new VoteBox for account {tx_signer_address}")
        
        votebox_created_events: list[dict[str:str]] = await self.tx_runner.createVoteBox(tx_signer_address=tx_signer_address)

        for votebox_created_event in votebox_created_events:
            log.info(f"Successfully created a VoteBox for account {votebox_created_event["voter_address"]}")

    
    async def destroy_votebox(self, tx_signer_address) -> None:
        """Function to destroy a VoteBox resource from the account in the tx_signer_address account provided.

        @param tx_signer_address: str The account address to use to digitally sign the transaction.
        """
        log.info(f"Destroying ")
        votebox_destroyed_events: list[dict] = await self.tx_runner.deleteVoteBox(tx_signer_address=tx_signer_address)
        
        for votebox_destroyed_event in votebox_destroyed_events:
            log.info(f"Successfully deleted a VoteBox for account {votebox_destroyed_event["voter_address"]}, with {votebox_destroyed_event["active_ballots"]} active ballots still in it. This VoteBox was used to vote in {len(votebox_destroyed_event["elections_voted"])} elections:")
        
            index: int = 0
            for active_election_id in votebox_destroyed_event["elections_voted"]:
                log.info(f"Election #{index}: {active_election_id}")
                index += 1

    
    async def mint_ballot_to_votebox(self, votebox_address: str, tx_signer_address: str) -> None:
        """Function to mint a new Ballot for the VoteBox resource in the account with the address provided as tx_signer_address. If the Election class in question does not have an active election in it, this function raises an Exception.

        @param votebox_address: str The account address to where the new Ballot is to be deposited to. This account should have a VoteBox resource already configured in it.
        @param tx_signer_address: str The account address to use to digitally sign the transaction.
        """
        if (self.election_id == None):
            raise Exception(f"ERROR: This Election class does not have an active election in it!")
        
        try:
            ballot_created_events: list[dict[str:int]] = await self.tx_runner.createBallot(election_id=self.election_id, recipient_address=votebox_address, tx_signer_address=tx_signer_address)

            for ballot_created_event in ballot_created_events:
                log.info(f"Successfully created Ballot with id {ballot_created_event["ballot_id"]} attached to Election {ballot_created_event["linked_election_id"]} for account {votebox_address}")
        except Exception as e:
            log.error(f"Unable to create a new Ballot to {votebox_address}: ")
            log.error(e)


    
from flow_py_sdk import(
    flow_client,
    ProposalKey,
    Tx, 
    cadence,
    entities
)

import configparser
import sys
import os
import pathlib
import asyncio

from common import utils, account_config
from python_scripts import cadence_scripts

import logging
log = logging.getLogger(__name__)
utils.configureLogging()


class EventRunner():
    def __init__(self) -> None:
        super().__init__()

        project_cwd = pathlib.Path(os.getcwd())
        config_path = project_cwd.joinpath("common", "config.ini")
        self.config = configparser.ConfigParser()
        self.config.read(config_path)

        self.ctx = account_config.AccountConfig()

        self.script_runner = cadence_scripts.ScriptRunner()

        # Set the project deployer address to None for now
        self.deployer_address: str = None
        self.flow_fees_deployer_address: str = None
        self.flow_token_deployer_address: str = None
        self.fungible_token_deployer_address: str = None

        
    def configureDeployerAddress(self) -> None:
        """Internal function to retrieve and set the address of the account where the project contracts are currently deployed.
        """
        # Check which one is the currently configured network and add the addresses for the FlowToken and Fungible and NonFungibleToken and FlowFees contract,
        # given that these contracts are often deployed in a different account than the service one
        current_network: str = self.config.get(section="network", option="current")
        self.flow_fees_deployer_address = self.config.get(section=current_network, option="FlowFees")
        self.flow_token_deployer_address = self.config.get(section=current_network, option="FlowToken")
        self.fungible_token_deployer_address = self.config.get(section=current_network, option="FungibleToken")
        self.deployer_address = self.config.get(section=current_network, option="service_account")


    async def getEventsByName(self, event_name: str, event_num: int) -> list[cadence.Event]:
        """Function to retrieve a list with the latest-n  events with the name provided as input from the event queue.

        @param event_name: str - The name of the events to retrieve from the queue.
        @param event_num: int - The number of event of the given name to return.

        @return list Returns a list with the even_num-most recent events with event_name from the networks's event queue. 
        """
        async with flow_client(
            host=self.ctx.access_node_host, port=self.ctx.access_node_port
        ) as client:
            
            latest_block = await client.get_latest_block()

            # Grab all the events of the type indicated for the latest block only. I'm doing an "efficient" search in which I look for the event immediately
            # after running the transaction that emits them.
            # TODO: I'm seriously doubtful this works in a livenet such as testnet. I need to either:
            # 1. Search for a longer string of blocks, i.e., start_height > end_height
            # 2. Find the block id at which the transaction was sealed into and run the client.get_events_for_block_id_s

            events = await client.get_events_for_height_range(
                type=event_name,
                start_height=latest_block.height,
                end_height=latest_block.height
            )

            events_to_return: list[cadence.Event] = []

            for i in range(0, event_num, 1):
                if (len(events[0].events) > 0):
                    events_to_return.append(events[0].events[i])
            
            return events_to_return
    

    async def getBallotCreatedEvents(self, tx_response: entities.TransactionResultResponse) -> dict[str:int]:
        """Function to return the latest event_num BallotCreated events from the event queue

        @param tx_response: entities.TransactionResultResponse - The transaction result object as returned as the result of the transaction whose events are to be retrieved from.

        @return dict[str:int] Returns the event parameters in the format
        {
            "ballot_id": int,
            "linked_election_id": int
        }
        """
        event_name: str = "A." + self.deployer_address + ".BallotStandard.BallotCreated"

        ballot_created_events: list[dict[str:int]] = []

        for event in tx_response.events:
            if (event.type == event_name):
                ballot_created_event: dict = {}
                ballot_created_event["ballot_id"] = event.value.fields["_ballotId"].value
                ballot_created_event["linked_election_id"] = event.value.fields["_linkedElectionId"].value

                ballot_created_events.append(ballot_created_event)
        
        return ballot_created_events


    async def getBallotBurnedEvents(self, tx_response: entities.TransactionResultResponse) -> dict[str:int]:
        """Function to return the latest event_num BallotBurned events from the event queue

        @param tx_response: entities.TransactionResultResponse - The transaction result object as returned as the result of the transaction whose events are to be retrieved from.

        @return dict[str:int] Returns the event parameters in the format
        {
            "ballot_id": int,
            "linked_election_id: int
        }
        """
        event_name: str = "A." + self.deployer_address + ".BallotStandard.BallotBurned"

        ballot_burned_events: list[dict[str:int]] = []

        for event in tx_response.events:
            if (event.type == event_name):
                ballot_burned_event: dict = {}
                ballot_burned_event["ballot_id"] = event.value.fields["_ballotId"].value
                ballot_burned_event["linked_election_id"] = event.value.fields["_linkedElectionId"].value

                ballot_burned_events.append(ballot_burned_event)
        
        return ballot_burned_events


    async def getBallotSubmittedEvents(self, tx_response: entities.TransactionResultResponse) -> dict[str:int]:
        """Function to return the latest event_num BallotSubmitted events from the event queue

        @param tx_response: entities.TransactionResultResponse - The transaction result object as returned as the result of the transaction whose events are to be retrieved from.

        @return dict[str:int] Returns the event parameters in the format
        {
            "ballot_id": int,
            "election_id": int
        }
        """
        event_name: str = "A." + self.deployer_address + ".ElectionStandard.BallotSubmitted"

        ballot_submitted_events: list[dict[str:int]] = []

        for event in tx_response.events:
            if (event.type == event_name):
                ballot_submitted_event: dict = {}
                ballot_submitted_event["ballot_id"] = event.value.fields["_ballotId"].value
                ballot_submitted_event["election_id"] = event.value.fields["_electionId"].value

                ballot_submitted_events.append(ballot_submitted_event)

        return ballot_submitted_events

    
    async def getBallotReplacedEvents(self, tx_response: entities.TransactionResultResponse) -> dict[str:int]:
        """Function to return the latest event_num BallotReplaced events from the event queue.

        @param tx_response: entities.TransactionResultResponse - The transaction result object as returned as the result of the transaction whose events are to be retrieved from.

        @return dict[str:int] Returns the event parameters in the format
        {
            "old_ballot_id": int,
            "new_ballot_id": int,
            "election_id": int
        }
        """
        event_name: str = "A." + self.deployer_address + ".ElectionStandard.BallotReplaced"

        ballot_replaced_events: list[dict[str:int]] = []

        for event in tx_response.events:
            if (event.type == event_name):
                ballot_replaced_event: dict = {}
                ballot_replaced_event["old_ballot_id"] = event.value.fields["_oldBallotId"].value
                ballot_replaced_event["new_ballot_id"] = event.value.fields["_newBallotId"].value
                ballot_replaced_event["election_id"] = event.value.fields["_electionId"].value

                ballot_replaced_events.append(ballot_replaced_event)
        
        return ballot_replaced_events

    
    async def getBallotRevokedEvents(self, tx_response: entities.TransactionResultResponse) -> dict[str:int]:
        """Function to return the latest event_num BallotRevoked events from the event queue.

        @tx_response TransactionResultResponse - The transaction result object as returned as the result of the transaction whose events are to be retrieved from.

        @return dict[str:int] Returns the event parameters in the format
        {
            "ballot_id": int,
            "election_id": int
        }
        """
        event_name: str = "A." + self.deployer_address + ".ElectionStandard.BallotRevoked"

        ballot_revoked_events: list[dict[str:int]] = []

        for event in tx_response.events:
            if (event.type == event_name):
                ballot_revoked_event: dict = {}
                ballot_revoked_event["ballot_id"] = event.value.fields["_ballotId"].value
                ballot_revoked_event["election_id"] = event.value.fields["_electionId"].value

                ballot_revoked_events.append(ballot_revoked_event)
        
        return ballot_revoked_events

    
    async def getBallotsWithdrawnEvents(self, tx_response: entities.TransactionResultResponse) -> dict[str: int]:
        """Function to return the latest event_num BallotsWithdrawn events from the event queue.

        @tx_response TransactionResultResponse - The transaction result object as returned as the result of the transaction whose events are to be retrieved from.

        @return dict[str:int] Returns the event parameters in the format
        {
            "ballots_withdrawn": int,
            "election_id": int
        }
        """
        event_name: str = "A." + self.deployer_address + ".ElectionStandard.BallotsWithdrawn"

        ballots_withdrawn_events: list[dict[str:int]] = []

        for event in tx_response.events:
            if (event.type == event_name):
                ballot_withdrawn_event: dict = {}
                ballot_withdrawn_event["ballots_withdrawn"] = event.value.fields["_ballotsWithdrawn"].value
                ballot_withdrawn_event["election_id"] = event.value.fields["_electionId"].value

                ballots_withdrawn_events.append(ballot_withdrawn_event)

        return ballots_withdrawn_events

    
    async def getElectionCreatedEvents(self, tx_response: entities.TransactionResultResponse) -> dict:
        """Function to return the latest event_num ElectionCreated events from the event queue.

        @tx_response TransactionResultResponse - The transaction result object as returned as the result of the transaction whose events are to be retrieved from.

        @return dict Returns the event parameters in the format
        {
            "election_id": int,
            "election_name": str
        }
        """
        event_name: str = "A." + self.deployer_address + ".ElectionStandard.ElectionCreated"

        election_created_events: list[dict] = []
        # Extract all events with the same name as the one defined
        for event in tx_response.events:
            if (event.type == event_name):
                election_created_event: dict = {}
                election_created_event["election_id"] = event.value.fields["_electionId"].value
                election_created_event["election_name"] = event.value.fields["_electionName"].value

                election_created_events.append(election_created_event)

        return election_created_events


    async def getElectionDestroyedEvents(self, tx_response: entities.TransactionResultResponse) -> dict[str:int]:
        """Function to return the latest event_num ElectionDestroyed events from the event queue.

        @param tx_response: entities.TransactionResultResponse - The transaction result object as returned as the result of the transaction whose events are to be retrieved from.

        @return dict[str:int] Returns the event parameters in the format
        {
            "election_id": int,
            "ballots_stored": int
        }
        """
        event_name: str = "A." + self.deployer_address + ".ElectionStandard.ElectionDestroyed"
        election_destroyed_events: list[dict] = []

        for event in tx_response.events:
            if (event.type == event_name):
                election_destroyed_event: dict = {}
                election_destroyed_event["election_id"] = event.value.fields["_electionId"].value
                election_destroyed_event["ballots_stored"] = event.value.fields["_ballotsStored"].value

                election_destroyed_events.append(election_destroyed_event)
        
        return election_destroyed_events

    
    async def getNonNilResourceReturnedEvents(self, tx_response: entities.TransactionResultResponse) -> dict[str:str]:
        """Function to return the latest event_num NonNilResourceReturned events from the event queue.

        @param tx_response: entities.TransactionResultResponse - The transaction result object as returned as the result of the transaction whose events are to be retrieved from.

        @return dict[str:str] Returns the event parameters in the format
        {
            "resource_type": str
        }
        """
        event_name: str = "A." + self.deployer_address + ".ElectionStandard.NonNilResourceReturned"

        non_nil_resource_returned_events: list[dict[str:str]] = []

        for event in tx_response.events:
            if (event.type == event_name):
                non_nil_resource_returned_event: dict = {}
                non_nil_resource_returned_event["resource_type"] = event.value.fields["_resourceType"].value

                non_nil_resource_returned_events.append(non_nil_resource_returned_event)
        
        return non_nil_resource_returned_events

    
    async def getVoteBoxCreatedEvents(self, tx_response: entities.TransactionResultResponse) -> dict[str:str]:
        """Function to return the latest event_num VoteBoxCreated events from the event queue.

        @param tx_response: entities.TransactionResultResponse - The transaction result object as returned as the result of the transaction whose events are to be retrieved from.

        @return dict[str:str] Returns the event parameters in the format
        {
            "voter_address": str
        }
        """
        event_name: str = "A." + self.deployer_address + ".VoteBoxStandard.VoteBoxCreated"

        votebox_created_events: list[dict[str:str]] = []

        for event in tx_response.events:
            if (event.type == event_name):
                votebox_created_event: dict[str:str] = {}
                votebox_created_event["voter_address"] = event.value.fields["_voterAddress"].hex()

                votebox_created_events.append(votebox_created_event)

        return votebox_created_events

    
    async def getVoteBoxBurnedEvents(self, tx_response: entities.TransactionResultResponse) -> dict:
        """Function to return the latest event_num VoteBoxBurned events from the event queue.

        @param tx_response: entities.TransactionResultResponse - The transaction result object as returned as the result of the transaction whose events are to be retrieved from.

        @return dict Returns the event parameters in the format
        {
            "elections_voted": list[int],
            "active_ballots": int,
            "voter_address": str
        }
        """
        event_name: str = "A." + self.deployer_address + ".VoteBoxStandard.VoteBoxBurned"

        votebox_destroyed_events: list[dict] = []

        for event in tx_response.events:
            if (event.type == event_name):
                votebox_destroyed_event: dict = {}
                votebox_destroyed_event["active_ballots"] = event.value.fields["_activeBallots"].value
                votebox_destroyed_event["voter_address"] = event.value.fields["_voterAddress"].hex()
                # The election_voted property is an [int], so it needs special processing
                votebox_destroyed_event["elections_voted"] = []
                for active_ballot in event.value.fields["_electionsVoted"].value:
                    votebox_destroyed_event["elections_voted"].append(active_ballot.value)

                votebox_destroyed_events.append(votebox_destroyed_event)
        
        return votebox_destroyed_events

    
    async def getElectionIndexCreatedEvents(self, tx_response: entities.TransactionResultResponse) -> dict[str:str]:
        """Function to return the latest event_num ElectionIndexCreated events from the event queue.

        @param tx_response: entities.TransactionResultResponse - The transaction result object as returned as the result of the transaction whose events are to be retrieved from.

        @return dict[str:str] Returns the event parameters in the format
        {
            "account_address": str
        }
        """
        event_name: str = "A." + self.deployer_address + ".VoteBooth.ElectionIndexCreated"

        election_index_created_events: list[dict[str:str]] = []

        for event in tx_response.events:
            if (event.type == event_name):
                election_index_created_event: dict[str:str] = {}
                election_index_created_event["account_address"] = event.value.fields["_accountAddress"].hex()

                election_index_created_events.append(election_index_created_event)

        return election_index_created_events

    
    async def getElectionIndexDestroyedEvents(self, tx_response: entities.TransactionResultResponse) -> dict[str:str]:
        """Function to return the latest event_num ElectionIndexDestroyed events from the event queue.

        @param tx_response: entities.TransactionResultResponse - The transaction result object as returned as the result of the transaction whose events are to be retrieved from.
        
        @return dict[str:str] Returns the event parameters in the format
        {
            "account_address": str
        }
        """
        event_name: str = "A." + self.deployer_address + ".VoteBooth.ElectionIndexDestroyed"

        election_index_destroyed_events: list[dict[str:str]] = []

        for event in tx_response.events:
            if (event.type == event_name):
                election_index_destroyed_event: dict[str:str] = {}
                election_index_destroyed_event["account_address"] = event.value.fields["_accountAddress"].hex()

                election_index_destroyed_events.append(election_index_destroyed_event)

        return election_index_destroyed_events

    
    async def getVoteBoothPrinterAdminCreatedEvents(self, tx_response: entities.TransactionResultResponse) -> dict[str:str]:
        """Function to return the latest event_num VoteBoothPrinterAdminCreated events from the event queue.

        @param tx_response: entities.TransactionResultResponse - The transaction result object as returned as the result of the transaction whose events are to be retrieved from.

        @return dict[str:str] Returns the event parameters in the format
        {
            "account_address": str
        }
        """
        event_name: str = "A." + self.deployer_address + ".VoteBooth.VoteBoothPrinterAdminCreated"

        votebooth_printer_admin_created_events: list[dict[str:str]] = []

        for event in tx_response.events:
            if (event.type == event_name):
                votebooth_printer_admin_created_event: dict[str:str] = {}
                votebooth_printer_admin_created_event["account_address"] = event.value.fields["_accountAddress"].hex()

                votebooth_printer_admin_created_events.append(votebooth_printer_admin_created_event)
        
        return votebooth_printer_admin_created_events


    async def getVoteBoothPrinterAdminDestroyedEvents(self, tx_response: entities.TransactionResultResponse) -> dict[str:str]:
        """Function to return the latest event_num VoteBoothPrinterAdminDestroyed events from the event queue.

        @param tx_response: entities.TransactionResultResponse - The transaction result object as returned as the result of the transaction whose events are to be retrieved from.

        @return dict[str:str] Returns the event parameters in the format
        {
            "account_address": str
        }
        """
        event_name: str = "A." + self.deployer_address + ".VoteBooth.VoteBoothPrinterAdminDestroyed"

        votebooth_printer_admin_destroyed_events: list[dict[str:str]] = []

        for event in tx_response.events:
            if (event.type == event_name):
                votebooth_printer_admin_destroyed_event: dict[str:str] = {}
                votebooth_printer_admin_destroyed_event["account_address"] = event.value.fields["_accountAddress"].hex()

                votebooth_printer_admin_destroyed_events.append(votebooth_printer_admin_destroyed_event)

        return votebooth_printer_admin_destroyed_events
    

    async def getTokensDepositedEvents(self, tx_response: entities.TransactionResultResponse) -> dict:
        """Function to return the latest event_num FlowToken.TokensDeposited events from the event queue.

        @param tx_response: entities.TransactionResultResponse - The transaction result object as returned as the result of the transaction whose events are to be retrieved from.
        
        @return dict Returns the event parameters in the format
        {
            "amount": float,
            "to": str
        }
        """
        event_name: str = "A." + self.flow_token_deployer_address + ".FlowToken.TokensDeposited"

        tokens_deposited_events: list[dict] = []

        for event in tx_response.events:
            if (event.type == event_name):
                tokens_deposited_event: dict = {}
                tokens_deposited_event["amount"] = event.value.fields["amount"].__str__()
                tokens_deposited_event["to"] = event.value.fields["to"].value.hex()

                tokens_deposited_events.append(tokens_deposited_event)

        return tokens_deposited_events
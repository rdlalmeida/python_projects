from flow_py_sdk import(
    flow_client,
    ProposalKey,
    Tx, 
    cadence
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

        
    async def configureDeployerAddress(self) -> None:
        """Internal function to retrieve and set the address of the account where the project contracts are currently deployed.
        """
        # Run the 01_test_contract_consistency script and store the result, if an address is returned. Raise an exception if the project was found inconsistent.
        self.deployer_address: str = await self.script_runner.testContractConsistency()

        if (self.deployer_address == ""):
            raise Exception("ERROR: The project is not consistent yet!")
        
        # Check which one is the currently configured network and add the addresses for the FlowToken and Fungible and NonFungibleToken and FlowFees contract,
        # given that these contracts are often deployed in a different account than the service one
        current_network: str = self.config.get(section="network", option="current")
        self.flow_fees_deployer_address = self.config.get(section=current_network, option="FlowFees")
        self.flow_token_deployer_address = self.config.get(section=current_network, option="FlowToken")
        self.fungible_token_deployer_address = self.config.get(section=current_network, option="FungibleToken")


    async def getEventsByName(self, event_name: str, event_num: int) -> list[cadence.Event]:
        """Function to retrieve a list with the latest-n  events with the name provided as input from the event queue.

        @param event_name: str - The name of the events to retrieve from the queue.
        @param event_num: int - The number of events with the name indicated to return. This function returns the last event_num events from the queue.

        @return list Returns a list with the even_num-most recent events with event_name from the networks's event queue. 
        """
        async with flow_client(
            host=self.ctx.access_node_host, port=self.ctx.access_node_port
        ) as client:
            
            latest_block = await client.get_latest_block()

            # Grab only the last 2 events of the type emitted. For now lets be efficient. I'm 
            events = await client.get_events_for_height_range(
                type=event_name,
                start_height=latest_block.height - 1,
                end_height=latest_block.height
            )

            events_to_return: list[cadence.Event] = []

            for i in range(len(events) - 1,(len(events) - 1 - event_num), -1):
                # Check if any events of the type in question were returned
                if (len(events[i].events) > 0):
                    events_to_return.append(events[i].events[0])
            
            return events_to_return
    

    async def getBallotCreatedEvents(self, event_num: int) -> dict[str:int]:
        """Function to return the latest event_num BallotCreated events from the event queue

        @param event_num: int - The number of events to return.

        @return dict[str:int] Returns the event parameters in the format
        {
            "ballot_id": int,
            "linked_election_id": int
        }
        """
        event_name: str = "A." + self.deployer_address + ".BallotStandard.BallotCreated"

        events: list[cadence.Event] = await self.getEventsByName(event_name=event_name, event_num=event_num)

        ballot_created_events: list[dict[str:int]] = []

        for event in events:
            ballot_created_event: dict = {}
            ballot_created_event["ballot_id"] = event.value.fields["_ballotId"].value
            ballot_created_event["linked_election_id"] = event.value.fields["_linkedElectionId"].value

            ballot_created_events.append(ballot_created_event)
        
        return ballot_created_events


    async def getBallotBurnedEvents(self, event_num: int) -> dict[str:int]:
        """Function to return the latest event_num BallotBurned events from the event queue

        @param event_num: int - The number of events to return.

        @return dict[str:int] Returns the event parameters in the format
        {
            "ballot_id": int,
            "linked_election_id: int
        }
        """
        event_name: str = "A." + self.deployer_address + ".BallotStandard.BallotBurned"
        events: list[cadence.Event] = await self.getEventsByName(event_name=event_name, event_num=event_num)

        ballot_burned_events: list[dict[str:int]] = []

        for event in events:
            ballot_burned_event: dict = {}
            ballot_burned_event["ballot_id"] = event.value.fields["_ballotId"].value
            ballot_burned_event["linked_election_id"] = event.value.fields["_linkedElectionId"].value

            ballot_burned_events.append(ballot_burned_event)
        
        return ballot_burned_events


    async def getBallotSubmittedEvents(self, event_num: int) -> dict[str:int]:
        """Function to return the latest event_num BallotSubmitted events from the event queue

        @param event_num: int - The number of events to return.

        @return dict[str:int] Returns the event parameters in the format
        {
            "ballot_id": int,
            "election_id": int
        }
        """
        event_name: str = "A." + self.deployer_address + ".ElectionStandard.BallotSubmitted"
        events: list[cadence.Event] = await self.getEventsByName(event_name=event_name, event_num=event_num)

        ballot_submitted_events: list[dict[str:int]] = []

        for event in events:
            ballot_submitted_event: dict = {}
            ballot_submitted_event["ballot_id"] = event.value.fields["_ballotId"].value
            ballot_submitted_event["election_id"] = event.value.fields["_electionId"].value

            ballot_submitted_events.append(ballot_submitted_event)

        return ballot_submitted_events

    
    async def getBallotReplacedEvents(self, event_num: int) -> dict[str:int]:
        """Function to return the latest event_num BallotReplaced events from the event queue.

        @param event_num: int - The number of events to return.

        @return dict[str:int] Returns the event parameters in the format
        {
            "old_ballot_id": int,
            "new_ballot_id": int,
            "election_id": int
        }
        """
        event_name: str = "A." + self.deployer_address + ".ElectionStandard.BallotReplaced"
        events: list[cadence.Event] = await self.getEventsByName(event_name=event_name, event_num=event_num)

        ballot_replaced_events: list[dict[str:int]] = []

        for event in events:
            ballot_replaced_event: dict = {}
            ballot_replaced_event["old_ballot_id"] = event.value.fields["_oldBallotId"].value
            ballot_replaced_event["new_ballot_id"] = event.value.fields["_newBallotId"].value
            ballot_replaced_event["election_id"] = event.value.fields["_electionId"].value

            ballot_replaced_events.append(ballot_replaced_event)
        
        return ballot_replaced_events

    
    async def getBallotRevokedEvents(self, event_num: int) -> dict[str:int]:
        """Function to return the latest event_num BallotRevoked events from the event queue.

        @param event_num: int - The number of events to return.

        @return dict[str:int] Returns the event parameters in the format
        {
            "ballot_id": int,
            "election_id": int
        }
        """
        event_name: str = "A." + self.deployer_address + ".ElectionStandard.BallotRevoked"
        events: list[dict[str:int]] = await self.getEventsByName(event_name=event_name, event_num=event_num)

        ballot_revoked_events: list[dict[str:int]] = []

        for event in events:
            ballot_revoked_event: dict = {}
            ballot_revoked_event["ballot_id"] = event.value.fields["_ballotId"].value
            ballot_revoked_event["election_id"] = event.value.fields["_electionId"].value

            ballot_revoked_events.append(ballot_revoked_event)
        
        return ballot_revoked_events

    
    async def getBallotsWithdrawnEvents(self, event_num: int) -> dict[str: int]:
        """Function to return the latest event_num BallotsWithdrawn events from the event queue.

        @param event_num: int - The number of events to return.

        @return dict[str:int] Returns the event parameters in the format
        {
            "ballots_withdrawn": int,
            "election_id": int
        }
        """
        event_name: str = "A." + self.deployer_address + ".ElectionStandard.BallotsWithdrawn"
        events: list[dict[str:int]] = await self.getEventsByName(event_name=event_name, event_num=event_num)

        ballots_withdrawn_events: list[dict[str:int]] = []

        for event in events:
            ballot_withdrawn_event: dict = {}
            ballot_withdrawn_event["ballots_withdrawn"] = event.value.fields["_ballotsWithdrawn"].value
            ballot_withdrawn_event["election_id"] = event.value.fields["_electionId"].value

            ballots_withdrawn_events.append(ballot_withdrawn_event)

        return ballots_withdrawn_events

    
    async def getElectionCreatedEvents(self, event_num: int) -> dict:
        """Function to return the latest event_num ElectionCreated events from the event queue.

        @param event_num: int - The number of events to return.

        @return dict Returns the event parameters in the format
        {
            "election_id": int,
            "election_name": str
        }
        """
        event_name: str = "A." + self.deployer_address + ".ElectionStandard.ElectionCreated"

        events: list[cadence.Event] = await self.getEventsByName(event_name=event_name, event_num=event_num)

        election_created_events: list[dict] = []

        for event in events:
            election_created_event: dict = {}
            election_created_event["election_id"] = event.value.fields["_electionId"].value
            election_created_event["election_name"] = event.value.fields["_electionName"].value

            election_created_events.append(election_created_event)

        return election_created_events


    async def getElectionDestroyedEvents(self, event_num: int) -> dict[str:int]:
        """Function to return the latest event_num ElectionDestroyed events from the event queue.

        @param event_num: int - The number of events to return.

        @return dict[str:int] Returns the event parameters in the format
        {
            "election_id": int,
            "ballots_stored": int
        }
        """
        event_name: str = "A." + self.deployer_address + ".ElectionStandard.ElectionDestroyed"

        events: list[cadence.Event] = await self.getEventsByName(event_name=event_name, event_num=event_num)

        election_destroyed_events: list[dict] = []

        for event in events:
            election_destroyed_event: dict = {}
            election_destroyed_event["election_id"] = event.value.fields["_electionId"].value
            election_destroyed_event["ballots_stored"] = event.value.fields["_ballotsStored"].value

            election_destroyed_events.append(election_destroyed_event)
        
        return election_destroyed_events

    
    async def getNonNilResourceReturnedEvents(self, event_num: int) -> dict[str:str]:
        """Function to return the latest event_num NonNilResourceReturned events from the event queue.

        @param event_num: int - The number of events to return.

        @return dict[str:str] Returns the event parameters in the format
        {
            "resource_type": str
        }
        """
        event_name: str = "A." + self.deployer_address + ".ElectionStandard.NonNilResourceReturned"
        events: list[cadence.Event] = await self.getEventsByName(event_name=event_name, event_num=event_num)

        non_nil_resource_returned_events: list[dict[str:str]] = []

        for event in events:
            non_nil_resource_returned_event: dict = {}
            non_nil_resource_returned_event["resource_type"] = event.value.fields["_resourceType"].value

            non_nil_resource_returned_events.append(non_nil_resource_returned_event)
        
        return non_nil_resource_returned_events

    
    async def getVoteBoxCreatedEvents(self, event_num: int) -> dict[str:str]:
        """Function to return the latest event_num VoteBoxCreated events from the event queue.

        @param event_num: int - The number of events to return.

        @return dict[str:str] Returns the event parameters in the format
        {
            "voter_address": str
        }
        """
        event_name: str = "A." + self.deployer_address + ".VoteBoxStandard.VoteBoxCreated"
        events: list[cadence.Event] = await self.getEventsByName(event_name=event_name, event_num=event_num)

        votebox_created_events: list[dict[str:str]] = []

        for event in events:
            votebox_created_event: dict[str:str] = {}
            votebox_created_event["voter_address"] = event.value.fields["_voterAddress"].hex()

            votebox_created_events.append(votebox_created_event)

        return votebox_created_events

    
    async def getVoteBoxDestroyedEvents(self, event_num: int) -> dict:
        """Function to return the latest event_num VoteBoxDestroyed events from the event queue.

        @param event_num: int - The number of events to return.

        @return dict Returns the event parameters in the format
        {
            "elections_voted": list[int],
            "active_ballots": int,
            "voter_address": str
        }
        """
        event_name: str = "A." + self.deployer_address + ".VoteBoxStandard.VoteBoxDestroyed"
        events: list[cadence.Event] = await self.getEventsByName(event_name=event_name, event_num=event_num)

        votebox_destroyed_events: list[dict] = []

        for event in events:
            votebox_destroyed_event: dict = {}
            votebox_destroyed_event["active_ballots"] = event.value.fields["_activeBallots"].value
            votebox_destroyed_event["voter_address"] = event.value.fields["_voterAddress"].hex()
            # The election_voted property is an [int], so it needs special processing
            votebox_destroyed_event["elections_voted"] = []
            for active_ballot in event.value.fields["_electionsVoted"].value:
                votebox_destroyed_event["elections_voted"].append(active_ballot.value)

            votebox_destroyed_events.append(votebox_destroyed_event)
        
        return votebox_destroyed_events

    
    async def getElectionIndexCreatedEvents(self, event_num: int) -> dict[str:str]:
        """Function to return the latest event_num ElectionIndexCreated events from the event queue.

        @param event_num: int - The number of events to return.

        @return dict[str:str] Returns the event parameters in the format
        {
            "account_address": str
        }
        """
        event_name: str = "A." + self.deployer_address + ".VoteBooth.ElectionIndexCreated"
        events: list[cadence.Event] = await self.getEventsByName(event_name=event_name, event_num=event_num)

        election_index_created_events: list[dict[str:str]] = []

        for event in events:
            election_index_created_event: dict[str:str] = {}
            election_index_created_event["account_address"] = event.value.fields["_accountAddress"].hex()

            election_index_created_events.append(election_index_created_event)

        return election_index_created_events

    
    async def getElectionIndexDestroyedEvents(self, event_num: int) -> dict[str:str]:
        """Function to return the latest event_num ElectionIndexDestroyed events from the event queue.

        @param event_num: int - The number of events to return.
        
        @return dict[str:str] Returns the event parameters in the format
        {
            "account_address": str
        }
        """
        event_name: str = "A." + self.deployer_address + ".VoteBooth.ElectionIndexDestroyed"
        events: list[cadence.Event] = await self.getEventsByName(event_name=event_name, event_num=event_num)

        election_index_destroyed_events: list[dict[str:str]] = []

        for event in events:
            election_index_destroyed_event: dict[str:str] = []
            election_index_destroyed_event["account_address"] = event.value.fields["_accountAddress"].hex()

            election_index_destroyed_events.append(election_index_destroyed_event)

        return election_index_destroyed_events

    
    async def getVoteBoothPrinterAdminCreatedEvents(self, event_num: int) -> dict[str:str]:
        """Function to return the latest event_num VoteBoothPrinterAdminCreated events from the event queue.

        @param event_num: int - The number of events to return.

        @return dict[str:str] Returns the event parameters in the format
        {
            "account_address": str
        }
        """
        event_name: str = "A." + self.deployer_address + ".VoteBooth.VoteBoothPrinterAdminCreated"
        events: list[cadence.Event] = await self.getEventsByName(event_name=event_name, event_num=event_num)

        votebooth_printer_admin_created_events: list[dict[str:str]] = []

        for event in events:
            votebooth_printer_admin_created_event: dict[str:str] = {}
            votebooth_printer_admin_created_event["account_address"] = event.value.fields["_accountAddress"].hex()

            votebooth_printer_admin_created_events.append(votebooth_printer_admin_created_event)
        
        return votebooth_printer_admin_created_events


    async def getVoteBoothPrinterAdminDestroyedEvents(self, event_num: int) -> dict[str:str]:
        """Function to return the latest event_num VoteBoothPrinterAdminDestroyed events from the event queue.

        @param event_num: int - The number of events to return.

        @return dict[str:str] Returns the event parameters in the format
        {
            "account_address": str
        }
        """
        event_name: str = "A." + self.deployer_address + ".VoteBooth.VoteBoothPrinterAdminDestroyed"
        events: list[cadence.Event] = await self.getEventsByName(event_name=event_name, event_num=event_num)

        votebooth_printer_admin_destroyed_events: list[dict[str:str]] = []

        for event in events:
            votebooth_printer_admin_destroyed_event: dict[str:str] = {}
            votebooth_printer_admin_destroyed_event["account_address"] = event.value.fields["_accountAddress"].hex()

            votebooth_printer_admin_destroyed_events.append(votebooth_printer_admin_destroyed_event)

        return votebooth_printer_admin_destroyed_events
    

    async def getTokensDepositedEvents(self, event_num: int) -> dict:
        """Function to return the latest event_num FlowToken.TokensDeposited events from the event queue.

        @param event_num: int - The number of events to return.
        
        @return dict Returns the event parameters in the format
        {
            "amount": float,
            "to": str
        }
        """
        # TODO: How to get the deployed address of the FlowToken contract?
        event_name: str = "A." + self.flow_token_deployer_address + ".FlowToken.TokensDeposited"
        events: list[cadence.Event] = await self.getEventsByName(event_name=event_name, event_num=event_num)

        tokens_deposited_events: list[dict] = []

        for event in events:
            tokens_deposited_event: dict = {}
            tokens_deposited_event["amount"] = event.value.fields["amount"].value
            tokens_deposited_event["to"] = event.value.fields["to"].from_hex()

            tokens_deposited_events.append(tokens_deposited_event)

        return tokens_deposited_events
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


    async def getBallotBurnedEvents(self, event_num: int) -> dict[str:int]:
        """Function to return the latest event_num BallotBurned events from the event queue

        @param event_num: int - The number of events to return.

        @return dict[str:int] Returns the event parameters in the format
        {
            "ballot_id": int,
            "linked_election_id: int
        }
        """


    async def getBallotSubmittedEvents(self, event_num: int) -> dict[str:int]:
        """Function to return the latest event_num BallotSubmitted events from the event queue

        @param event_num: int - The number of events to return.

        @return dict[str:int] Returns the event parameters in the format
        {
            "ballot_id": int,
            "election_id": int
        }
        """

    
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

    
    async def getBallotRevokedEvents(self, event_num: int) -> dict[str:int]:
        """Function to return the latest event_num BallotRevoked events from the event queue.

        @param event_num: int - The number of events to return.

        @return dict[str:int] Returns the event parameters in the format
        {
            "ballot_id": int,
            "election_id": int
        }
        """

    
    async def getBallotsWithdrawnEvents(self, event_num: int) -> dict[str: int]:
        """Function to return the latest event_num BallotsWithdrawn events from the event queue.

        @param event_num: int - The number of events to return.

        @return dict[str:int] Returns the event parameters in the format
        {
            "ballots_withdrawn": int,
            "election_id": int
        }
        """

    
    async def getElectionCreatedEvents(self, event_num: int) -> dict:
        """Function to return the latest event_num ElectionCreated events from the event queue.

        @param event_num: int - The number of events to return.

        @return dict Returns the event parameters in the format
        {
            "election_id": int,
            "election_name": str
        }
        """
        event_name: str = "A.f8d6e0586b0a20c7.ElectionStandard.ElectionCreated"

        events: list[cadence.Event] = await self.getEventsByName(event_name=event_name, event_num=event_num)

        election_created_events: list[dict] = []

        for event in events:
            current_event: dict = {}
            current_event["election_id"] = event.value.fields["_electionId"].value
            current_event["election_name"] = event.value.fields["_electionName"].value

            election_created_events.append(current_event)

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
        event_name: str = "A.f8d6e0586b0a20c7.ElectionStandard.ElectionDestroyed"

        events: list[cadence.Event] = await self.getEventsByName(event_name=event_name, event_num=event_num)

        election_destroyed_events: list[dict] = []

        for event in events:
            current_event: dict = {}
            current_event["election_id"] = event.value.fields["_electionId"].value
            current_event["ballots_stored"] = event.value.fields["_ballotsStored"].value

            election_destroyed_events.append(current_event)
        
        return election_destroyed_events

    
    async def getNonNilResourceReturnedEvents(self, event_num: int) -> dict[str:str]:
        """Function to return the latest event_num NonNilResourceReturned events from the event queue.

        @param event_num: int - The number of events to return.

        @return dict[str:str] Returns the event parameters in the format
        {
            "resource_type": str
        }
        """

    
    async def getVoteBoxCreatedEvents(self, event_num: int) -> dict[str:str]:
        """Function to return the latest event_num VoteBoxCreated events from the event queue.

        @param event_num: int - The number of events to return.

        @return dict[str:str] Returns the event parameters in the format
        {
            "voter_address": str
        }
        """

    
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

    
    async def getElectionIndexCreatedEvents(self, event_num: int) -> dict[str:str]:
        """Function to return the latest event_num ElectionIndexCreated events from the event queue.

        @param event_num: int - The number of events to return.

        @return dict[str:str] Returns the event parameters in the format
        {
            "account_address": str
        }
        """

    
    async def getElectionIndexDestroyedEvents(self, event_num: int) -> dict[str:str]:
        """Function to return the latest event_num ElectionIndexDestroyed events from the event queue.

        @param event_num: int - The number of events to return.
        
        @return dict[str:str] Returns the event parameters in the format
        {
            "account_address": str
        }
        """

    
    async def getVoteBoothPrinterAdminCreatedEvents(self, event_num: int) -> dict[str:str]:
        """Function to return the latest event_num VoteBoothPrinterAdminCreated events from the event queue.

        @param event_num: int - The number of events to return.

        @return dict[str:str] Returns the event parameters in the format
        {
            "account_address": str
        }
        """


    async def getVoteBoothPrinterAdminDestroyedEvents(self, event_num: int) -> dict[str:str]:
        """Function to return the latest event_num VoteBoothPrinterAdminDestroyed events from the event queue.

        @param event_num: int - The number of events to return.

        @return dict[str:str] Returns the event parameters in the format
        {
            "account_address": str
        }
        """
import sys
from common import account_config, utils
from python_scripts import cadence_scripts
import asyncio
from pathlib import Path
import os
import configparser

import logging
log = logging.getLogger(__name__)
utils.configureLogging()


async def createVoteBoxes() -> list[dict[str:str]]:
    """This function seems redundant, but I need to create this wrapper over the function that runs the transaction that creates a new votebox because I need to run this inside a loop and asyncio has a weird way to do these things...
    @param tx_signer_address: str - The address for the account that is going to digitally sign the transaction that creates the new votebox resource

    @return list[dict[str:str]] If successful, this function returns a list with the parameters of the VoteBoxCreated event in the format:
    {
        "voter_address": str
    }
    """
    votebox_created_events: list[dict[str:str]] = []

    for user_account in ctx.accounts:
        votebox_created_event: dict[str:str] = await tx_runner.createVoteBox(tx_signer_address=user_account["address"].hex())
        votebox_created_events.append(votebox_created_event)
    
    return votebox_created_events

def sayHello():
    print("Hello Mr. Bad Luck!")

def printSysVars():
    print("sys.prefix = ", sys.prefix)
    print("sys.exec_prefix = ", sys.exec_prefix)
    print("sys.base_prefix = ", sys.base_prefix)
    print("sys.base_exec_prefix = ", sys.base_exec_prefix)

async def main():
    script_runner = cadence_scripts.RunScript()

    result = await script_runner.testContractConsistency()

    if (result):
        log.info("Project is consistent!")
    else:
        log.warning("Project is not yet consistent!")
        

# Use the following set of instructions to run asynchronous loops
# new_loop = asyncio.new_event_loop()
# asyncio.set_event_loop(new_loop)

# new_loop.run_until_complete(main())

asyncio.run(main())
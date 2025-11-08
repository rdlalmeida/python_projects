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
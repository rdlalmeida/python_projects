import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from common.account_config import AccountConfig
from subprocess import Popen
import pathlib
import time

if __name__ == "__main__":
    # Get the environment configuration
    ctx = AccountConfig()
    account_addresses: list[str] = ctx.getAddresses()
    # Remove the service account from the set
    account_addresses.remove(ctx.service_account["address"].hex())

    # Set the path to the python install in the virtualenv dir to get the necessary module imports
    virtualenv_python = pathlib.Path(os.getcwd()).joinpath("virtualenv", "bin", "python")

    for account_address in account_addresses:
        # Create the subprocess command by setting each element in a string list
        voter_process: list[str] = [virtualenv_python.__str__(), "runners/voter_runner.py", account_address, "&"]

        # Send out one of the process
        result = Popen(voter_process)

        # print(result)

        # Sleep for a few seconds before sending out the next one, to avoid concurrency issues
        time.sleep(10)

# TODO: Include the 'mainnet' option for this script

"""
This script serves to enable a fast environment switching between the local emulator, testnet, and mainnet testing.

The issue currently is with the python layer that I'm using to interact with the local emulator. By some retarded reason, contracts, scripts or transactions require a specific deployment address to be set in their import statements to resolve, while Cadence has simplified this in later versions.
Specifically, since a while now, Cadence only requests the name of the contract to be imported, e. g., 'import "Burner"', with the contract name within quotes. Cadence resolves the source of the contract automatically, i. e., checks the available networks and relieves the developer from this moronic task.

But when I slapped a high level python layer on these contracts, when I interact with the local emulator, the python interface freaks out and doesn't allow me to import any contracts with this standard. For this shit to work, I need to specify the local address where the contracts are deployed, e. g. "import Burner from 0xf753ab91..."

Problem: Flow testnet and other executable platforms no longer recognise this format, and complain if a contract, script or transaction still uses these types of imports.

This is a shitty conundrum and the easiest way I could find to solve it is to create this python script to automate the comment and uncomment of imports in all .cdc files...

USAGE: python common/set_cadence_environment.py <local | remote | testnet>

local - The contracts, scripts, and transactions have their imports set to the addresses defined in the 'emulator' section of each contract in the flow.json file, e.g., "import Crypto from 0xf8d6e0586b0a20c7
remote - The contracts, scripts, and transactions have the "from" section removed from their imports and the imported contracts set under quotes, e.g, "import 'Crypto'"
testnet - The contracts, scripts, and transactions have their imports set to the addresses defined in the 'testnet' section of each contract in the flow.json file, e.g., "import Crypto from 0x8c5303eaa26202d6"
"""
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import configparser
from pathlib import Path
from common.utils import Utils

import logging
log = logging.getLogger(__name__)
Utils.configureLogging()

project_cwd = Path(os.getcwd())
config_path = project_cwd.joinpath("common", "config.ini")
config = configparser.ConfigParser()
config.read(config_path)

# Path for the buffer file
temp_path: Path = Path(os.getcwd()).joinpath("temp_file.cdc")

def main(env: str = "local"):
    if (len(sys.argv) > 1):
        input_env: str = sys.argv[1].lower().strip()

    if (input_env == "local"):
        env = "local"
    elif (input_env == "remote"):
        env = "remote"
    elif (input_env == "testnet"):
        env = "testnet"
    else:
        log.warning(f"WARNING: Invalid input provided '{input_env}'. Defaulting to 'local'")

    set_environment(env=env)

def set_environment(env: str = "local") -> None:
    """
    Main function for this module. This is the entry point for a function that scans every .cdc file in this project folder, reads it line by line and switches the imports on and off depending on the environment mode set, namely, "local" for the local emulator, or "testnet" for remote development.
    
    :param env (str): The environment to set the Cadence files to. This function expects and validates the options, namely, "local", "remote", and "testnet"
    """
    # Grab the paths of all cdc files into dedicated arrays
    cadence_contracts: list[Path] = []
    cadence_scripts: list[Path] = []
    cadence_transactions: list[Path] = []

    # Move into each of the project subfolders and list all the files in it to the arrays in question
    current_path: Path = Path(os.getcwd()).joinpath("cadence", "contracts")

    current_files = os.listdir(current_path)

    for contract in current_files:
        cadence_contracts.append(current_path.joinpath(contract))

    # Do the transactions
    current_path: Path = Path(os.getcwd()).joinpath("cadence", "transactions")

    current_files = os.listdir(current_path)

    for transaction in current_files:
        cadence_transactions.append(current_path.joinpath(transaction))

    # Repeat for the scripts
    current_path: Path = Path(os.getcwd()).joinpath("cadence", "scripts")

    current_files = os.listdir(current_path)

    for script in current_files:
        cadence_scripts.append(current_path.joinpath(script))

    # Validate input before anything else
    if (env.lower() == "local"):
        # Process each file in the contracts, transactions, and scripts array
        log.info("Switching project contracts to local mode: ")
        for contract in cadence_contracts:
            log.info(f"Processing contract '{contract}'...")
            switchToLocal(source_path=contract)
        
        log.info("\n\nSwitching project transactions to local mode:")
        for transaction in cadence_transactions:
            log.info(f"Processing transaction '{transaction}'...")
            switchToLocal(source_path=transaction)

        log.info("\n\nSwitching project scripts to local mode:")
        for script in cadence_scripts:
            log.info(f"Processing script '{script}'...")
            switchToLocal(source_path=script)

    elif (env.lower() == "remote"):
        # Process each file in the contracts, transactions, and scripts array
        log.info("Switching project contracts to remote mode: ")
        for contract in cadence_contracts:
            log.info(f"Processing contract '{contract}'...")
            switchToRemote(source_path=contract)

        log.info("\n\nSwitching project transactions to remote mode: ")
        for transaction in cadence_transactions:
            log.info(f"Processing transaction '{transaction}'...")
            switchToRemote(source_path=transaction)

        log.info("\n\nSwitching project scripts to remote mode: ")
        for script in cadence_scripts:
            log.info(f"Processing script '{script}'...")
            switchToRemote(source_path=script)

    elif (env.lower() == "testnet"):
        log.info("Switching project contracts to testnet mode: ")
        for contract in cadence_contracts:
            log.info(f"Processing contract '{contract}':")
            switchToTestnet(source_path=contract)
        
        log.info("\n\nSwitching project transactions to testnet mode:")
        for transaction in cadence_transactions:
            log.info(f"Processing transaction '{transaction}':")
            switchToTestnet(source_path=transaction)

        log.info("\n\nSwitching project scripts to testnet mode:")
        for script in cadence_scripts:
            log.info(f"Processing script '{script}':")
            switchToTestnet(source_path=script)
    else:
        raise Exception(f"ERROR: Invalid environment option provided: {env}. Please use either 'local' or 'remote' to continue")


def switchToLocal(source_path: Path) -> None:
    """
    Function to switch the source text provided, under the assumption that it refers to a contract, transaction, or script, with all the import statements normalised to the local environment, i.e., with the imports recognised in the local emulator. NOTE: For this function, it is irrelevant if the source files are in "remote" or "testnet" mode since the contract addresses are both getting cut. 
    
    :param source_text (Path): The Path object for the source file to adapt.
    """
    # Validate the path provided
    if (not os.path.exists(source_path)):
        raise Exception(f"ERROR: The source path provided: {source_path.__str__()} does not exists!")

    if (os.path.isdir(source_path)):
        raise Exception(f"ERROR: The source path provided: {source_path.__str__()} points to a directory and not a file!")
    
    # All seems good so far. Read the file line by line and process it
    file_stream = open(source_path, "+r")
    
    try:
        temp_stream = open(temp_path, "+x")
    except FileExistsError:
        temp_stream = open(temp_path, "+w")

    current_line = file_stream.readline()

    while (current_line != ""):
        # Read the file line by line and look out for import statements but without the 'from' bit
        if (current_line.__contains__('import ') and not current_line.__contains__('from')):
            # Import lines set for the remote environment are set as 'import "<contract_name>"', so if I have an 'import' followed by a single '"', I have a line that needs 
            # changing
            # Remove the quotes first
            current_line = current_line.replace('\"', '')

            # Split it by the space character. This is a remote bound import, so it should yield two elements with the last one being the contract imported
            import_elements: list[str] = current_line.strip().split(' ')
            contract_name: str = import_elements[-1]

            # Grab the contract name and test if it is one of the ones that are not deployed in the service_account
            if (contract_name == "FlowFees"):
                # Append the rest of the import statement
                current_line = f"import {contract_name} from 0x{config.get(section="emulator", option=contract_name)}\n"
            elif (contract_name == "FlowToken"):
                current_line = f"import {contract_name} from 0x{config.get(section="emulator", option=contract_name)}\n"
            elif (contract_name == "FungibleToken"):
                current_line = f"import {contract_name} from 0x{config.get(section="emulator", option=contract_name)}\n"
            elif (contract_name == "Burner"):
                current_line = f"import {contract_name} from 0x{config.get(section="emulator", option=contract_name)}\n"
            elif (contract_name == "Crypto"):
                current_line = f"import {contract_name} from 0x{config.get(section="emulator", option=contract_name)}\n"
            else:
                # Default to the service account
                current_line = f"import {contract_name} from 0x{config.get(section="emulator", option="service_account")}\n"
        
        elif (current_line.__contains__("import ") and current_line.__contains__(" from ")):
            line_elements: list[str] = current_line.strip().split(' ')
            current_line: str = ""

            contract_name: str = line_elements[1]

            for i in range(0, len(line_elements) - 1):
                current_line += f"{line_elements[i]} "

            if (contract_name == "FlowFees"):
                # Finish the new line
                current_line += f"0x{str(config.get(section="emulator", option=contract_name))}\n"
            elif (contract_name == "FlowToken"):
                current_line += f"0x{str(config.get(section="emulator", option=contract_name))}\n"
            elif (contract_name == "FungibleToken"):
                current_line += f"0x{str(config.get(section="emulator", option=contract_name))}\n"
            elif (contract_name == "Burner"):
                current_line += f"0x{str(config.get(section="emulator", option=contract_name))}\n"
            elif (contract_name == "Crypto"):
                current_line += f"0x{str(config.get(section="emulator", option=contract_name))}\n"
            else:
                # Default to the service account if the contract is different from these ones
                current_line += f"0x{str(config.get(section="emulator", option="service_account"))}\n"
        
        # Write the line to the temp file
        temp_stream.write(current_line)
        
        # Grab new line and go for another round
        current_line = file_stream.readline()
        
    # Done. Rewrite the initial file by re-opening it in truncating mode, and dumping the temp stream into it
    # Close the origin stream and temp stream
    file_stream.close()
    temp_stream.close()

    # Re-open it in truncating mode
    file_stream = open(source_path, "+w")
    # And the temp stream in read mode
    temp_stream = open(temp_path, "+r")

    # Write the temp stream into the file stream
    file_stream.writelines(temp_stream.readlines())

    # Close both streams to finish the job
    file_stream.close()
    temp_stream.close()


def switchToTestnet(source_path: Path) -> None:
    """
    Function to switch the source text provided, under the assumption that it refers to a contract, transaction, or script, with all the import statements normalised to the testnet environment, i.e., with the imports recognisable by the testnet environment

    :param source_text (Path): The Path object for the source file to adapt.
    """
    # Validate the path provided
    if (not os.path.exists(source_path)):
        raise Exception(f"ERROR: The source path provided {source_path.__str__()} does not exists!")
    
    if (os.path.isdir(source_path)):
        raise Exception(f"ERROR: The source path provided {source_path.__str__()} points to a directory instead of a file!")
    
    file_stream = open(source_path, "+r")

    try:
        temp_stream = open(temp_path, "+x")
    except FileExistsError:
        temp_stream = open(temp_path, "+w")

    current_line = file_stream.readline()

    while (current_line != ""):
        # Test for the two elements that characterise a local import
        if (current_line.__contains__("import ") and current_line.__contains__(" from ")):
            # In this case, split the line by spaces
            line_elements: list[str] = current_line.strip().split(' ')
            current_line: str = ""

            # Extract the contract name for a variable. The split should have returned:
            # line_elements[0] = import
            # line_elements[1] = <contract_name>
            # line_elements[2] = from
            # line_elements[2] = <contract_address>
            # 
            # The contract name should be in element #1
            contract_name: str = line_elements[1]

            # Rebuilt the line with all elements but the last one, which is currently the one with the local contract address
            for i in range(0, len(line_elements) - 1):
                current_line += f"{line_elements[i]} "
            
            # Append the new address to the line
            if (contract_name == "FlowFees"):
                # Finish the new line
                current_line += f"0x{str(config.get(section="testnet", option=contract_name))}\n"
            elif (contract_name == "FlowToken"):
                current_line += f"0x{str(config.get(section="testnet", option=contract_name))}\n"
            elif (contract_name == "FungibleToken"):
                current_line += f"0x{str(config.get(section="testnet", option=contract_name))}\n"
            elif (contract_name == "Burner"):
                current_line += f"0x{str(config.get(section="testnet", option=contract_name))}\n"
            elif (contract_name == "Crypto"):
                current_line += f"0x{str(config.get(section="testnet", option=contract_name))}\n"
            else:
                # Default to the service account if the contract is different from these ones
                current_line += f"0x{str(config.get(section="testnet", option="service_account"))}\n"
        
        elif(current_line.__contains__("import ") and not current_line.__contains__("from")):
            # The source file is in remote mode
            # Remove the quotes from the contract name
            current_line = current_line.replace('\"', '')

            # Split the line by spaces into tokens
            line_elements: list[str] = current_line.strip().split(' ')
            contract_name: str = line_elements[1]

            if (contract_name == "FlowFees"):
                current_line = f"import {contract_name} from 0x{config.get(section="testnet", option=contract_name)}\n"
            elif (contract_name == "FlowToken"):
                current_line = f"import {contract_name} from 0x{config.get(section="testnet", option=contract_name)}\n"
            elif (contract_name == "FungibleToken"):
                current_line = f"import {contract_name} from 0x{config.get(section="testnet", option=contract_name)}\n"
            elif (contract_name == "Burner"):
                current_line = f"import {contract_name} from 0x{config.get(section="testnet", option=contract_name)}\n"
            elif (contract_name == "Crypto"):
                current_line = f"import {contract_name} from 0x{config.get(section="testnet", option=contract_name)}\n"
            else:
                # Default to the service account
                current_line = f"import {contract_name} from 0x{config.get(section="testnet", option="service_account")}\n"
        
        # Write the line to the temp file
        temp_stream.write(current_line)

        # Grab new line and go for another round
        current_line = file_stream.readline()

    # Done. Rewrite the initial file by re-opening it in truncating mode, and dump the temp stream into it.
    # Close the origin and temp stream
    file_stream.close()
    temp_stream.close()

    # Re-open it in truncating mode
    file_stream = open(source_path, "+w")
    # And the temp stream in read mode
    temp_stream = open(temp_path, "+r")

    # Write the temp stream into the file stream
    file_stream.writelines(temp_stream.readlines())

    # Close both streams to finish the job
    file_stream.close()
    temp_stream.close()


def switchToRemote(source_path: Path) -> None:
    """
    Function to switch the source text provided, under the assumption that it refers to a contract, transaction, or script, with all the import statements normalised to the remote environment, i.e., with the imports recognisable by an environment that is able to process absolute contract paths.

    :param source_text (Path): The Path object for the source file to adapt.
    """
    # Validate the path provided
    if (not os.path.exists(source_path)):
        raise Exception(f"ERROR: The source path provided: {source_path.__str__()} does not exists!")
    
    if (os.path.isdir(source_path)):
        raise Exception(f"ERROR: The source path provided: {source_path.__str__()} points to a directory instead of a file!")
    
    file_stream = open(source_path, "+r")
    try:
        temp_stream = open(temp_path, "+x")
    except FileExistsError:
        temp_stream = open(temp_path, "+w")

    current_line = file_stream.readline()

    while (current_line != ""):
        # Test for the two elements that characterise a local import
        if (current_line.__contains__("import ") and current_line.__contains__(" from ")):
            # This one is easy. Split the line into words using a space as separator
            line_elements: list[str] = current_line.split(' ')

            # The two first line elements are the ones that I need. Put them in a line with the second one inside quotes
            current_line = f'{line_elements[0]} "{line_elements[1]}"\n'
        
        # Write the current line to the temp file
        temp_stream.write(current_line)

        # And grab a new one
        current_line = file_stream.readline()
    
    # Done. Rewrite the initial file by re-opening it in truncating mode, and dumping the temp stream into it
    # Close the origin stream and temp stream
    file_stream.close()
    temp_stream.close()

    # Re-open it in truncating mode
    file_stream = open(source_path, "+w")
    # And the temp stream in read mode
    temp_stream = open(temp_path, "+r")

    # Write the temp stream into the file stream
    file_stream.writelines(temp_stream.readlines())

    # Close both streams to finish the job
    file_stream.close()
    temp_stream.close()


main(env="local")
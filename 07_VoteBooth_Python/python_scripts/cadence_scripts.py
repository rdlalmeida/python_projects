from flow_py_sdk import (
    flow_client,
    cadence,
    Script
)

import configparser
from common import utils, account_config
import pathlib
import os

# Setup logging capabilities
import logging
log = logging.getLogger(__name__)
utils.configureLogging()

class ScriptError(Exception):
    """Custom Exception to be raised when a Flow script was not properly executed.
    Attributes:
        script_name: The name of the script that did not executed.
    """

    def __init__(self, script_name: str) -> None:
        config = configparser.ConfigParser()
        config.read(pathlib.Path(os.getcwd()).joinpath("common", "config.ini"))
        network = config.get(section="network", option="current")
        host = config.get(section=network, option="host")
        port = config.get(section=network, option="port")
        self.message = f"Script {script_name} did not execute in network {host}:{port}"

        super().__init__(self.message)

class ScriptRunner():
    def __init__(self) -> None:
        super().__init__()
        self.ctx = account_config.AccountConfig()
        self.project_cwd = pathlib.Path(os.getcwd())

        config_path = self.project_cwd.joinpath("common", "config.ini")
        self.config = configparser.ConfigParser()
        self.config.read(config_path)


    def getScript(self, script_name: str, script_arguments: list) -> Script:
        """
        Simple function to abstract the logic of reading the config file, grab the script file, read it, and building the Script object
        :param script_name (str): The name of the script to be retrieved and configured.
        :param script_arguments (list): A list with the arguments to set in the script object to execute.

        :return (Script): If successful, this function returns a configured Script object ready to be executed.
        """
        try:
            script_path = pathlib.Path(self.config.get(section="scripts", option=script_name))
        except configparser.NoOptionError:
            log.error(f"No script named '{script_name}' configured for this project.")
            exit(-2)
        except Exception as e:
            log.error(f"Unable to retrieve a valid path for script '{script_name}':")
            log.error(e)
            exit(-1)
        
        script_code = open(script_path).read()

        return Script(
            code=script_code,
            arguments=script_arguments
        )

    
    async def testContractConsistency(self) -> str:
        """
        Function to abstract the execution of the '01_test_contract_consistency.cdc' Cadence script

        :return (bool): This function returns True if all the deployed contracts for this project are consistent, False otherwise.
        """
        name = "01_test_contract_consistency"

        # Create the script object with the argument array
        script_object = self.getScript(script_name=name, script_arguments=[])
        # Run the script
        async with flow_client(
            host=self.ctx.access_node_host, port=self.ctx.access_node_port
        ) as client:
            script_result = await client.execute_script(script=script_object)

            if (not script_result):
                raise ScriptError(script_name=name)
            
            if (script_result.value == None):
                return ""
            else:
                return script_result.value.hex()
    
        
    async def getActiveElections(self, votebox_address: str = None) -> list[int]:
        """Function to retrieve a list with all the active election ids.

        :param votebox_address (str?): If provided, this function gets the list of active election ids for the votebox configured in the address provided. Otherwise, the script gets the list of active election ids from the central votebooth contract instead.

        :return (list[int]): This function returns the list of active election ids.
        """
        name = "02_get_active_elections"
        arguments = [cadence.Address.from_hex(votebox_address)] if votebox_address else [cadence.Optional(None)]
        # arguments = [cadence.Optional(cadence.Address.from_hex(votebox_address))]

        script_object = self.getScript(script_name=name, script_arguments=arguments)

        async with flow_client(
            host=self.ctx.access_node_host, port=self.ctx.access_node_port
        ) as client:
            script_result = await client.execute_script(script=script_object)

            if (not script_result):
                raise ScriptError(script_name=name)
            
            # This particular script returns an array of cadence.UInt64 values. Cast those to a regular array before returning.
            return_list: list[int] = []

            for return_item in script_result.value:
                return_list.append(return_item.value)

            return return_list
    
    
    async def getElectionName(self, election_id: int, votebox_address: str = None) -> str:
        """Function to retrieve the name of the election with the id provided as input.

        :param election_id (int): The election id for the election whose name is to be retrieved
        :param votebox_address (str?): If provided, the script retrieves the election name from the votebox resource. If None is provided, it goes to the votebooth contract.

        :return (str): The function returns the name of the election with the id provided.
        """
        name = "03_get_election_name"
        arguments = [cadence.UInt64(election_id)]

        if(votebox_address):
            arguments.append(cadence.Address.from_hex(votebox_address))
        else:
            arguments.append(cadence.Optional(None))

        script_object = self.getScript(script_name=name, script_arguments=arguments)

        async with flow_client(
            host=self.ctx.access_node_host, port=self.ctx.access_node_port
        ) as client:
            
            script_result = await client.execute_script(script=script_object)

            if (not script_result):
                raise ScriptError(script_name=name)
            
            return str(script_result.value.__str__())
    
    
    async def getElectionBallot(self, election_id: int, votebox_address: str = None) -> str:
        """Function to retrieve the ballot of the election with the id provided as input.

        :param election_id (int): The election id for the election whose ballot is to be retrieved
        :param votebox_address (str?): If provided, the script retrieves the election ballot from the votebox resource. If None is provided, it goes to the votebooth contract.

        :returns (str): The function returns the ballot set to the election with the id provided.
        """
        name = "04_get_election_ballot"
        arguments = [cadence.UInt64(election_id)]

        if (votebox_address):
            arguments.append(cadence.Address.from_hex(votebox_address))
        else:
            arguments.append(cadence.Optional(None))

        script_object = self.getScript(script_name=name, script_arguments=arguments)

        async with flow_client(
            host=self.ctx.access_node_host, port=self.ctx.access_node_port
        ) as client:
            script_result = await client.execute_script(script=script_object)

            if (not script_result):
                raise ScriptError(script_name=name)

            return str(script_result.value)
    
    
    async def getElectionOptions(self, election_id: int, votebox_address: str = None) -> dict[int: str]:
        """Function to retrieve the set of options configured for the election with the id provided.

        :param election_id (int): The election id for the election whose set of options are to be retrieved.
        :param votebox_address: (str?): If provided, the script retrieves the set of election options for the votebox resource. If None is provided, this goes to the votebooth contract.

        :returns (dict[int: str]): The function returns the set of active options for the election, as a dictionary with id as key and the option text as value.
        """
        name = "05_get_election_options"
        arguments = [cadence.UInt64(election_id)]

        if (votebox_address):
            arguments.append(cadence.Address.from_hex(votebox_address))
        else:
            arguments.append(cadence.Optional(None))
        
        script_object = self.getScript(script_name=name, script_arguments=arguments)

        async with flow_client(
            host=self.ctx.access_node_host, port=self.ctx.access_node_port
        ) as client:
            script_result = await client.execute_script(script=script_object)

            if (not script_result):
                raise ScriptError(script_name=name)
            
            return utils.convertCadenceDictionaryToPythonDictionary(cadence_dict=script_result.value)
    

    async def getElectionId(self, election_id: int, votebox_address: str = None) -> int:
        """Function to retrieve the election id, from the election resource itself, for the election with the id provided. Redundant, I know...

        :param election_id (int): The election id for the election whose election id is to be retrieved.
        :param votebox_address (str?) If provided, the script retrieves the election id from the votebox resource. If None is provided, this goes to the votebooth contract.

        :returns (int): The function returns the election identifier for the election resource identified by the input.
        """
        name = "06_get_election_id"
        arguments = [cadence.UInt64(election_id)]

        if (votebox_address):
            arguments.append(cadence.Address.from_hex(votebox_address))
        else:
            arguments.append(cadence.Optional(None))

        script_object = self.getScript(script_name=name, script_arguments=arguments)
        async with flow_client(
            host=self.ctx.access_node_host, port=self.ctx.access_node_port
        ) as client:
            script_result = await client.execute_script(script=script_object)

            if (not script_result):
                raise ScriptError(script_name=name)
        
            return int(script_result.value.__str__())
    

    async def getPublicEncryptionKey(self, election_id: int, votebox_address: str = None) -> str:
        """Function to retrieve the public encryption key for the election identified by id provided as argument.

        :param election_id (int): The election id for the election whose public encryption key is to be retrieved.
        :param votebox_address (str?): If provided, the script retrieves the public encryption key from the votebox resource. If None is provided, this goes to the votebooth contract.

        :returns (str): The function returns the public encryption key for the election identified by the election id provided.
        """
        name = "07_get_public_encryption_key"
        arguments = [cadence.UInt64(election_id)]

        if (votebox_address):
            arguments.append(cadence.Address.from_hex(votebox_address))
        else:
            arguments.append(cadence.Optional(None))

        script_object = self.getScript(script_name=name, script_arguments=arguments)

        async with flow_client(
            host=self.ctx.access_node_host, port=self.ctx.access_node_port
        ) as client:
            script_result = await client.execute_script(script=script_object)

            if (not script_result):
                raise ScriptError(script_name=name)
            
            return script_result.value.__str__()
    

    async def getElectionCapability(self, election_id: int, votebox_address: str = None) -> cadence.Capability:
        """Function to retrieve the capability value configured in the election identified by the id provided as argument.

        :param election_id (int): The election id for the election whose public capability is to be retrieved.
        :param votebox_address: (str?): If provided, the script retrieves the public encryption key from a votebox resource. If None is provided, this goes to the votebooth contract.

        :return (cadence.Capability): This function returns the cadence.Capability-type object configured for the election with the id provided.
        """
        name = "08_get_election_capability"
        arguments = [cadence.UInt64(election_id)]

        if (votebox_address):
            arguments.append(cadence.Address.from_hex(votebox_address))
        else:
            arguments.append(cadence.Optional(None))

        script_object = self.getScript(script_name=name, script_arguments=arguments)

        async with flow_client(
            host=self.ctx.access_node_host, port=self.ctx.access_node_port
        ) as client:
            script_result = await client.execute_script(script=script_object)

            if (not script_result):
                raise ScriptError(script_name=name)
            
            return script_result.value
    

    async def getElectionTotals(self, election_id: int, votebox_address: str = None) -> dict[str: int]:
        """Function to retrieve the ballots totals for the election identified by the id provided as argument.

        :param election_id (int): The election id for the election whose ballot totals are to be retrieved.
        :param votebox_address (str?): If provided, the script retrieved the ballot totals from the votebox resource. If None is provided, this goes to the votebooth contract.

        @return dict[str: int] This function returns a dictionary in the format {"totalBallotsMinted": <value>, "totalBallotsSubmitted": <value>} regarding the election resource identified by the election id provided.
        """
        name = "09_get_election_totals"
        arguments = [cadence.UInt64(election_id)]

        if (votebox_address):
            arguments.append(cadence.Address.from_hex(votebox_address))
        else:
            arguments.append(cadence.Optional(None))

        script_object = self.getScript(script_name=name, script_arguments=arguments)

        async with flow_client(
            host=self.ctx.access_node_host, port=self.ctx.access_node_port
        ) as client:
            script_result = await client.execute_script(script=script_object)

            if (not script_result):
                raise ScriptError(script_name=name)
            
            return utils.convertCadenceDictionaryToPythonDictionary(cadence_dict=script_result.value)


    async def getElectionStoragePath(self, election_id: int) -> str:
        """Function to retrieve the storage path for the election identified by the id provided as argument

        :param election_id (int): The election id for the election whose storage path is to be retrieved.

        :return (str): Returns a string representation of the storage path retrieved.
        """
        name = "10_get_election_storage_path"
        arguments = [cadence.UInt64(election_id)]

        script_object = self.getScript(script_name=name, script_arguments=arguments)

        async with flow_client(
            host=self.ctx.access_node_host, port=self.ctx.access_node_port
        ) as client:
            script_result = await client.execute_script(script=script_object)

            if (not script_result):
                raise ScriptError(script_name=name)

            return "/" + script_result.domain + "/" + script_result.identifier
    

    async def getElectionPublicPath(self, election_id: int) -> str:
        """Function to retrieve the public path for the election identified by the id provided as argument.

        :param election_id (int): The election id for the election whose public path is to be retrieved.

        :return (str): Returns a string representation of the public path retrieved.
        """
        name = "11_get_election_public_path"
        arguments = [cadence.UInt64(election_id)]

        script_object = self.getScript(script_name=name, script_arguments=arguments)
        async with flow_client(
            host=self.ctx.access_node_host, port=self.ctx.access_node_port
        ) as client:
            script_result = await client.execute_script(script=script_object)

            if (not script_result):
                raise ScriptError(script_name=name)
            
            return "/" + script_result.domain + "/" + script_result.identifier


    async def getElectionsList(self) -> dict[int: str]:
        """Function to retrieve the list of active elections directly from the election index resource, therefore this function does not need any additional inputs to execute.

        :return (dict[int: str]): This function returns the list of currently active elections in a dictionary with the format {<electionId>: <electionName>}
        """
        name = "12_get_elections_list"
        arguments = []

        script_object = self.getScript(script_name=name, script_arguments=arguments)

        async with flow_client(
            host=self.ctx.access_node_host, port=self.ctx.access_node_port
        ) as client:
            script_result = await client.execute_script(script=script_object)

            if (not script_result):
                raise ScriptError(script_name=name)
            
            return utils.convertCadenceDictionaryToPythonDictionary(cadence_dict=script_result)

    
    async def getBallotOption(self, election_id: int, votebox_address: str) -> str:
        """Function to retrieve the option string currently set in the votebox in the address provided as input, and submitted under the election id also provided as input.

        :param election_id (int): The election id for the election whose ballot option is to be retrieved.
        :param votebox_address (str) The address for the account from where the votebox resource reference is to be retrieved.:
        
        :return (str): If there's a ballot submitted for the election id provided, in the votebox for the address provided as well, this function returns the option set in it. Otherwise returns None. 
        """
        name = "13_get_ballot_option"
        arguments = [cadence.UInt64(election_id), cadence.Address.from_hex(votebox_address)]

        script_object = self.getScript(script_name=name, script_arguments=arguments)

        async with flow_client(
            host=self.ctx.access_node_host, port=self.ctx.access_node_port
        ) as client:
            script_result = await client.execute_script(script=script_object)

            if (not script_result):
                raise ScriptError(script_name=name)
            
            return script_result.value

    
    async def getBallotId(self, election_id: int, votebox_address: str) -> int:
        """Function to retrieve the ballot identifier for a ballot set in the votebox inside the address provided, and under the election id provided as well.

        :param election_id (int): The election id for the election whose ballot id is to be retrieved.
        :param votebox_address (str): The account address from where the votebox resource reference is to be retrieved

        :return (int): This function returns the ballot identifiers number for the Ballot stored under the election id inside the votebox resource retrieved from the input argument.
        """
        name = "14_get_ballot_id"
        arguments = [cadence.UInt64(election_id), cadence.Address.from_hex(votebox_address)]

        script_object = self.getScript(script_name=name, script_arguments=arguments)

        async with flow_client(
            host=self.ctx.access_node_host, port=self.ctx.access_node_port
        ) as client:
            script_result = await client.execute_script(script=script_object)

            if (not script_result):
                raise ScriptError(script_name=name)
            
            return script_result.value.value
    

    async def getElectionResults(self, election_id: int) -> dict[str: int]:
        """Function to retrieve the results for the election identified by the election id provided as input in this function.

        :param election_id (int): The election id for the election whose results are to be retrieved.

        :return (dict[str: int]): If the election identified by the id provided as argument is finalised, this function returns its results in the form of a dictionary, using the format {<electionBallotOptions>: <votesCounted>}. If the election is still ongoing, this function returns None.
        """
        name = "15_get_election_results"
        arguments = [cadence.UInt64(election_id)]

        script_object = self.getScript(script_name=name, script_arguments=arguments)

        async with flow_client(
            host=self.ctx.access_node_host, port=self.ctx.access_node_port
        ) as client:
            
            script_result = await client.execute_script(script=script_object)

            if (not script_result):
                raise ScriptError(script_name=name)
            
            return utils.convertCadenceDictionaryToPythonDictionary(cadence_dict=script_result)

    async def isElectionFinished(self, election_id: int) -> bool:
        """Function to retrieve the running state for the election resource identified by the election id provided as argument.

        :param election_id (int): The election id for the election whose status is to be retrieved.

        :return (bool): This function returns True if the election has been tallied already, False otherwise.        
        """
        name = "16_is_election_finished"
        arguments = [cadence.UInt64(election_id)]

        script_object = self.getScript(script_name=name, script_arguments=arguments)

        async with flow_client(
            host=self.ctx.access_node_host, port=self.ctx.access_node_port
        ) as client:
            script_result = await client.execute_script(script=script_object)

            if (not script_result):
                raise ScriptError(script_name=name)
            
            return bool(script_result.value)


    async def getElectionWinner(self, election_id: int) -> dict[str:int]:
        """Function to retrieve the winning option for the election with the identifier provided as argument.

        :param election_id (int): The election identifier for the Election to be processed.

        :return (dict[str:int]): The function returns a dictionary with the winning option for the election, which can have multiple elements for tied election.
        """
        name = "18_get_election_winner"
        arguments = [cadence.UInt64(election_id)]

        script_object: Script = self.getScript(script_name=name, script_arguments=arguments)

        async with flow_client(
            host=self.ctx.access_node_host, port=self.ctx.access_node_port
        ) as client:
            script_result = await client.execute_script(script=script_object)

            if (not script_result):
                raise ScriptError(script_name=name)

            if (len(script_result.value) > 0):
                return utils.convertCadenceDictionaryToPythonDictionary(cadence_dict=script_result)
            else:
                return {}
            
    
    async def getElectionEncryptedBallots(self, election_id: int) -> list[str]:
        """Function to retrieve the set of encrypted options to be further processed and tallied.

        :param election_id (int): The election identifier for the Election to be processed.

        :return (list[str]): The list of Ballot options, still in its encrypted format
        """
        name = "19_get_election_encrypted_ballots"
        arguments = [cadence.UInt64(election_id)]

        script_object: Script = self.getScript(script_name=name, script_arguments=arguments)

        async with flow_client(
            host=self.ctx.access_node_host, port=self.ctx.access_node_port
        ) as client:
            script_result = await client.execute_script(script=script_object)

            if (not script_result):
                raise ScriptError(script_name=name)
            
            encrypted_options: str = []
            if (len(script_result.value) > 0):
                # I need to extract and decode each value to a return array first
                for result_value in script_result.value:
                    encrypted_options.append(result_value.__str__())

                return encrypted_options
            else:
                return []
            

    async def isBallotReceiptValid(self, election_id: int, ballot_receipt: int) -> bool:
        """
        This function tests if a given ballot receipt provided as argument is currently among the ones tallied by an election identified by the electionId provided as input.
        
        :param election_id (int): The election identifier for the instance to use for the check.
        :param ballot_receipt (int): The ballot receipt to test.
        :return (bool): If the ballot receipt provided is among the ones tallied in the election, the function returns true, false otherwise.
        """
        name = "20_is_ballot_receipt_valid"
        arguments = [cadence.UInt64(election_id), cadence.UInt64(ballot_receipt)]

        script_object: Script = self.getScript(script_name=name, script_arguments=arguments)

        async with flow_client(
            host=self.ctx.access_node_host, port=self.ctx.access_node_port
        ) as client:
            script_result = await client.execute_script(script=script_object)

            if (not script_result):
                raise ScriptError(script_name=name)
            
            return bool(script_result.value)
        
    
    async def getAccountBalance(self, recipient_address: str) -> dict[str:float]:
        """
        This function returns the account balance for the account whose address is provided as input.

        :param recipient_address (str): The account address for the account whose balance is to be retrieved
        :return (dict[str:float]): If the account exists, this function returns the result in the format
        {
            "default": float,
            "available": float
        },
        where "default" is the value from the default vault in the account, "available" is the amount that is available to be moved.
        """
        name = "21_get_account_balance"
        arguments = [cadence.Address.from_hex(recipient_address)]

        script_object: Script = self.getScript(script_name=name, script_arguments=arguments)

        async with flow_client(
            host=self.ctx.access_node_host, port=self.ctx.access_node_port
        ) as client:
            script_result = await client.execute_script(script=script_object)

            if (not script_result):
                raise ScriptError(script_name=name)
            
            if (len(script_result.value) > 0):
                account_balance = utils.convertCadenceDictionaryToPythonDictionary(cadence_dict=script_result)

                # The balance value returned is missing the decimal value at the 8th digit. Fix this before returning the value
                scale_factor: int = 100000000
                account_balance["default"] = float(account_balance["default"])/float(scale_factor)
                account_balance["available"] = float(account_balance["available"])/float(scale_factor)

                return account_balance
            else:
                return {}

    

    async def getAccountStorage(self, recipient_address: str) -> dict[str: int]:
        """
        This function returns the account storage values for the account whose address is provided as input.

        :param recipient_address (str): The account address for the account whose storage values are to be retrieved. 
        :return (dict[str:int]): If the account exists, this function returns the result in the format
        {
            "capacity": int,
            "used": int 
        },
        where "capacity" is the account available capacity in bytes, "used" is the current amount of storage currently used by the account, also in bytes.
        """
        name = "22_get_account_storage"
        arguments = [cadence.Address.from_hex(recipient_address)]

        script_object: Script = self.getScript(script_name=name, script_arguments=arguments)

        async with flow_client(
            host=self.ctx.access_node_host, port=self.ctx.access_node_port
        ) as client:
            script_result = await client.execute_script(script=script_object)

            if (not script_result):
                raise ScriptError(script_name=name)
            
            if (len(script_result.value) > 0):
                return utils.convertCadenceDictionaryToPythonDictionary(cadence_dict=script_result)
            else:
                return {}
            

    async def profile_all_accounts(self, program_stage: str = None) -> None:
        """
        Simple function to abstract and automate the characterisation of all configured accounts, i.e., all the one indicated in the "accounts" section of this project's flow.json file. The function require no inputs and returns no data. All results are printed to stdout.
        """
        if (program_stage):
            print(program_stage)
                
        print("|---------------------------------------------------------------------------------------------- |")
        print("| Account       |            Balance                    |                    Storage            |")
        print("|-----------------------------------------------------------------------------------------------|")
        print("|               | default       | available             | capacity              | used          |")
        print("|-----------------------------------------------------------------------------------------------|")
        
        ctx = account_config.AccountConfig()
        accounts = ctx.getAccounts()

        for account_entry in accounts:

            account_balance: dict[str:float] = await self.getAccountBalance(recipient_address=accounts[account_entry])
            account_storage: dict[str:int] = await self.getAccountStorage(recipient_address=accounts[account_entry])

            if (account_entry == "emulator"):
                print(f"|{account_entry}\t|{account_balance["default"]}\t|{account_balance["available"]}\t|{account_storage["capacity"]}\t|{account_storage["used"]}\t|")
                print("|-----------------------------------------------------------------------------------------------|")
            else:
                print(f"|{account_entry}\t|{account_balance["default"]}\t|{account_balance["available"]}\t\t|{account_storage["capacity"]}\t\t|{account_storage["used"]}\t\t|")
                print("|-----------------------------------------------------------------------------------------------|")
        
        print("\n")


    async def profile_all_accounts_csv(self, program_stage: str = None, output_file_path: pathlib.Path = None) -> None:
        """
        This function profiles all configured accounts in the system, i.e., the one indicated in flow.json, but this time printing them in a CSV (comma separated values) to make it easy to import into other tools to do statistical analysis, plot graphs, etc. This version accepts one single string argument to indicate where in the main program the account profiling was done. This function prints the account profiles using the format
        
        <account_name>,<program_stage>,<default_balance(float)>,<available_balance(float)>,<capacity_storage(int)>,<used_storage)int>

        Using one line per account. This function is the only one using the "print" function, therefore, running the main script and forwarding all output to a file (using > or >>), will write all this data in a handy file ready to be imported.

        :param program_state(str): If provided, this item is added to the line describing the current account profile. If not, the whole entry is omitted from the final result
        :param output_file_path (pathlib.Path): If provided, this routine dumps the line to the file and omits the stdout
        """
        ctx = account_config.AccountConfig()
        accounts = ctx.getAccounts()

        # Check if the file pointed by the path exists and proceed accordingly
        if (output_file_path):
            # If a file path was provided
            if (os.path.isfile(output_file_path)):
                # And the file already exists, open it in append mode
                output_stream = open(output_file_path, "+a")
            else:
                # Create a new one
                output_stream = open(output_file_path, "+x")

        for account_entry in accounts:
            # Get account data
            account_balance: dict[str:float] = await self.getAccountBalance(recipient_address=accounts[account_entry])
            account_storage: dict[str:int] = await self.getAccountStorage(recipient_address=accounts[account_entry])
            new_line: str = ""

            # Print the account info in a single line, using the csv format
            if (program_stage != None):
                new_line = f"{program_stage},{account_entry},{account_balance["default"]},{account_balance["available"]},{account_storage["capacity"]},{account_storage["used"]}"
            else:
                new_line = f"{account_entry},{account_balance["default"]},{account_balance["available"]},{account_storage["capacity"]},{account_storage["used"]}"

            if (output_stream):
                # If an output stream is present, dump the new line into it
                output_stream.write(new_line)
            else:
                # Otherwise print it to stdout
                print(new_line)

        # Check if an output stream was created and close it if so
        if (output_stream):
            output_stream.close() 
                
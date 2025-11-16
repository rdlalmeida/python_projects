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
        @param script_name: str - The name of the script to be retrieved and configured.
        @param script_arguments: list - A list with the arguments to set in the script object to execute.

        @return Script If successful, this function returns a configured Script object ready to be executed.
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

        @return bool This function returns True if all the deployed contracts for this project are consistent, False otherwise.
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

        @param votebox_address: str? - If provided, this function gets the list of active election ids for the votebox configured in the address provided. Otherwise, the script gets the list of active election ids from the central votebooth contract instead.

        @return list[int] This function returns the list of active election ids.
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

        @param election_id: int - The election id for the election whose name is to be retrieved
        @param votebox_address: str? - If provided, the script retrieves the election name from the votebox resource. If None is provided, it goes to the votebooth contract.

        @return str The function returns the name of the election with the id provided.
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

        @param election_id: int - The election id for the election whose ballot is to be retrieved
        @param votebox_address: str? - If provided, the script retrieves the election ballot from the votebox resource. If None is provided, it goes to the votebooth contract.

        @returns str The function returns the ballot set to the election with the id provided.
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

        @param election_id: int - The election id for the election whose set of options are to be retrieved.
        @param votebox_address: str? - If provided, the script retrieves the set of election options for the votebox resource. If None is provided, this goes to the votebooth contract.

        @returns dict[int: str] The function returns the set of active options for the election, as a dictionary with id as key and the option text as value.
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

        @param election_id: int - The election id for the election whose election id is to be retrieved.
        @param votebox_address: str? - If provided, the script retrieves the election id from the votebox resource. If None is provided, this goes to the votebooth contract.

        @returns int The function returns the election identifier for the election resource identified by the input.
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
    

    async def getPublicEncryptionKey(self, election_id: int, votebox_address: str = None) -> list[int]:
        """Function to retrieve the public encryption key for the election identified by id provided as argument.

        @param election_id: int - The election id for the election whose public encryption key is to be retrieved.
        @param votebox_address: str? - If provided, the script retrieves the public encryption key from the votebox resource. If None is provided, this goes to the votebooth contract.

        @returns int The function returns the public encryption key for the election identified by the election id provided.
        """
        name = "07_get_public_encryption_key"
        arguments = [cadence.UInt64(election_id)]

        if (votebox_address):
            arguments.append(cadence.Address.from_hex(votebox_address))
        else:
            arguments.append(cadence.Optional(None))

        script_object = self.getScript(script_name=name, script_arguments=arguments)

        public_key_to_return: list[int] = []

        async with flow_client(
            host=self.ctx.access_node_host, port=self.ctx.access_node_port
        ) as client:
            script_result = await client.execute_script(script=script_object)

            if (not script_result):
                raise ScriptError(script_name=name)

            for key_element in script_result.value.value:
                public_key_to_return.append(int(key_element.value.__str__()))

            return public_key_to_return
    

    async def getElectionCapability(self, election_id: int, votebox_address: str = None) -> cadence.Capability:
        """Function to retrieve the capability value configured in the election identified by the id provided as argument.

        @param election_id: int - The election id for the election whose public capability is to be retrieved.
        @param votebox_address: str? - If provided, the script retrieves the public encryption key from a votebox resource. If None is provided, this goes to the votebooth contract.

        @return cadence.Capability This function returns the cadence.Capability-type object configured for the election with the id provided.
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

        @param election_id: int - The election id for the election whose ballot totals are to be retrieved.
        @param votebox_address: str? - If provided, the script retrieved the ballot totals from the votebox resource. If None is provided, this goes to the votebooth contract.

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

        @param election_id: int - The election id for the election whose storage path is to be retrieved.

        @return str Returns a string representation of the storage path retrieved.
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

        @param election_id: int - The election id for the election whose public path is to be retrieved.

        @return str Returns a string representation of the public path retrieved.
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

        @return dict[int: str] This function returns the list of currently active elections in a dictionary with the format {<electionId>: <electionName>}
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

        @param election_id: int - The election id for the election whose ballot option is to be retrieved.
        @param votebox_address: str - The address for the account from where the votebox resource reference is to be retrieved.

        @return str - If there's a ballot submitted for the election id provided, in the votebox for the address provided as well, this function returns the option set in it. Otherwise returns None. 
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

        @param election_id: int - The election id for the election whose ballot id is to be retrieved.
        @param votebox_address: str - The account address from where the votebox resource reference is to be retrieved

        @return int This function returns the ballot identifiers number for the Ballot stored under the election id inside the votebox resource retrieved from the input argument.
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

        @param election_id: int - The election id for the election whose results are to be retrieved.

        @return dict[str: int] If the election identified by the id provided as argument is finalised, this function returns its results in the form of a dictionary, using the format {<electionBallotOptions>: <votesCounted>}. If the election is still ongoing, this function returns None.
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

        @param election_id: int - The election id for the election whose status is to be retrieved.

        @return bool This function returns True if the election has been tallied already, False otherwise.        
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
        

    async def getAccountBalance(self, account_address: str) -> float:
        """Function to retrieve the account balance, in FLOW tokens, of the account whose address is provided as input.

        @param account_address: str - The address of the account whose balance is to be retrieved.

        @return float This function returns the balance amount in FLOW tokens for the account provided.
        """
        name = "17_get_account_balance"
        arguments = [cadence.Address.from_hex(account_address)]

        script_object: Script = self.getScript(script_name=name, script_arguments=arguments)

        async with flow_client(
            host=self.ctx.access_node_host, port=self.ctx.access_node_port
        ) as client:
            script_result = await client.execute_script(script=script_object)

            if (not script_result):
                raise ScriptError(script_name=name)

            return float(script_result.__str__())


    async def getElectionWinner(self, election_id: int) -> dict[str:int]:
        """Function to retrieve the winning option for the election with the identifier provided as argument.

        @param election_id: int - The election identifier for the Election to be processed.

        @return dict[str:int] The function returns a dictionary with the winning option for the election, which can have multiple elements for tied election.
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

        @param election_id: int - The election identifier for the Election to be processed.

        @return list[str] The list of Ballot options, still in its encrypted format
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
            
            if (len(script_result.value) > 0):
                return script_result.value
            else:
                return []
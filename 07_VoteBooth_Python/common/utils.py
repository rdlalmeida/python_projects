import logging
import configparser
import os, sys
import pathlib
from flow_py_sdk import cadence
import datetime

config_path = pathlib.Path(os.getcwd()).joinpath("common", "config.ini")
config = configparser.ConfigParser()
config.read(config_path)


class Utils():
    def __init__(self) -> None:
        super().__init__()
        
    def configureLogging() -> None: 
        """
        Configurator for the logging module
        """
        log_level = config.get("logging", "level")
        log_date = config.get("logging", "datefmt")
        log_format = config.get("logging", "format")

        logging.basicConfig(
            level=log_level,
            datefmt=log_date,
            format=log_format
        )

    def encodeIntArrayToString(input_array: list[int]) -> str:
        """
        Simple function to convert a [int] into the corresponding string using an hexadecimal encoding. This function is to be used to convert encryption keys between strings and [int].

        @param input_array: list[int] - The array of int values, expected in a UInt8 format, i.e., each element within the hex encoding interval [0 - 255]

        @return str This function returns the hex encoding of the input array, as a string.
        """
        for input_element in input_array:
            if (input_element < 0 or input_element > 255):
                raise Exception(f"Unable to convert non {config.get(section="encryption", option="encoding")} value to a character: {input_element}")

        return bytearray(input_array).hex()



    def encodeStringToIntArray(input_string: str) -> list[int]:
        """
        Simple function to convert a input string into an array of int value corresponding to the hex encoding of each of the characters from the input string.
        
        @param input_string - The string to convert into list[int].

        @return list[int] The function return an int array with the numeric value of each character from the input string.
        """

        return list(bytes.fromhex(input_string))


    def convertCadenceDictionaryToPythonDictionary(cadence_dict: cadence.Dictionary) -> dict:
        """Function to abstract the logic of converting a cadence.Dictionary type object into a Python one. I need this because cadence.Dictionaries are composed of cadence.KeyValuePair-type elements and these are a pain to covert into Python-type values.
        
        @param cadence_dict: cadence.Dictionary - The cadence.Dictionary type object to convert.

        @return dict Returns the Python dictionary version of the input argument.
        """
        dictionary_to_return: dict = {}

        for dict_element in cadence_dict.value:
            # The dict_element should be a KeyValuePair object
            dictionary_to_return[dict_element.key.value] = dict_element.value.value

        # Done. Return the converted dictionary
        return dictionary_to_return


    def convertPythonDictionaryToCadenceDictionary(python_dict: dict) -> cadence.Dictionary:
        """Function to abstract the logic of converting a Python dictionary type object into a cadence.Dictionary one. Though the cadence.Dictionary class does provide some helpers in this sense, these are quite rudimentary and prone to problems. This routine should solve all those issues.

        @param python_dict: dict - The Python-type dictionary to convert.

        @return cadence.Dictionary Returns the converted, cadence.Dictionary type object. 
        """
        # I need to convert each entry of the input dictionary into a list of KeyValuePair
        cadence_input: list[cadence.KeyValuePair] = []

        for python_element in python_dict:
            cadence_input.append(cadence.KeyValuePair(key=python_element, value=python_dict[python_element]))

        # Convert the list of KeyValuePairs into a cadence.Dictionary and return it
        return cadence.Dictionary(value=cadence_input)


    def processTransactionData(fees_deducted_events: list[dict], tokens_withdrawn_events: list[dict], elapsed_time: int, tx_description: str, output_file_path: pathlib.Path) -> None:
        """Function to automate the processing of transaction metrics that are interesting to characterise the system performance. These metrics are retrieved from the system through events. This function continues the processing by retrieving the data from the events, format it in a handy .csv format, and appends it to a file whose path is provided as argument. The idea is to have a nice data feed to build graphs and do all sort of post analysis.
        
        :param flow_fees_events (list[dict]): A list with all the FlowFees.FeesDeducted events to retrieve the gas paid in the transaction and the execution effort (computational effort) required by the computation. 
        :param tokens_withdrawn_events (list[dict]): A list with all the FungibleToken.Withdrawn events related to the transaction to retrieve additional gas expenditure details.
        :param elapsed_time (int): The time that the transaction required to fully execute, in nanoseconds.
        :param tx_description (str): A descriptor for the data set, namely, a summary of what the transaction did, e.g., "create ballot", "tally election", etc.
        :param output_file_path (pathlib.Path): A pathlib.Path object to the file to be used to write the analysis data.
        """
        # Test if the file pointed by the Path provided exists, create a new one if does not
        if (os.path.isfile(output_file_path)):
            # If the file already exists, open it in append mode
            output_stream = open(output_file_path, "+a")
        else:
            # If not, create a new one
            output_stream = open(output_file_path, "+x")
            # And write the headers in the first line
            new_line: str = f"Transaction Descriptor, Timestamp, Tx Execution Time (ns), Fee Amount (FLOW), Execution Effort, Inclusion Effort, Tokens Withdrawn (FLOW), From Account, Balance After (FLOW)\n"
            output_stream.write(new_line)


        # Process the FlowFees.FeesDeducted and FungibleToken.Withdrawn events at the same time since these are always emitted simultaneously. In case they aren't, I created this
        # clever loop that omits missing events but guarantees that each pair of events is properly processed
        for i in range(0,max(len(fees_deducted_events), len(tokens_withdrawn_events))):
            new_line: str = ""
            if (fees_deducted_events[i]):
                new_line = f"{tx_description},{datetime.datetime.now().strftime("%d-%m-%yT%H:%M:%S")}, {elapsed_time},{fees_deducted_events[i]["amount"]},{fees_deducted_events[i]["execution_effort"]},{fees_deducted_events[i]["inclusion_effort"]},"
            else:
                new_line = f"{tx_description},{datetime.datetime.now().strftime("%d-%m-%yT%H:%M:%S")},{elapsed_time},,,,"

            if (tokens_withdrawn_events[i]):
                new_line += f"{tokens_withdrawn_events[i]["amount"]},{tokens_withdrawn_events[i]["from"]},{tokens_withdrawn_events[i]["balance_after"]}\n"
            else:
                new_line += f",,\n"
            
            # Write the line to the stream and move to the next pair
            output_stream.write(new_line)
        
        # All done. Close the output stream before exiting
        output_stream.close()


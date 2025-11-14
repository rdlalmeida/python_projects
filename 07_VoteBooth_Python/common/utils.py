import logging
import configparser
import os
import pathlib
from flow_py_sdk import cadence

config_path = pathlib.Path(os.getcwd()).joinpath("common", "config.ini")
config = configparser.ConfigParser()
config.read(config_path)

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
            raise Exception(f"Unable to convert non UTF-8 value to a character: {input_element}")

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

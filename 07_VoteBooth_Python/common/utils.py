import logging
import configparser
import os
import pathlib

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
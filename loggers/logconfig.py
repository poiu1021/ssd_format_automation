import logging
import os
import yaml


def bring_yaml():
    """Read the configuration file"""
    try:
        with open('/home/hkim/sd_ssd_program/config.yaml', 'r') as f:
            data = yaml.safe_load(f)
        return data
    except FileNotFoundError:
        print("[ERROR]: File 'config.yaml not found.")
        return None
    except yaml.YAMLError as e:
        print(f"[ERROR]: An error occurred while parsing YAML: {e}")
        return None


def create_logger(dirpath: str, filename: str, name: str):
    """
    Create a logger with the path and name
    :param dirpath: Path to the logger
    :param filename: Logger name
    :param name: Logger nane
    :return: Logger
    """
    try:
        if not os.path.exists(dirpath):
            os.mkdir(dirpath)
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s : %(message)s')
        file_handler = logging.FileHandler(f'{dirpath}/{filename}', mode='a')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        return logger
    except PermissionError as e:
        print(f"[ERROR]: Permission denied : {e}")
        return None


def log_data(data: str, logger):
    """Log message to the logger"""
    logger.log(logging.DEBUG, data)

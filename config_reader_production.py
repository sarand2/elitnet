from heapq import nlargest
from operator import itemgetter
import yaml
import logging
import os
import subprocess


class ConfigurationReader:
    configuration_file = "configuration/scriptConfig.yaml"

    @staticmethod
    def databaseConfiguration():
        with open(ConfigurationReader.configuration_file, 'r') as config_file:
            info = yaml.load(config_file)
            ip_address = info['Database']['IP adress']
            port = info['Database']['Port']
            namespace = info['Database']['Namespace']
            db_set = info['Database']['Set']
            return ip_address, port, namespace, db_set
    @staticmethod
    def setup_logging(logger, default_path='logging.yaml', default_level=logging.INFO, env_key='LOG_CFG'):
        path = default_path
        value = os.getenv(env_key, None)
        if value:
            path = value
        if os.path.exists(path):
            with open(path, 'rt') as f:
                config = yaml.safe_load(f.read())
            logging.config.dictConfig(config)
        else:
            logging.basicConfig(level=default_level)
    @staticmethod
    def svmParameters():
        with open(ConfigurationReader.configuration_file, 'r') as config_file:
            info = yaml.load(config_file)
            file = info['Support vector machine']['Parameter file']
            return file

    @staticmethod
    def scriptExecutionInfo():
        with open(ConfigurationReader.configuration_file, 'r') as config_file:
            info = yaml.load(config_file)
            attack_time = info['Custom script']['Script execution interval(seconds)']
            attack_percent = info['Custom script']['Execute script after (percent alarms per interval)']
            return attack_time, attack_percent

    @staticmethod
    def higherScriptExecution():
        with open(ConfigurationReader.configuration_file, 'r') as config_file:
            info = yaml.load(config_file)
            script_counts = info['Custom script']['Execute higher level script after first runs for (fixed times)']
            return script_counts



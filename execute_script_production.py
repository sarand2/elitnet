import yaml
import subprocess


class ScriptExecutor():

    @staticmethod
    def execute_attack_script():
        with open("configuration/scriptConfig.yaml", 'r') as ymlfile:
            info = yaml.load(ymlfile)  # Load content of YAML file to yaml object
            #print(info['Custom script']['Execute script after attack alarm exceeds (alarms per 10 seconds)'])
            program = info['Custom script']['Script folder'] + '/' + info['Custom script']['Script file']
            subprocess.call(['python', program])

    @staticmethod
    def execute_higher_level_script():
        with open("configuration/scriptConfig.yaml", 'r') as ymlfile:
            info = yaml.load(ymlfile)  # Load content of YAML file to yaml object
            # print(info['Custom script']['Execute script after attack alarm exceeds (alarms per 10 seconds)'])
            program = info['Custom script']['Higher script folder'] + '/' + info['Custom script']['Higher script file']
            subprocess.call(['python', program])

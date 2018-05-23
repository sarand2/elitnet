import yaml
import io
import inspect
import sys
import logging


class Executor():

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def change_alarm_script(self, script_file, script_folder, alarm_limit):
        data = \
            {
            'Custom script': {'Script file': script_file,
                              'Script folder': script_folder,
                              'Execute script after attack alarm exceeds (alarms per 10 seconds)': alarm_limit,
                              }
           }
        with io.open('scriptConfig.yaml', 'w', encoding='utf8') as outfile:
            try:
                yaml.dump(data, outfile, default_flow_style=False, allow_unicode=True)
            except yaml.YAMLError as e:
                self.logger.error('Failed to write to scriptConfig.yaml file. ' + 'Exception message: ' + str(e))

    def execute_alarm_script(self):
        with open('scriptConfig.yaml', 'r') as stream:
            try:
                data_loaded = yaml.load(stream)
            except yaml.YAMLError as e:
                self.logger.error('Failed to read scriptConfig.yaml file. ' + 'Exception message: ' + str(e))

        try:
            sys.path.append(data_loaded['Custom script']['Script folder'])
            script_file = data_loaded['Custom script']['Script file']
            imported_script = __import__(script_file)
            for name, obj in inspect.getmembers(imported_script):
                if inspect.isclass(obj):
                    execution_script = obj()
                    break
        except Exception as e:
            self.logger.error('Failed to import/start custom alert script' + (data_loaded['Custom script']['Script file']) +
                              'from ' + data_loaded['Custom script']['Script file'] + 'Exception message: ' + str(e))
object = Executor()
object.execute_alarm_script()
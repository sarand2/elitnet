from multiprocessing import Process, Queue
from kalman_production import *
from execute_script_production import ScriptExecutor
from AeroSpike_production import AerospikeClient
from sniffer_production import *
import queue as pythonQueue
import datetime
import logging
import logging.config
import yaml
import threading
from pympler.tracker import SummaryTracker
import ipaddress

class SnifferProcessClass(object):
    def __init__(self, queue, sniffer, analyzer):
        self.queue = queue
        self.sniffer = sniffer
        self.analyzer = analyzer

    def run(self):
        self.sniffer.run_sniffer(self.queue)


class HrpiProcessClass(object):
    def __init__(self, lock, queue, sniffer, analyzer, AerospikeClient):
        self.lock = lock
        self.queue = queue
        self.sniffer = sniffer
        self.analyzer = analyzer
        self.timestamp = ""
        self.logger = logging.getLogger(__name__)
        self.attack_time, self.attack_percent = ConfigurationReader.scriptExecutionInfo()
        self.first_value = 0
        self.attack_alert = 0
        self.Aero = AerospikeClient

        self.attack_alert_limit = ((self.attack_time * 10) / 100) * self.attack_percent
        self.custom_script_counter = ConfigurationReader.higherScriptExecution()
        self.script_execution_counter = self.custom_script_counter
        self.IsAttack = 0
        self.selftracker = SummaryTracker()

    def get_first_datetime(self):
        while(True):
            if (self.queue.empty()):
                continue
            else:
                self.lock.acquire()
                value = self.queue.get(False)
                self.lock.release()
                self.datetimeValue = value.get_datetime()
                self.datetime_limit = self.datetimeValue + datetime.timedelta(0, self.attack_time)
                print("Pradzios datetime: {0}, limitas: {1}".format(self.datetimeValue, self.datetime_limit))
                break

    def run(self):
        while True:
            try:
                if (self.queue.empty()):
                    continue
                else:
                    self.lock.acquire()
                    value = self.queue.get(False)
                    self.lock.release()
                    #print(value.return_data())
                #print(self.queue.qsize())
                if self.timestamp == value.get_timestamp():
                   # print("timestamp={0}, value.timestamp ={1}, dedama i sarasa".format(self.timestamp, sniffer.get_timestamp(value)))
                    self.sniffer.requests.add_request(value)
                else:
                    #print("timestamp {0} value.timestamp ={1}, nesutampa, spausdinama".format(self.timestamp, sniffer.get_timestamp(value)))
                    if self.sniffer.requests.request_count() > 0:
                        requests_per_ip, request_count = sniffer.requests.return_request_normal_run()
                        mili_to_kalman = sniffer.requests.get_milisecond_timestamp()
                        overallCount = sniffer.requests.overall_request_counter
                        dictReturn = self.analyzer.kalman_run_normal_parallel(request_count, requests_per_ip, mili_to_kalman, overallCount)
                        milisecond = dictReturn['TimeStamp']
                        alert= dictReturn['alert']
                        Y =  dictReturn['Y']
                        counter = dictReturn['Counter']
                        unixtime = self.sniffer.requests.get_unix_timestamp()
                        self.Aero.loadData(self.sniffer.requests.get_unix_timestamp(), Y, alert, self.IsAttack)                       
                        #self.Aero.put_data(milisecond, alert, Y, counter)
                        self.Aero.put_ip_table(sniffer.get_max_ips())
                        #print("Get_max_ips = {0}".sniffer.get_max_ips())
                        #print("ALERT = {0}".format(alert))
                        self.attack_alert += alert
                        #print("Laiko {0} requestai: ".format(self.timestamp))
                        #self.sniffer.requests.print_all_requests()

                    self.timestamp = value.get_timestamp()

                    while (self.datetimeValue < value.get_datetime()):
                        self.datetimeValue += datetime.timedelta(0, 0, 100000)
                    #print("Datetime + kito requesto laiko skirtumas: {0}".format(self.datetimeValue))

                    if(self.datetimeValue >=  self.datetime_limit):
                        print("Datetime {0} virsijo limita {1} ".format(self.datetimeValue, self.datetime_limit))
                        if(self.attack_alert >= self.attack_alert_limit):
                            #ScriptExecutor.execute_attack_script()
                            self.script_execution_counter -= 1
                            if(self.script_execution_counter <= 1):
                                #ScriptExecutor.execute_higher_level_script()
                                self.IsAttack = 1
                                self.script_execution_counter = self.custom_script_counter
                        else:
                            self.IsAttack = 0

                        self.attack_alert = 0
                        self.datetime_limit = self.datetimeValue + datetime.timedelta(0, self.attack_time)
                        print("Naujas datetime limitas: {0} ".format(self.datetime_limit))

                        print("naujas timestamp =  {0}, sarasas isvalomas ir pridedama reiksme su : ".format(self.timestamp))
                    #self.selftracker.print_diff()
                    self.sniffer.requests.clear_list()
                    #print(str("Requestu masyvo dydis:") + str(sniffer.requests.return_size()))
                    #self.sniffer.requests.clear_ip_list()
                    self.sniffer.requests.add_request(value)
            except pythonQueue.Empty:
                self.lock.release()
                self.logger.debug('Packet queue is empty')
            except Exception as e:
                logging.error('Running loop failed. ' + 'Exception message: ' + str(repr(e)))
                #time.sleep(0.3)

def setup_logging(default_path='logging.yaml', default_level=logging.INFO):
    try:
        path = default_path
        if os.path.exists(path):
            with open(path, 'rt') as f:
                config = yaml.safe_load(f.read())
            logging.config.dictConfig(config)
        else:
            logging.basicConfig(level=default_level)
    except Exception as e:
        print('Setting up the logger failed. Exception: ' + str(repr(e)))

if __name__ == '__main__':
    try:
        setup_logging()
        logger = logging.getLogger(__name__)
        logger.info('Started')
        queue = mp.Queue()
        lock = threading.Lock()
        Aero = AerospikeClient()
        Aero.connect()
        sniffer = Sniffer(lock, Aero)
        analyzer = HRPIAnalyzer()

        sniff = SnifferProcessClass(queue, sniffer, analyzer)
        calculate = HrpiProcessClass(lock, queue, sniffer, analyzer, Aero)

        processSniff = Process(target=sniff.run)
        processSniff.start()
        calculate.get_first_datetime()
        processCalculate = Process(target=calculate.run)
        processCalculate.start()

        processSniff.join()
        processCalculate.join()
    except Exception as e:
        logger.error('Primary process initialization failed. ', exc_info=True)


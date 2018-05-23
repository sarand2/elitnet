import logging
import aerospike
from config_reader_production import ConfigurationReader
import ipaddress

class AerospikeClient:

    # Configure the client
    def __init__(self):
        ip_address, port, namespace, db_set = ConfigurationReader.databaseConfiguration()
        self.config = {'hosts': [(ip_address, port)]}
        self.ip_address = ip_address
        self.port = port
        self.namespace = namespace
        self.db_set = db_set
        self.logger = logging.getLogger(__name__)

    # Create a client and connect it to the cluster
    def connect(self):
        try:
            self.client = aerospike.client(self.config).connect()
        except Exception as e:
            import sys
            self.logger.error('Failed to connect to the cluster with ' + str(self.config['hosts']) + 'Exception message: ' + str(e))

    def put_ip_table(self, dictionary):
        for keyDict, value in dictionary.items():
            bins = {
                    'IP': keyDict,
                    'Count': value
                   }
            key = (self.namespace, self.db_set, keyDict)
            try:
                self.client.put(key, bins)
            except Exception as e:
                self.logger.error('Inserting value failed with host: ' + str(self.config['hosts']) + ', KEY=' + str(key) + 'Exception message: ' + str(e))

    def put_data(self, hrpi_time, prediction, hrpi, counter):
        bins = {
            'HRPI': hrpi,
            'Prediction': prediction,
            'Counter': counter
        }
        key = (self.namespace, self.db_set, hrpi_time)
        try:
            self.client.put(key, bins)
        except Exception as e:
            self.logger.error('Inserting value failed with host: ' + str(self.config['hosts']) + ', KEY=' + str(
                key) + 'Exception message: ' + str(e))

    def loadData(self, timeStamp, hrpi, eval, attack):
        namespace = "firewall"
        set = "graph"
        hrpiDict = "data"
        evalDict = "eval"
        attackDict = "attack"
        print("timeStamp=",timeStamp,"hrpi=",hrpi)     
        try:
             self.client.put((namespace, set, timeStamp), {
                hrpiDict: hrpi, evalDict: eval, attackDict: attack
            },
                       policy={'key': aerospike.POLICY_KEY_SEND})
        except Exception as e:
            import sys
            #print("error: {0}".format(e), file=sys.stderr)

    def incrementData(self, set, key, dict):
        print("Incrementing: ", key, " : ", dict)
        try:
            #print("Set=",set,"Key=",key,"Dict=",dict)
            self.client.increment(('firewall', 'ip_table', key), dict, 1,
                             policy={'key': aerospike.POLICY_KEY_SEND})
            test = self.client.get(('firewall','ip_table', key))
            print(test)
        except Exception as e:
            import sys
            #print("error: {0}".format(e), file=sys.stderr)
   
    def getData(self, timeFrom, timeTo):
        try:
            keys = []
            for time in range(timeFrom, timeTo):
                 #print(time)
                 key = ('firewall', 'graph', time)             
                 keys.append(key)
                 #print(key)
            records = self.client.get_many(keys)    
                     
            #tkey = ('firewall', 'graph', '15269351967')
            #test = self.client.get(('firewall', 'graph', 15269373319))[2].get('data'))
            #print("---")
            #print(test)
            #print("---")
           
          
          #  for record in records:
                 #print(record)
               #  print(str(record[2].get('data')))
               #  print(str(record[2].get('eval')))
                 #returnList['hrpi'].append(str(record[2].get('data')))
                 #returnList['evaluation'].append(record[2]['eval'])               
            return records
        except Exception as e:
            import sys
            self.logger.error('Error loading batch HRPI data from host: ' + str(self.config['hosts']) + '. Exception message: ' + str(e))

    def getDataIP(self, timeFrom, timeTo):
        try:
            keys = []
            for time in range(timeFrom, timeTo+1):
                key = ('firewall', 'ip_table', time)
                keys.append(key)
            records = self.client.get_many(keys)
            return records
        except Exception as e:
            import sys
            self.logger.error('Error loading batch HRPI data from host: ' + str(self.config['hosts']) + '. Exception message: ' + str(e))
         
    def getHistoryData(self, timeFrom, timeTo):
        try:
            keys = []
            for time in range(timeFrom, timeTo):
                 #print(time)
                 key = ('firewall', 'graph', time)
                 #print(key)           
                 keys.append(key)
                 #print(key)
            records = self.client.get_many(keys)    
                     
            #tkey = ('firewall', 'graph', '15269351967')
            #test = self.client.get(('firewall', 'graph', 15269373319))[2].get('data'))
            #print("---")
            #print(test)
            #print("---")
           
          
          #  for record in records:
                 #print(record)
               #  print(str(record[2].get('data')))
               #  print(str(record[2].get('eval')))
                 #returnList['hrpi'].append(str(record[2].get('data')))
                 #returnList['evaluation'].append(record[2]['eval'])               
            return records
        except Exception as e:
            import sys
            self.logger.error('Error loading batch HRPI data from host: ' + str(self.config['hosts']) + '. Exception message: ' + str(e))
       


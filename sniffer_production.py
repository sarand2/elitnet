from scapy.all import *
import multiprocessing as mp
from heapq import nlargest
import datetime
from operator import itemgetter
import logging
import ipaddress

class HttpRequest:
    timestamp = ""
    source_ip = ""
    sender_port = ""
    destination_ip = ""
    destination_port = ""
    http_method = ""
    http_protocol = ""
    http_url = ""
    unix_stamp = ""
    milisecond=10
    datetime = ""

    def __init__(self, time_stamp, source_ip, destination_ip, mili, datetimeValue, unix_time_stamp):
        self.timestamp = time_stamp
        self.source_ip = source_ip
        self.destination_ip = destination_ip
        self.milisecond = mili
        self.datetime = datetimeValue
        self.unix_stamp = unix_time_stamp

    def __str__(self):
        return "Timestamp {0} Source: {1} SenderPort: {2} Destination: {3} DestinationPort: {4}" \
            .format(self.timestamp, self.source_ip, self.sender_port, self.destination_ip, self.destination_port)

    def return_source_ip(self):
        return self.source_ip

    def return_milisecond(self):
        return self.milisecond

    def get_timestamp(self):
        return self.timestamp

    def get_unix_timestamp(self):
        return self.unix_stamp

    def get_datetime(self):
        return self.datetime

    def return_data(self):
        return '{0};{1} ------> {2}' \
                .format(self.timestamp, self.source_ip, self.destination_ip)

class RequestList:

    httpRequestList = []
    requests_count_taken = 0

    def __init__(self):
        self.ip_interval_table = {}
        self.overall_request_counter = 0

    def clear_list(self):
        self.httpRequestList = []

    def return_size(self):
        return len(self.httpRequestList)

    def add_request(self, http_request):
        self.httpRequestList.append(http_request)

    def print_all_requests(self):
        for request in self.httpRequestList:
            print(request.return_data())

    def request_count(self):
        return len(self.httpRequestList)

    def get_timestamp(self):
        if(len(self.httpRequestList) > 0):
            return self.httpRequestList[0].time_stamp

    def get_milisecond_timestamp(self):
        if(len(self.httpRequestList) > 0):
            return self.httpRequestList[0].milisecond

    def get_unix_timestamp(self):
        if (len(self.httpRequestList) > 0):
            return self.httpRequestList[0].unix_stamp

    def clear_ip_list(self):
        self.ip_interval_table = {}
        
    def return_request_normal_run(self):
        requests_per_ip = {}
        request_count = 0
        self.overall_request_counter = len(self.httpRequestList)
        for request in self.httpRequestList:
         key = request.return_source_ip()
         if key in self.ip_interval_table.keys():
           self.ip_interval_table[key] += 1
         else:
           self.ip_interval_table[key] = 1
         request_count += 1
         if key in requests_per_ip.keys():
           requests_per_ip[key] += 1
         else:
           requests_per_ip[key] = 1

        return requests_per_ip, request_count


class Sniffer:

    def __init__(self, lock, AerospikeClient):
        self.lock = lock
        self.requests = RequestList()
        self.packet_queue = mp.Queue()
        self.Aero = AerospikeClient
        self.logger = logging.getLogger(__name__)

    def get_url(self, packet):
        pkt = packet.getlayer(Raw).load

    def get_method(self, packet):
        pkt = packet.getlayer(Raw).load

    def get_protocol(self, packet):
        pkt = packet.summary()

    def get_sender_port(self, packet):
        senderPort = packet[TCP].sport
        return senderPort

    def get_destination_port(self, packet):
        dstPort = packet[TCP].dport
        return dstPort

    def get_source_ip(self, packet):
        sourceIpAddress = packet[IP].src
        return sourceIpAddress

    def get_destination_ip(self, packet):
        destinationIpAddress = packet[IP].dst
        return destinationIpAddress

    def get_timestamp(self, packet):
        miliseconds  = str(packet.time - int(packet.time))[2]
        packetTime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(packet.time))
        packetTime += ':' + miliseconds
        return packetTime

    def get_unix_timestamp_w_miliseconds(self, packet):
        return int(packet.time * 10 )

    def get_packet_time_data(self, packet):
        try:
            year = int(time.strftime('%Y', time.localtime(packet.time)))
            month = int(time.strftime('%m', time.localtime(packet.time)))
            day = int(time.strftime('%d', time.localtime(packet.time)))
            hour = int(time.strftime('%H', time.localtime(packet.time)))
            minute = int(time.strftime('%M', time.localtime(packet.time)))
            second = int(time.strftime('%S', time.localtime(packet.time)))
            miliseconds = str(packet.time - int(packet.time))[2]
            milisecond_put = int(miliseconds) * 100000+1
            timeReturn = datetime.datetime(year, month, day, hour, minute, second, milisecond_put)
            return timeReturn
        except Exception as e:
            self.logger.error('Getting packet datetime failed. ' + 'Exception message: ' + str(e))

    def get_milisecond_timestamp(self, packet):
        miliseconds = str(packet.time - int(packet.time))[2]
        packetTime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(packet.time))
        packetTime += ':' + miliseconds
        return packetTime

    def get_first_milisecond(self):
        return int(self.requests.first_milisecond())

    def get_max_ips(self):
        dictionary = {}
        for ip, count in nlargest(10, self.requests.ip_interval_table.items(), key=itemgetter(1)):
            dictionary[ip] = count
        return dictionary

    def run_sniffer(self, queue):
        self.packet_queue = queue
        try:
            sniff(iface='enp2s0', prn=self.packet_log_run, store=0)
        except Exception as e:
            self.logger.error('Sniff initialization failed. ' + 'Exception message: ' + str(e))

    def packet_log_run(self, pkt):
        try:
            #The packet index
            global packet_no
            if pkt.haslayer('TCP') and pkt.getlayer('TCP') and pkt.haslayer(Raw):
                packet_content = pkt.getlayer(Raw).load
                if "GET".encode() in packet_content:
                    timestamp = self.get_timestamp(pkt)
                    source_ip = self.get_source_ip(pkt)
                    destination_ip = self.get_destination_ip(pkt)
                    milisecond_stamp = self.get_milisecond_timestamp(pkt)
                    datetimeValue = self.get_packet_time_data(pkt)
                    unixstamp = self.get_unix_timestamp_w_miliseconds(pkt)
                    single_request = HttpRequest(timestamp, source_ip, destination_ip, milisecond_stamp, datetimeValue, unixstamp)
                    self.Aero.incrementData('ip_table', single_request.get_unix_timestamp(), str(int(ipaddress.IPv4Address(source_ip))))                   
                    self.lock.acquire()
                    self.packet_queue.put(single_request)
                    self.lock.release()
        except Exception as e:
           
            self.logger.error('Analyzing packet failed. ' + 'Exception message: ' + str(e))


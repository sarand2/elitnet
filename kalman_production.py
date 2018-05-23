import numpy as np
from numpy.linalg import inv
from sklearn.externals import joblib
from AeroSpike_production import AerospikeClient
import logging
from config_reader_production import ConfigurationReader


class HRPIAnalyzer:

    def __init__(self):
        try:
            self.logger = logging.getLogger(__name__)
            self.N = 3                                 # fixed filter lag
            self.X = np.array([[0], [0], [0]])         # initial state vector
            self.Xhat = self.X                         # initial state estimate

            self.P = np.array([[1, 0, 0],
                               [0, 1, 0],
                               [0, 0, 1]])             # initial error covariance
            self.Ce = 1                                # measurement(observation) error(noise) covariance
            self.Cw = np.array([[1, 0, 0],
                                [0, 1, 0],
                                [0, 0, 1]]) * 0.0001   # process(state) error(noise) covariance

            self.PCol = np.zeros((3, 3, self.N + 1))   # additional covariance matrices for 3 step fixed lag
            self.PColOld = np.zeros((3, 3, self.N + 1))
            self.PSmooth = np.zeros((3, 3, self. N + 1))
            self.PSmoothOld = np.zeros((3, 3, self.N + 1))
            self.eye = np.eye(3, dtype=int)

            self.ip_counter = 0

            self.Y_run = np.ndarray(shape=(1, 4), dtype=float)
            self.get_run_primary()
            self.Support_vector_machine = self.load_parameters()

            self.AerospikeClient = AerospikeClient()
            self.AerospikeClient.connect()
        except Exception as e:
            self.logger.error('Failed to start HRPI analyzer ' + 'Exception message: ' + str(e))

    def load_parameters(self, file='/home/ubuntu/Desktop/CustomScriptFolder/parameters/trained_parameters.pkl'):
        try:
            file = ConfigurationReader.svmParameters()
            return joblib.load(file)
        except Exception as e:
            self.logger.error('Failed to load SVM parameters' + 'Exception message: ' + str(e))

    def kalman_run_normal_parallel(self, requestCount, requestsPerIp, milisecond, overall_count):
        try:
            #request_count, requests_per_ip, mili_to_kalman, overallCount)
            self.get_current_run_hrpi_normal_parallel(self.Y_run, requestCount, requestsPerIp)
            H = np.matrix([self.Y_run[0][2], self.Y_run[0][1], self.Y_run[0][0]])
            # innovation vector
            Inn = self.Y_run[0][3] - H.dot(self.Xhat)
            # covariance of innovation
            S = H.dot(self.P).dot(H.T) + self.Ce
            # kalman gain
            K = self.P.dot(H.T).dot(inv(S))
            # update the estimate from currrent data
            self.Xhat = self.Xhat + K.dot(Inn)
            XhatSmooth = self.Xhat
            # covariance of estimation error
            self.PColOld[:, :, 1] = self.P
            self.PSmoothOld[:, :, 1] = self.P
            self.P = (self.eye - K.dot(H)).dot(self.P) + self.Cw
            # apply fixed 3 step lag
            for i in range(1, self.N):
                KSmooth = self.PColOld[:, :, i].dot(H.T).dot(inv(S))
                self.PSmooth[:, :, i + 1] = self.PSmoothOld[:, :, i] - self.PColOld[:, :, i].dot(H.T).dot(
                    KSmooth.T)
                self.PCol[:, :, i + 1] = self.PColOld[:, :, i].dot((self.eye - K.dot(H)).T)
                XhatSmooth = XhatSmooth + KSmooth.dot(Inn)
            # update for the next step
            self.PSmoothOld = self.PSmooth
            self.PColOld = self.PCol
            prediction_data = XhatSmooth.reshape(1, -1)
            prediction = self.Support_vector_machine.predict(prediction_data)
            dictReturn = {'TimeStamp': milisecond, 'alert': int(prediction), 'Y': self.Y_run[0][3], 'Counter': overall_count}
            return dictReturn
        except Exception as e:
            self.logger.error('Kalman filter failed. ' + 'Exception message: ' + str(e))

    @staticmethod
    def calculate_hrpi(requests_per_ip, request_count):
        hrpi = 0
        if request_count > 0:
            for request in requests_per_ip.values():
                p = (request / request_count)
                hrpi += -p * np.log2(p)
        return hrpi

    def get_run_primary(self):
        self.Y_run[0][2] = 4.75
        self.Y_run[0][1] = 4.75
        self.Y_run[0][0] = 4.75

    def get_current_run_hrpi_normal_parallel(self, Y, request_count, requests_per_ip):
        for t in range(1, 4):
            Y[0][t - 1] = Y[0][t]
        #requests_per_ip, request_count = sniffer.requests.return_request_normal_run()
        Y[0][3] = self.calculate_hrpi(requests_per_ip, request_count)


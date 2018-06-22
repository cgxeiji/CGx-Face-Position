from __future__ import print_function
import socket
import json
import threading
import time

class _NetSender(threading.Thread):
    def __init__(self, client):
        threading.Thread.__init__(self)
        self.client = client
        self.running = False
        self.send_available = False
        self.data = ""
    
    def run(self):
        self.running = True
        while self.running:
            if self.send_available:
                self.send_available = False
                self.client.send(self.data)

    def send(self, data):
        self.data = data
        self.send_available = True

    def stop(self):
        self.running = False


class _NetTraffic(threading.Thread):
    def __init__(self, socket):
        threading.Thread.__init__(self)
        self.socket = socket
        self.size = 1024
        self.running = False
        self.client = None
        self.available = False
        self.position = (0, 0, 0, 0)

    def run(self):
        self.running = True
        while self.running:
            print("Awaiting client...")
            self.client, address = self.socket.accept()
            print("Client [{}] has connected!".format(address))
            while self.running:
                if not self.available:
                    self.data = ''
                    try:
                        self.data = self.client.recv(self.size).decode('UTF-8')
                    except:
                        self.client = None
                        break
                    self.available = True
                    if self.data == 'give':
                        text = "{},{},{},{}".format(self.position[0], self.position[1], self.position[2], self.position[3])
                        text += '\n'
                        self.client.send(text.encode('UTF-8'))
                        self.available = False
                        #time.sleep(0.05)

    def get_client(self):
        return self.client

    def get_data(self):
        self.available = False
        return self.data

    def is_available(self):
        return self.available

    def stop(self):
        print("Stopping client")
        self.running = False
        if self.client != None:
            self.client.close()
        else:
            _socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            _socket.connect(('localhost', 5111))
            _socket.close()


class NetManager:
    def __init__(self):
        self.host = 'localhost'
        self.port = 5111
        self.backlog = 5
        self.client_available = False
        
        
    def start(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((self.host, self.port))
        self.socket.listen(self.backlog)
        self.traffic = _NetTraffic(self.socket)
        self.traffic.start()

    def is_available(self):
        return self.traffic.is_available()

    def get_data(self):
        return self.traffic.get_data()

    def set_position(self, x, y, z, a):
        self.traffic.position = (x, y, z, a)

    def get_data(self):
        (x, y, z, a) = self.traffic.position
        return "({:.2f}, {:.2f}, {:.2f})[{:.2f}]".format(x, y, z, a)

    def stop(self):
        self.traffic.stop()
        self.traffic.join()
        self.socket.close()
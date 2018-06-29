from __future__ import print_function
import socket
import json
import threading
import time
import select

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
    def __init__(self, server, host, port):
        threading.Thread.__init__(self)
        self.connection_list = []
        self.server = server
        self.size = 4096
        self.running = False
        self.client = None
        self.available = False
        self.position = (0, 0, 0, 0)
        self.host = host
        self.port = port

    def run(self):
        self.running = True
        while self.running:
            read_sockets, write_sockets, error_sockets = select.select(self.connection_list, [], [])

            for _socket in read_sockets:
                if _socket == self.server:
                    client, address = self.server.accept()
                    self.connection_list.append(client)
                    print("Client [{}] has connected!".format(address))
                else:
                    try:
                        self.data = ''
                        self.data = _socket.recv(self.size).decode('UTF-8')
                        self.available = True

                        if self.data == 'give':
                            text = "{},{},{},{}".format(self.position[0], self.position[1], self.position[2], self.position[3])
                            text += '\n'
                            _socket.send(text.encode('UTF-8'))
                            self.available = False
                    except:
                        print("Client [{}] has disconnected!".format(1))
                        _socket.close()
                        self.connection_list.remove(_socket)
                        continue

    def get_client(self):
        return self.client

    def get_data(self):
        self.available = False
        return self.data

    def is_available(self):
        return self.available

    def send(self, msg):
        for _socket in self.connection_list:
            _socket.send(msg.encode('UTF-8'))

    def stop(self):
        print("Stopping client")
        self.running = False
        if self.client != None:
            self.client.close()
        else:
            _socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            _socket.connect((self.host, self.port))
            _socket.close()


class NetManager:
    def __init__(self, host='', port=''):
        self.connection_list = []
        self.buffer_size = 4096

        if host == '':
            self.host = socket.gethostname()#'192.168.0.37'
        else:
            self.host = host
        if port == '':
            self.port = 5111
        else:
            self.port = port
        self.backlog = 5
        self.client_available = False
        
        
    def start(self):
        try:
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server.bind((self.host, self.port))
            self.server.listen(self.backlog)
            print(socket.gethostname())
            self.traffic = _NetTraffic(self.server, self.host, self.port)
            self.traffic.start()
            self.enabled = True
            print("Started server at [{}:{}]".format(self.host, self.port))
        except:
            print("Could not open {}:{}".format(self.host, self.port))
            self.enabled = False

    def is_available(self):
        return self.traffic.is_available()

    def get_data(self):
        return self.traffic.get_data()

    def set_position(self, x, y, z, a):
        if self.enabled:
            self.traffic.position = (x, y, z, a)

    def get_data(self):
        (x, y, z, a) = self.traffic.position
        return "({:.2f}, {:.2f}, {:.2f})[{:.2f}]".format(x, y, z, a)

    def get_client(self):
        if self.enabled:
            return self.traffic.get_client()
        else:
            return None

    def send(self, msg):
        if self.enabled:
            self.traffic.send(msg)

    def stop(self):
        if self.enabled:
            self.traffic.stop()
            self.traffic.join()
            self.socket.close()
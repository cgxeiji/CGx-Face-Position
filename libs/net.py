from __future__ import print_function
import socket
import json
import threading
import logging
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

class Client:
    def __init__(self, socket, name='client'):
        self.socket = socket
        self.name = name
        self.address = socket.getpeername()
        self.ending = '\n'

    def print(self, text):
        self.socket.sendall("{}".format(text).encode('UTF-8'))

    def println(self, text):
        self.socket.sendall("{}{}".format(text, self.ending).encode('UTF-8'))

    def set_ending(self, ending):
        self.ending = ending

    def close(self):
        self.socket.close()

    def is_owner(self, socket):
        return self.socket is socket

class NetManager(threading.Thread):
    def __init__(self, host='', port=''):
        threading.Thread.__init__(self)
        self.position = (0, 0, 0, 0)

        self.connection_list = []
        self.client_list = []
        self.buffer_size = 4096

        if host == '':
            self.host = '10.0.1.43'#socket.gethostname()#'192.168.0.37'
        else:
            self.host = host
        if port == '':
            self.port = 5111
        else:
            self.port = port
        self.backlog = 5

        self.server = None

        self.running = False
        
    def run(self):
        self.running = True
        try:
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server.bind((self.host, self.port))
            self.server.listen(self.backlog)
            self.connection_list.append(self.server)
            logging.info("Connected to {}:{}".format(socket.getfqdn(), self.port))
            print("Connected to {}:{}".format(self.host, self.port))
            logging.info("Waiting for clients...")
            print("Waiting for clients...")

            while self.running:
                read_sockets, write_sockets, error_sockets = select.select(self.connection_list, [], [], 0)
                for _socket in read_sockets:
                    if _socket == self.server:
                        client_socket, address = self.server.accept()
                        self.connection_list.append(client_socket)
                        client = Client(client_socket, "Robot Arm {}".format(len(self.client_list)))
                        self.client_list.append(client)
                        logging.info("Client '{}' [{}] has connected!".format(client.name, client.address))
                        print("Client '{}' [{}] has connected!".format(client.name, client.address))
                    else:
                        try:
                            data = _socket.recv(self.buffer_size).decode('UTF-8')
                            client = self.get_client(_socket)
                            if client is not None:
                                if data == "":
                                    raise
                                print("From '{}': {}".format(client.name, data))
                                if '$name' in data:
                                    text = data.split(':')
                                    client.name = text[1].strip()
                                    print("Client '{}' [{}] changed names!".format(client.name, client.address))
                        except:
                            client = self.get_client(_socket)
                            print(client.name)
                            if client is not None:
                                name = client.name
                                logging.info("Client '{}' [{}] has disconnected!".format(client.name, client.address))
                                print("Client '{}' [{}] has disconnected!".format(client.name, client.address))
                                client.close()
                                self.connection_list.remove(client.socket)
                                self.client_list.remove(client)
                            continue
        except:
            logging.exception("There was an error on networking!")
        finally:
            self.stop()

    def get_client(self, socket):
        client = None
        for _client in self.client_list:
            if _client.is_owner(socket):
                client = _client
                break

        return client

    def set_position(self, x, y, z, a):
        self.position = (x, y, z, a)

    def get_data(self):
        return self.position

    def send(self, msg):
        for client in self.client_list:
            client.println(msg)

    def send_to(self, client_name, msg):
        for client in self.client_list:
            if client_name in client.name:
                client.println(msg)

    def stop(self):
        for client in self.client_list:
            client.close()

        self.server.close()
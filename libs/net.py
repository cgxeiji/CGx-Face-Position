from __future__ import print_function
import socket
import json
import threading
import logging
import time
import select

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
    def __init__(self, host=None, port=None):
        threading.Thread.__init__(self)
        self.position = (0, 0, 0, 0)

        self.connection_list = []
        self.client_list = []
        self.buffer_size = 4096

        if host == None:
            self.host = socket.gethostname()
        else:
            self.host = host
        if port == None:
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
            logging.info("Connected to {}:{}".format(socket.gethostbyname(self.host), self.port))
            print("Connected to {}:{}".format(socket.gethostbyname(self.host), self.port))
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
                                self._on_data_received(client, data)
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
            print("***** There was an error on networking! *****\n***** Check the log file! ***** ")
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
        self.running = False

        for client in self.client_list:
            client.close()

        self.server.close()

    def on_data_received(self, client, data):
        pass

    def _on_data_received(self, client, data):
        logging.debug("{} sent: '{}'".format(client.name, data))
        self.on_data_received(client, data)
import socket
import select
import sys

class Client:
    def __init__(self, socket, name='client'):
        self.socket = socket
        self.name = name
        self.address = socket.getpeername()

    def print(self, text):
        self.socket.sendall("{}".format(text).encode('UTF-8'))

    def println(self, text):
        self.socket.sendall("{}\n\r".format(text).encode('UTF-8'))

    def close(self):
        self.socket.close()

    def is_owner(self, socket):
        return self.socket is socket

def main():
    connection_list = []
    client_list = []
    data_buffer = {}
    buffer_size = 4096

    host = '192.168.1.167'#socket.gethostname()
    port = 5000

    backlog = 5
    
    try:
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((host, port))
        server.listen(backlog)
        connection_list.append(server)
        print("Connected to {}:{}".format(socket.gethostname(), port))
        print("Waiting for clients...")
        while 1:
            read_sockets, write_sockets, error_sockets = select.select(connection_list, [], [], 0)
            for _socket in read_sockets:
                if _socket == server:
                    client_socket, address = server.accept()
                    connection_list.append(client_socket)
                    client = Client(client_socket, "Client {}".format(len(client_list)))
                    client_list.append(client)
                    client.println("Welcome to {}".format(socket.gethostname()))
                    for other_client in client_list:
                        if other_client != client:
                            client.println("[{} is connected!]".format(other_client.name))
                            other_client.println("[{} has joined!]".format(client.name))
                    print("Client '{}' [{}] has connected!".format(client.name, client.address))
                else:
                    try:
                        data = _socket.recv(buffer_size).decode('UTF-8')
                        client = get_client(client_list, _socket)
                        for other_client in client_list:
                            if other_client != client:
                                other_client.print("{} wrote: {}".format(client.name, data))
                            else:
                                client.print("You wrote: {}".format(data))
                    except:
                        client = get_client(client_list, _socket)
                        name = client.name
                        print("Client '{}' [{}] has disconnected!".format(client.name, client.address))
                        client.close()
                        connection_list.remove(client.socket)
                        client_list.remove(client)
                        for client in client_list:
                            client.println("[{} has disconnected!]".format(name))
                        continue
    finally:
        print("Closing server...")
        server.close()
        print("Server closed!")

def get_client(client_list, socket):
    client = None
    for _client in client_list:
        if _client.is_owner(socket):
            client = _client
            break
    return client

if __name__ == '__main__':
    main()
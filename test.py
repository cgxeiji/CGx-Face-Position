import socket
import select

if __name__ == '__main__':
    connection_list = []
    buffer_size = 4096

    host = ''#socket.gethostname()
    port = 5000

    backlog = 5
    
    try:
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((host, port))
        server.listen(backlog)
        print("Connected to {}:{}".format(socket.gethostname(), port))
        print("Waiting for clients...")
        while 1:
            read_sockets, write_sockets, error_sockets = select.select(connection_list, [], [])
            for _socket in read_sockets:
                if _socket == server:
                    client, address = server.accept()
                    connection_list.append(client)
                    client.send("Welcome to {}".format(socket.gethostname()))
                    print("Client [{}] has connected!".format(address))
                else:
                    try:
                        data = _socket.recv(buffer_size).decode('UTF-8')
                        text = "You wrote: '{}'".format(data)
                        _socket.send(text.encode('UTF-8'))
                    except:
                        print("Client [{}] has disconnected!".format(_socket))
                        _socket.close()
                        connection_list.remove(_socket)
                        continue
    finally:
        print("Closing server...")
        server.close()
        print("Server closed!")

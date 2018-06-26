from __future__ import print_function
import time
import math
from net import NetManager

class Robot:
    def __init__(self):
        self.network = NetManager('172.31.1.140', 30000)
        self.network.start()
        time.sleep(1)
        self.translation_speed = 10
        self.rotation_speed = 1

    def move(self,(x, y, z), (a, b, c)):
        self.network.send('R,{:.2f},{:.2f},{:.2f},{:.2f},{:.2f},{:.2f},{:.2f},{:.2f}'.format(x, y, z, a, b, c, self.translation_speed, self.rotation_speed))

    def set_translation_speed(self, speed):
        self.translation_speed = speed

    def set_rotation_speed(self, speed):
        self.rotation_speed = math.radians(speed)

def main():
    my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    my_socket.bind(('172.31.1.140', 30000))
    my_socket.listen(5)
    print(socket.gethostname())

    print("Waiting for client to connect")
    client, address = my_socket.accept()
    print("A client has connected from {}".format(address))
    time.sleep(1)
    
    message = "R,150,0,0,30,0,0,2,{}\n".format(math.radians(1))
    print("Sending: {}".format(message))
    client.sendall(message.encode('UTF-8'))
    time.sleep(10)
    
    message = "R,0,0,0,0,0,0,10,{}\n".format(math.radians(10))
    print("Sending: {}".format(message))
    client.sendall(message.encode('UTF-8'))
    time.sleep(5)
    client.close()
    print("Client closed!")


if __name__ == '__main__':
    main()
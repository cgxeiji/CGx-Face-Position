from __future__ import print_function
import csv
import numpy as np
import glob
import sys
import matplotlib.pyplot as plt
from datetime import datetime
from libs.net import NetManager
import time


def main():
    try:
        network = NetManager()
        network.start()

        frames = []

        with open(sys.argv[1]) as file:
            content = file.readlines()
            content = [x.strip() for x in content]
            for line in content:
                if 'INFO' in line:
                    sections = line.split('->')
                    if len(sections) > 3:
                        if 'face_data' in sections[2]:
                            face_time = datetime.strptime(sections[1], "%Y-%m-%d %H:%M:%S,%f")
                            data = sections[3].split(', ')
                            data.append(face_time)
                            frames.append(data)

        while True:
            _c = raw_input("Press enter")

            for data in frames:
                network.send("{},{},{},{}".format(data[0], data[1], data[2], data[3]))
                print("Sending: {},{},{},{}".format(data[0], data[1], data[2], data[3]))
                time.sleep(0.1)

    finally:
        network.stop()

if __name__ == "__main__":
    main()
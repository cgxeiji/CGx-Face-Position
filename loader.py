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

        rate = 1

        if len(sys.argv) > 2:
            rate = float(sys.argv[2])

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
                            data.append('face')
                            frames.append(data)
                        elif 'monitor_data' in sections[2]:
                            monitor_time = datetime.strptime(sections[1], "%Y-%m-%d %H:%M:%S,%f")
                            data = sections[3].split(',')
                            data.append(monitor_time)
                            data.append('monitor')
                            print(data)
                            frames.append(data)


        while True:
            _c = raw_input("Press enter")
            prev_time = None
            for data in frames:
                if prev_time == None:
                    prev_time = data[len(data) - 2]
                delta_time = (data[len(data)-2] - prev_time).total_seconds()
                if 'face' in data[len(data)-1]:
                    network.send_to("Head", "{},{},{},{}".format(data[0], data[1], data[2], data[3]))
                    print("Face: {},{},{},{}".format(data[0], data[1], data[2], data[3]))
                elif 'monitor' in data[len(data)-1]:
                    network.send_to("Monitor", "{},{},{},{},{},{},{},{}".format(data[0], data[1], data[2], data[3], data[4], data[5], float(data[6])*rate, float(data[7])*rate))
                    print("Monitor: {},{},{},{},{},{}".format(data[0], data[1], data[2], data[3], data[4], data[5]))
                prev_time = data[len(data)-2]
                time.sleep(delta_time/rate)

    finally:
        network.stop()

if __name__ == "__main__":
    main()
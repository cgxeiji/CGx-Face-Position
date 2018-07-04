from __future__ import print_function
import traceback
import csv
import sys
from datetime import datetime
import time
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.widgets import Slider, Button, RadioButtons

def main():
    try:
        face_frames = []
        monitor_frames = []

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
                            face_frames.append(data)
                        elif 'monitor_data' in sections[2]:
                            monitor_time = datetime.strptime(sections[1], "%Y-%m-%d %H:%M:%S,%f")
                            data = sections[3].split(',')
                            data.append(monitor_time)
                            data.append('monitor')
                            monitor_frames.append(data)

        with open('face_data.csv', 'wb') as csv_file:
            writer = csv.writer(csv_file)
            labels = ['timestamp (s)', 'x', 'y', 'z', 'angle', 'zone', 'time (s)']
            data = []
            start_time = None
            for frame in face_frames:
                if start_time == None:
                    start_time = frame[len(frame) - 2]
                timestamp = (frame[len(frame) - 2] - start_time).total_seconds()
                datum = []
                datum.append(timestamp)
                datum.extend(frame[0:6])
                data.append(datum)
            
            dump(writer, labels, data)

        x = []
        y = []
        z = []
        time_data = []

        for frame in face_frames:
            time_data.append(float(frame[0]))
            x.append(float(frame[1]))
            y.append(float(frame[2]))
            z.append(float(frame[3]))

        fig = plt.figure()
        ax = fig.gca(projection='3d')
        ax.set_xlim(-10, 10)
        ax.set_ylim(-10, 10)
        ax.set_zlim(-10, 10) 

        ax.set_xlabel('Z')
        ax.set_ylabel('X')
        ax.set_zlabel('Y')
        ax.scatter([0], [0], [0], label='Center Position', color='r')
        ax.scatter([z[0]], [x[0]], [y[0]], label='Face Position')
        ax.legend()

        def update(val):
            time = int(time_slider.val)
            ax.cla()
            ax.set_xlim(-10, 10)
            ax.set_ylim(-10, 10)
            ax.set_zlim(-10, 10) 

            ax.set_xlabel('Z')
            ax.set_ylabel('X')
            ax.set_zlabel('Y')
            ax.scatter([0], [0], [0], label='Center Position', color='r')
            ax.scatter([z[time]], [x[time]], [y[time]], label='Face Position')
            fig.canvas.draw_idle()

        axcolor = 'lightgoldenrodyellow'
        time_ax = plt.axes([0.25, 0.1, 0.65, 0.03], facecolor=axcolor)

        time_slider = Slider(time_ax, 'timestamp', 0, len(time_data) - 1, valinit=0)
        time_slider.on_changed(update)

        

        plt.show()

    finally:
        print('Finished')


def dump(writer, labels, data):
    writer.writerow(labels)
    rows = []
    for line in data:
        row = []
        for datum in line:
            row.append(datum)
        rows.append(row)

    for row in rows:
        writer.writerow(row)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Keyboard Interrupt')
    except Exception:
        print('{}'.format(traceback.format_exc()))
    finally:
        print('Exit main()')
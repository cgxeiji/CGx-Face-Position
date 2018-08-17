from __future__ import print_function
import traceback
import csv
import sys
from datetime import datetime, timedelta
import time
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.widgets import Slider, Button, RadioButtons
import operator
import Tkinter as tk
import tkFileDialog as filedialog
import matplotlib.collections as collections
import matplotlib.ticker as ticker


class Smoother:
    def __init__(self, size=3):
        self.size = size
        self.buffer = [0] * self.size

    def input(self, value):
        self.buffer.append(value)
        self.buffer.pop(0)

    def set(self, value):
        self.buffer = []
        for i in range(self.size):
            self.buffer.append(value)

    def value(self):
        return sum(self.buffer) / len(self.buffer)


def main():
    try:
        all_enabled = False
        face_frames = []
        monitor_frames = []
        monitor_motion = []

        root = tk.Tk()
        root.withdraw()

        smooth_distance = Smoother(20)
        smooth_angle = Smoother(20)
        smooth_speed = Smoother(20)

        filepath = ''

        print('select a file to analyze')

        if len(sys.argv) < 2:
            filepath = filedialog.askopenfilename()
        elif sys.argv[1] == 1:
            all_enabled = True
        else:
            filepath = sys.argv[1]

        print('loading file: {}'.format(filepath))

        with open(filepath) as file:
            content = file.readlines()
            content = [x.strip() for x in content]
            for line in content:
                if 'INFO' in line:
                    sections = line.split('->')
                    if len(sections) > 3:
                        if 'face_data' in sections[2]:
                            face_time = datetime.strptime(
                                sections[1], "%Y-%m-%d %H:%M:%S,%f")
                            data = sections[3].split(', ')
                            data.append(face_time)
                            data.append('face')
                            face_frames.append(data)
                        elif 'monitor_data' in sections[2]:
                            monitor_time = datetime.strptime(
                                sections[1], "%Y-%m-%d %H:%M:%S,%f")
                            data = sections[3].split(',')
                            data.append(monitor_time)
                            data.append('monitor')
                            monitor_frames.append(data)
                        elif 'motion' in sections[2]:
                            motion_time = datetime.strptime(
                                sections[1], "%Y-%m-%d %H:%M:%S,%f")
                            data = [str(sections[3])]
                            data.append(motion_time)
                            data.append('motion')
                            monitor_motion.append(data)

        print('data loaded\nProcessing data...')

        # with open('face_data.csv', 'wb') as csv_file:
        #     writer = csv.writer(csv_file)
        #     labels = ['timestamp (s)', 'x', 'y', 'z',
        #               'angle', 'zone', 'time (s)']
        #     data = []
        #     start_time = None
        #     for frame in face_frames:
        #         if start_time == None:
        #             start_time = frame[len(frame) - 2]
        #         timestamp = (frame[len(frame) - 2] -
        #                      start_time).total_seconds()
        #         datum = []
        #         datum.append(timestamp)
        #         datum.extend(frame[0:6])
        #         data.append(datum)

        #     dump(writer, labels, data)

        # print('... created *.csv file')

        face_data = []
        start_time = None
        for frame in face_frames:
            if start_time == None:
                start_time = frame[len(frame) - 2]
            timestamp = (frame[len(frame) - 2] -
                         start_time).total_seconds()
            datum = []
            datum.append(timestamp)
            datum.extend(frame[0:6])
            if "Pose Safe" in datum[5]:
                datum[5] = "Pose Safe"
            face_data.append(datum)

        monitor_data = []
        monitor_labels = {
            'Default Position': 0,
            'Default Fast': -1,
            'Move forward': -2,
            'Move upward': -3,
            'Move left': -4,
            'Move right': -5,
            'Turn clockwise': -6,
            'Turn counter clockwise': -7}
        for frame in monitor_motion:
            if not monitor_labels.has_key(frame[0]):
                continue
            if start_time == None:
                start_time = frame[len(frame) - 2]
            timestamp = (frame[len(frame) - 2]
                         - start_time).total_seconds()
            datum = []
            datum.append(timestamp)
            datum.append(frame[0])
            monitor_data.append(datum)

        print('... monitor motion')

        x = []
        y = []
        z = []
        speed = []
        distance = []
        angle_data = []
        time_data = []

        zones = {}
        prev_pos = np.array((0, 0, 0))
        prev_time = 0
        for datum in face_data:
            time_data.append(float(datum[0]))
            x.append(float(datum[1]))
            y.append(float(datum[2]))
            z.append(float(datum[3]))
            current_pos = np.array(
                (float(datum[1]), float(datum[2]), float(datum[3])))
            dist = np.linalg.norm(current_pos - prev_pos)
            sp = dist / (float(datum[0]) - prev_time) \
                if (float(datum[0]) - prev_time) != 0 \
                else 0

            smooth_speed.input(sp if sp < 400 else 0)
            speed.append(smooth_speed.value())
            smooth_distance.input(np.linalg.norm(
                current_pos - np.array((0, 0, 0))))
            distance.append(smooth_distance.value())
            smooth_angle.input(float(datum[4]))
            angle_data.append(smooth_angle.value())
            prev_pos = current_pos
            prev_time = float(datum[0])

        for i in range(1, len(face_data)):
            if face_data[i][5] not in zones:
                zones[face_data[i][5]] = 0.0

            if face_data[i][5] == face_data[i-1][5]:
                if float(face_data[i][6]) != -1:
                    zones[face_data[i][5]] += (
                        float(face_data[i][6])
                        - float(face_data[i-1][6]))

        print('... face zones')

        """
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
        """

        print('... computing times')

        _color_dict_face = {
            'Pose Safe': 'green',
            '': 'white',
                'CGx Bug': 'white',
                'Face Lost': 'lightgrey',
                'Leaning right': 'purple',
                'Leaning left': 'navy',
                'Lean backward': 'salmon',
                'Lean forward': 'saddlebrown',
                'Head tilt left': 'orchid',
                'Head tilt right': 'royalblue'}
        _y_dict = {
            'Pose Safe': 0,
            '': 0,
            'CGx Bug': 0,
            'Face Lost': 1,
            'Leaning right': 2,
            'Leaning left': 3,
            'Lean backward': 4,
            'Lean forward': 5,
            'Head tilt left': 6,
            'Head tilt right': 7}

        #_color_dict = {'Pose Safe':'green', '':'white','CGx Bug':'white', 'Face Lost':'white', 'Leaning right':'saddlebrown', 'Leaning left':'saddlebrown', 'Lean backward':'saddlebrown', 'Lean forward':'saddlebrown', 'Head tilt left':'saddlebrown', 'Head tilt right':'saddlebrown'}

        if all_enabled:
            zones_fig, zones_ax = plt.subplots(
                figsize=(6, 3), subplot_kw=dict(aspect="equal"))

            zones_clean = {}
            for key, value in zones.iteritems():
                if key not in ["Face Lost", '', "CGx Bug"]:
                    zones_clean["{}\n{:.0f}:{:02.0f}".format(
                        key, value/60, value % 60)] = value

            zones_show = {}
            recipe = []
            _data = []
            order_flag = False
            while len(zones_clean) > 0:
                key = ''
                if order_flag:
                    key = max(zones_clean.iteritems(),
                              key=operator.itemgetter(1))[0]
                else:
                    key = min(zones_clean.iteritems(),
                              key=operator.itemgetter(1))[0]
                value = zones_clean.pop(key)
                recipe.append(key)
                _data.append(value)
                order_flag = not order_flag

        print('... plotting')

        if all_enabled:
            _colors = []
            for _d in recipe:
                _colors.append(_color_dict_face[_d.split('\n')[0]])

            wedges, texts = zones_ax.pie(
                _data, colors=_colors, wedgeprops=dict(width=0.5), startangle=-89)

            bbox_props = dict(
                boxstyle="square,pad=0.3",
                fc="w",
                ec="k",
                lw=0.72)
            kw = dict(
                xycoords='data',
                textcoords='data',
                arrowprops=dict(arrowstyle="-"),
                bbox=bbox_props,
                zorder=0,
                va="center")

            for i, p in enumerate(wedges):
                ang = (p.theta2 - p.theta1)/2. + p.theta1
                _y = np.sin(np.deg2rad(ang))
                _x = np.cos(np.deg2rad(ang))
                horizontalalignment = {-1: "right",
                                       1: "left"}[int(np.sign(_x))]
                connectionstyle = "angle,angleA=0,angleB={}".format(ang)
                kw["arrowprops"].update({"connectionstyle": connectionstyle})
                zones_ax.annotate(recipe[i], xy=(_x, _y), xytext=(
                    1.35*np.sign(_x), 1.4*_y), horizontalalignment=horizontalalignment, **kw)

            zones_ax.set_title("Pose Distribution")
            #zones_ax.legend(wedges, recipe)

        face_in_safe = []
        _bar_text = []
        _bar_start = []
        _bar_end = []
        for datum in face_data:
            if datum[5] == 'Pose Safe':
                face_in_safe.append(1)
            else:
                face_in_safe.append(0)
            if len(_bar_text) > 0:
                if datum[5] not in 'Face Lost' and datum[5] not in _bar_text[len(_bar_text) - 1]:
                    _bar_end.append(datum[0])
                    _bar_start.append(datum[0])
                    _bar_text.append(datum[5])
            else:
                _bar_text.append(datum[5])
                _bar_start.append(datum[0])

        _bar_end.append(face_data[len(face_data) - 1][0])

        _y_dict_m = {
            'Default Position': -3,
            'Default Fast': -4,
            'Move forward': -8,
            'Move upward': -7,
            'Move left': -5,
            'Move right': -6,
            'Turn clockwise': -9,
            'Turn counter clockwise': -10}

        @ticker.FuncFormatter
        def zone_formatter(y, pos):
            label = ""
            index = int(y)
            if index <= -3:
                for key, value in _y_dict_m.iteritems():
                    if index == value:
                        label = key
                        break
            else:
                for key, value in _y_dict.iteritems():
                    if index == value:
                        label = key
                        break
            return "{} ({})".format(label, index)

        @ticker.FuncFormatter
        def major_formatter(x, pos):
            adder = timedelta(seconds=x)
            which_time = start_time + adder
            return "{}\n({})".format(which_time.strftime("%H:%M:%S"), int(x))

        if all_enabled:
            fig, ax = plt.subplots()
            ax.set_yticks(np.arange(-10, 8, 1.0))
            ax.set_title(filepath)
            ax.set_ylim(-11, 8)
            ax.xaxis.set_major_formatter(major_formatter)
            ax.yaxis.set_major_formatter(zone_formatter)
            for i in range(len(_bar_text)):
                color = _color_dict_face[_bar_text[i]]
                ax.hlines(_y_dict[_bar_text[i]], _bar_start[i],
                          _bar_end[i], colors=color, lw=20)

        _color_dict = {
            'Default Position': 'green',
            'Default Fast': 'red',
            'Move forward': 'saddlebrown',
            'Move upward': 'salmon',
            'Move left': 'purple',
            'Move right': 'navy',
            'Turn clockwise': 'orchid',
            'Turn counter clockwise': 'royalblue'}

        _monitor_text = []
        _monitor_start = []
        _monitor_end = []

        for datum in monitor_data:
            if len(_monitor_text) > 0:
                if datum[1] not in _monitor_text[len(_monitor_text) - 1]:
                    _monitor_end.append(datum[0])
                    _monitor_start.append(datum[0])
                    _monitor_text.append(datum[1])
            else:
                _monitor_text.append(datum[1])
                _monitor_start.append(datum[0])

        _monitor_end.append(monitor_data[len(monitor_data) - 1][0])

        if all_enabled:
            for i in range(len(_monitor_text)):
                color = _color_dict[_monitor_text[i]]
                ax.hlines(_y_dict_m[_monitor_text[i]], _monitor_start[i],
                          _monitor_end[i], colors=color, lw=20)

        # fig.savefig("{}.pdf".format(
        #     filepath.split('/')[-1]), bbox_inches='tight')

        fig, ax = plt.subplots()

        for i in range(len(_bar_text)):
            color = _color_dict_face[_bar_text[i]]
            ax.axvspan(_bar_start[i], _bar_end[i],
                       ymin=0.5, ymax=1,
                       color=color, alpha=0.5, linewidth=0)

        for i in range(len(_monitor_text)):
            color = _color_dict[_monitor_text[i]]
            ax.axvspan(_monitor_start[i], _monitor_end[i],
                       ymin=0, ymax=0.5,
                       color=color, alpha=0.5, linewidth=0)

        ax.set_title("Visual Data")
        ax.xaxis.set_major_formatter(major_formatter)
        ax.set_xlabel("time")
        ax.set_ylabel("Distance (cm) / Speed (cm/s)")

        ax.plot(time_data, distance, 'blue', linewidth=1)
        # collection = collections.BrokenBarHCollection.span_where(
        #     np.array(time_data), ymin=-10, ymax=40,
        #     where=np.array(face_in_safe) > 0,
        #     facecolor="green", alpha=0.5, linewidths=0)
        # ax.add_collection(collection)
        locs = ax.get_xticks(minor=True)
        labels = ax.get_xticklabels(minor=True)

        ax.plot(time_data, speed, 'green', linewidth=1)
        ax.set_ylim(0, 10)

        ax2 = ax.twinx()
        ax2.set_ylabel("Angle (degrees)", color='red')
        ax2.tick_params(axis='y', labelcolor='red')

        ax2.plot(time_data, angle_data, 'red', linewidth=1)
        ax2.set_ylim(-20, 20)

        print('done!')

        plt.show()

    finally:
        print('Finished')

    # TODO: Sync the slider with video frames and graphs


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

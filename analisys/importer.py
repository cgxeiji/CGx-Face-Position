#!/usr/bin/env python2

from __future__ import print_function
import inspect
import traceback
import os
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
import ConfigParser
import pprint
import argparse


parser = argparse.ArgumentParser(
    description='Graph log files of the robot monitor system')
parser.add_argument("-a", "--all", dest="all",
                    action="store_true",
                    help="Plot all available information")
parser.add_argument("-v", "--video", dest="video_data",
                    action="store_true",
                    help="Load video annotation to sync with the data")
parser.add_argument("-F", "--file", dest="filepath",
                    help="Specify the filepath of the log file to process")

parser.add_argument("-f", "--from", dest="from_time",
                    default="0", type=float,
                    help="Specify the starting time to plot the graph")
parser.add_argument("-t", "--to", dest="to_time",
                    default="0", type=float,
                    help="Specify the ending time to plot the graph")
parser.add_argument("-w", "--width", dest="width",
                    default="0", type=float,
                    help="Set a custom WIDTH in cm")


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


class Action:
    def __init__(self, (x, y, z), (a, b, c), tspeed, aspeed):
        self.position = (x, y, z)
        self.rotation = (a, b, c)
        self.tspeed = tspeed
        self.aspeed = aspeed


class Color:
    def __init__(self):
        self.pose = {}
        self.monitor = {}
        self.video = {}
        self.face_loc = {}
        self.monitor_loc = {}
        self.load_colors()

    def load_colors(self):
        print("Loading colors")
        config = ConfigParser.ConfigParser()
        config.optionxform = str
        config.read(
            '{}/colors.ini'.format(os.path.dirname(inspect.stack()[0][1])))
        for section in config.sections():
            items = {}
            for (name, value) in config.items(section):
                items[name] = value
            if section == "Pose":
                items[''] = 'white'
                self.pose = items
            elif section == "Monitor":
                self.monitor = items
            elif section == "Video":
                self.video = items
            elif section == "Head Movement":
                self.face_loc = items
            elif section == "Monitor Movement":
                self.monitor_loc = items
        print("  ... loaded {} categories of colors".format(len(config.sections())))


class Monitor:
    def __init__(self):
        self.actions = {}
        self.load_actions()

    def load_actions(self):
        print("Loading actions")
        config = ConfigParser.ConfigParser()
        config.read(
            '{}/monitor.ini'.format(os.path.dirname(inspect.stack()[0][1])))
        for section in config.sections():
            pos = (config.getfloat(section, 'x'), config.getfloat(
                section, 'y'), config.getfloat(section, 'z'))
            rot = (config.getfloat(section, 'a'), config.getfloat(
                section, 'b'), config.getfloat(section, 'c'))
            tspeed = config.getfloat(section, 'tspeed')
            aspeed = config.getfloat(section, 'aspeed')

            action = Action(pos, rot, tspeed, aspeed)

            self.actions[section] = action
        print(" ... loaded {} actions".format(len(config.sections())))

    def p(self, start, end, length):
        if start == end:
            return end
        proportion = float(length)/abs(start - end)
        if proportion > 1.0:
            proportion = 1.0
        if proportion < 0.0:
            proportion = 0.0
        return (float(end) - float(start)) * float(proportion) + float(start)

    def calculate(self, (x_s, y_s, z_s), (a_s, b_s, c_s),
                  (x_f, y_f, z_f), (a_f, b_f, c_f),
                  tspeed, aspeed, time):
        distance = tspeed * time
        x = self.p(x_s, x_f, distance)
        y = self.p(y_s, y_f, distance)
        z = self.p(z_s, z_f, distance)

        angle = aspeed * time
        a = self.p(a_s, a_f, angle)
        b = self.p(b_s, b_f, angle)
        c = self.p(c_s, c_f, angle)

        return (x, y, z), (a, b, c)


def process_logfile(file):
    face_frames = []
    monitor_frames = []
    monitor_motion = []

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

    return face_frames, monitor_frames, monitor_motion


def process_videofile(file):
    data = {}
    data["Text"] = []
    data["Start"] = []
    data["End"] = []

    def time2seconds(s):
        start = datetime.strptime("0:0:0:0", "%H:%M:%S:%f")
        return (datetime.strptime(s, "%H:%M:%S:%f") - start).total_seconds()

    csv_data = csv.DictReader(file)
    for row in csv_data:
        data["Text"].append(row["Name"])
        data["Start"].append(time2seconds(row["Start"]))
        data["End"].append(time2seconds(row["End"]))

    return data


def main():
    try:
        print(os.path.dirname(inspect.stack()[0][1]))
        args = parser.parse_args()

        root = tk.Tk()
        root.withdraw()

        smooth_distance = Smoother(20)
        smooth_angle = Smoother(20)
        smooth_speed = Smoother(20)
        smooth_x = Smoother(20)
        smooth_y = Smoother(20)
        smooth_z = Smoother(20)

        monitor = Monitor()
        colors = Color()

        filepath = ''
        videopath = ''

        if args.filepath is None:
            print('Select a log file to analyze:')
            filepath = filedialog.askopenfilename(
                title='Select a log file to analyze:',
                filetypes=[('Log files', '*.log')])
            print('File: {} selected'.format(filepath))
        else:
            filepath = args.filepath

        if args.video_data:
            print('Select a video annotation file to append:')
            videopaths = filedialog.askopenfilenames(
                title='Select a video annotation file to append:',
                filetypes=[('CSV files', '.csv')])
            for p in videopaths:
                print('File: {} selected'.format(p))

        root.update()
        root.destroy()

        print('loading file: {}'.format(filepath))

        face_frames = []
        monitor_frames = []
        monitor_motion = []
        video_data = []

        if args.video_data:
            for path in videopaths:
                with open(path) as file:
                    video_data.append(process_videofile(file))

        with open(filepath) as file:
            face_frames, monitor_frames, monitor_motion = process_logfile(file)
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
            datum.append(monitor.actions[frame[0]])
            monitor_data.append(datum)

        print('... monitor motion')

        x = []
        y = []
        z = []
        speed = []
        distance = []
        angle_data = []
        time_data = []

        face_x = []
        face_y = []
        face_z = []

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

            smooth_x.input(float(datum[1]))
            smooth_y.input(float(datum[2]))
            smooth_z.input(float(datum[3]))

            face_x.append(smooth_x.value())
            face_y.append(smooth_y.value())
            face_z.append(smooth_z.value())

            smooth_speed.input(sp if sp < 400 else 0)
            speed.append(smooth_speed.value())
            smooth_distance.input(np.linalg.norm(
                current_pos - np.array((0, 0, 0))))
            distance.append(smooth_distance.value())
            smooth_angle.input(float(datum[4]))
            angle_data.append(smooth_angle.value())
            prev_pos = current_pos
            prev_time = float(datum[0])

        export_factor = 40
        export_width = time_data[len(time_data) - 1] / export_factor
        _section_width = args.to_time - args.from_time
        print(_section_width)
        if _section_width > 0:
            export_width = _section_width / export_factor
        elif _section_width < 0:
            export_width = (
                time_data[len(time_data) - 1] - args.from_time) / export_factor
        elif (args.from_time == 0) and (args.to_time == 0):
            export_width = 8

        if args.width != 0:
            export_width = args.width * 0.393701

        export_nbins = int(export_width)

        print(time_data[len(time_data) - 1])
        print(export_width)
        print(export_nbins)

        for i in range(1, len(face_data)):
            if face_data[i][5] not in zones:
                zones[face_data[i][5]] = 0.0

            if face_data[i][5] == face_data[i-1][5]:
                if float(face_data[i][6]) != -1:
                    zones[face_data[i][5]] += (
                        float(face_data[i][6])
                        - float(face_data[i-1][6]))

        print('... face zones')

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

        if args.all:
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

        if args.all:
            _colors = []
            for _d in recipe:
                _colors.append(colors.pose[_d.split('\n')[0]])

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

        if args.all:
            fig, ax = plt.subplots()
            ax.set_yticks(np.arange(-10, 8, 1.0))
            ax.set_title(filepath)
            ax.set_ylim(-11, 8)
            ax.xaxis.set_major_formatter(major_formatter)
            ax.yaxis.set_major_formatter(zone_formatter)
            for i in range(len(_bar_text)):
                color = colors.pose[_bar_text[i]]
                ax.hlines(_y_dict[_bar_text[i]], _bar_start[i],
                          _bar_end[i], colors=color, lw=20)
            ax.set_xlim(
                left=None if args.from_time == 0 else args.from_time,
                right=None if args.to_time == 0 else args.to_time)

        if args.video_data:
            fig, ax = plt.subplots(len(video_data), 1, sharex=True)
            for idx in range(len(video_data)):
                vd = video_data[idx]
                ax[idx].set_yticks(np.arange(-1, 1, 1.0))
                ax[idx].set_ylim(-1, 1)
                ax[idx].xaxis.set_major_formatter(major_formatter)
                ax[idx].yaxis.set_major_formatter(zone_formatter)
                for i in range(len(vd["Text"])):
                    color = colors.video.get(vd["Text"][i], 'black')
                    ax[idx].hlines(0, vd["Start"][i],
                                   vd["End"][i], colors=color, lw=20)
                ax[idx].set_xlim(
                    left=None if args.from_time == 0 else args.from_time,
                    right=None if args.to_time == 0 else args.to_time)

        _monitor_text = []
        _monitor_start = []
        _monitor_end = []
        _monitor_time_data = []
        _monitor_x = []
        _monitor_y = []
        _monitor_z = []
        _monitor_a = []
        _monitor_b = []
        _monitor_c = []
        prev_t = None
        prev_a = None
        prev_action = None
        prev_time = 0.0

        for datum in monitor_data:
            if len(_monitor_text) > 0:
                if datum[1] not in _monitor_text[len(_monitor_text) - 1]:
                    _monitor_end.append(datum[0])
                    action = datum[2]
                    _p, _a = monitor.calculate(
                        pprev_t, pprev_a,
                        prev_t, prev_a,
                        prev_action.tspeed, prev_action.aspeed,
                        datum[0] - prev_time)

                    _monitor_start.append(datum[0])
                    _monitor_text.append(datum[1])

                    _monitor_time_data.append(datum[0])
                    _monitor_x.append(_p[0]/10.0)
                    _monitor_y.append(_p[1]/10.0)
                    _monitor_z.append(_p[2]/10.0)

                    _monitor_a.append(_a[0])
                    _monitor_b.append(_a[1])
                    _monitor_c.append(_a[2])

                    pprev_a = _a
                    pprev_t = _p
                    prev_t = action.position
                    prev_a = action.rotation
                    prev_action = action
                    prev_time = datum[0]

            else:
                _monitor_text.append(datum[1])
                _monitor_start.append(datum[0])
                action = datum[2]
                prev_t = action.position
                prev_a = action.rotation
                pprev_a = prev_a
                pprev_t = prev_t
                prev_action = action
                prev_time = datum[0]

        _monitor_end.append(monitor_data[len(monitor_data) - 1][0])

        if args.all:
            for i in range(len(_monitor_text)):
                color = colors.monitor[_monitor_text[i]]
                ax.hlines(_y_dict_m[_monitor_text[i]], _monitor_start[i],
                          _monitor_end[i], colors=color, lw=20)

        # fig.savefig("{}.pdf".format(
        #     filepath.split('/')[-1]), bbox_inches='tight')

        fig, ax = plt.subplots(figsize=(export_width, 10))

        for i in range(len(_bar_text)):
            color = colors.pose[_bar_text[i]]
            ax.axvspan(_bar_start[i], _bar_end[i],
                       ymin=0.2, ymax=1,
                       color=color, alpha=0.5, linewidth=0)

        for i in range(len(_monitor_text)):
            color = colors.monitor[_monitor_text[i]]
            ax.axvspan(_monitor_start[i], _monitor_end[i],
                       ymin=0, ymax=0.2,
                       color=color, alpha=0.5, linewidth=0)

        ax.set_title("Visual Data")
        ax.xaxis.set_major_formatter(major_formatter)
        ax.set_xlabel("time")
        ax.set_ylabel("Distance (cm) / Speed (cm/s)")
        ax.locator_params(axis='x', nbins=export_nbins)

        ax.plot(time_data, distance, colors.face_loc["Distance"], linewidth=1)

        # ax.plot(time_data, face_x, '#9A32CD', linewidth=1)
        # ax.plot(time_data, face_y, '#66CDAA', linewidth=1)
        # ax.plot(time_data, face_z, '#CD5B45', linewidth=1)
        # collection = collections.BrokenBarHCollection.span_where(
        #     np.array(time_data), ymin=-10, ymax=40,
        #     where=np.array(face_in_safe) > 0,
        #     facecolor="green", alpha=0.5, linewidths=0)
        # ax.add_collection(collection)
        locs = ax.get_xticks(minor=True)
        labels = ax.get_xticklabels(minor=True)

        ax.plot(time_data, speed, colors.face_loc["Speed"], linewidth=1)
        ax.set_ylim(-10, 10)
        ax.set_xlim(
            left=None if args.from_time == 0 else args.from_time,
            right=None if args.to_time == 0 else args.to_time)

        ax2 = ax.twinx()
        ax2.set_ylabel("Angle (degrees)", color=colors.face_loc["A"])
        ax2.tick_params(axis='y', labelcolor=colors.face_loc["A"])

        ax2.plot(time_data, angle_data, colors.face_loc["A"], linewidth=1)

        ax2.set_ylim(-30, 30)
        ax2.set_xlim(
            left=None if args.from_time == 0 else args.from_time,
            right=None if args.to_time == 0 else args.to_time)

        fig.savefig("{}.pdf".format(
            filepath.split('/')[-1]), bbox_inches='tight')

        fig, ax = plt.subplots(3, 1, sharex=True, figsize=(export_width, 10))
        for a in ax:
            for i in range(len(_bar_text)):
                color = colors.pose[_bar_text[i]]
                a.axvspan(_bar_start[i], _bar_end[i],
                          ymin=0.5, ymax=1,
                          color=color, alpha=0.5, linewidth=0)

            for i in range(len(_monitor_text)):
                color = colors.monitor[_monitor_text[i]]
                a.axvspan(_monitor_start[i], _monitor_end[i],
                          ymin=0, ymax=0.5,
                          color=color, alpha=0.5, linewidth=0)

            ax[0].xaxis.set_major_formatter(major_formatter)
            ax[0].set_ylabel("Monitor Coordinates (cm)")

            ax[0].plot(_monitor_time_data, _monitor_x,
                       colors.monitor_loc["X"], linewidth=1)
            ax[0].plot(_monitor_time_data, _monitor_y,
                       colors.monitor_loc["Y"], linewidth=1)
            ax[0].plot(_monitor_time_data, _monitor_z,
                       colors.monitor_loc["Z"], linewidth=1)
            ax[0].set_ylim(-10, 10)

            ax[1].xaxis.set_major_formatter(major_formatter)
            ax[1].set_ylabel("Monitor Angle (degrees)")

            ax[1].plot(_monitor_time_data, _monitor_a,
                       colors.monitor_loc["A"], linewidth=1)
            ax[1].plot(_monitor_time_data, _monitor_b,
                       colors.monitor_loc["B"], linewidth=1)
            ax[1].plot(_monitor_time_data, _monitor_c,
                       colors.monitor_loc["C"], linewidth=1)
            ax[1].set_ylim(-30, 30)

            ax[2].xaxis.set_major_formatter(major_formatter)
            ax[2].set_xlabel("time")
            ax[2].set_ylabel("Face Coordinates (cm)")

            ax[2].plot(time_data, face_x, colors.face_loc["X"], linewidth=1)
            ax[2].plot(time_data, face_y, colors.face_loc["Y"], linewidth=1)
            ax[2].plot(time_data, face_z, colors.face_loc["Z"], linewidth=1)
            ax[2].set_ylim(-10, 10)
            ax[2].locator_params(axis='x', nbins=export_nbins)
            ax[2].set_xlim(
                left=None if args.from_time == 0 else args.from_time,
                right=None if args.to_time == 0 else args.to_time)

            ax2 = ax[2].twinx()
            ax2.set_ylabel("Angle (degrees)", color=colors.face_loc["A"])
            ax2.tick_params(axis='y', labelcolor=colors.face_loc["A"])

            ax2.plot(time_data, angle_data, colors.face_loc["A"], linewidth=1)

            ax2.set_ylim(-30, 30)
            ax2.set_xlim(
                left=None if args.from_time == 0 else args.from_time,
                right=None if args.to_time == 0 else args.to_time)

        fig.savefig("{}{}.pdf".format(
            filepath.split('/')[-1], "_2"), bbox_inches='tight')

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

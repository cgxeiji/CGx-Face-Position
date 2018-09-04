from __future__ import print_function
import matplotlib.pyplot as plt
import traceback
import json
import argparse
import pprint
import numpy as np
import glob
import cPickle as pickle
from libs.utils import Smoother
from libs.eye import Eye


parser = argparse.ArgumentParser(
    description='Parse json points generated from Open Pose')
parser.add_argument("-f", "--folder", dest="folderpath", required=True,
                    help="Specify the filepath of the log file to process")
parser.add_argument("-p", "--plot", dest="plot_enabled",
                    action="store_true",
                    help="Plot data")


def main():
    args = parser.parse_args()
    folderpath = args.folderpath
    eyes_list = []

    filenames = glob.glob(folderpath + "/*.json")

    print("Loading files from: {}".format(folderpath))
    for filename in filenames:
        with open(filename) as file:
            data = json.load(file)
            print(" .. loading: {}".format(filename))

            data_array = np.asarray(
                data['people'][0]['pose_keypoints_2d']).reshape((-1, 3))
            eyes = data_array[14:16, :2]
            eyes_list.append(eyes)

    face = []

    baseX = None
    baseY = None
    baseZ = None

    face_x = []
    face_y = []
    face_z = []
    face_a = []

    smooth_x = Smoother(20)
    smooth_y = Smoother(20)
    smooth_z = Smoother(20)
    smooth_a = Smoother(20)

    face_angle = Smoother(10)
    face_distance = Smoother(10)

    r_eye = Eye()
    l_eye = Eye()

    for eyes in eyes_list:
        rx = eyes[0, 0]
        ry = eyes[0, 1]
        lx = eyes[1, 0]
        ly = eyes[1, 1]

        r_eye.input((rx, ry))
        l_eye.input((lx, ly))

        (rx, ry) = r_eye.position()
        (lx, ly) = l_eye.position()

        _angle = (np.arctan2(ly - ry, lx - rx) * 180.0 / np.pi)
        _d = np.sqrt(np.power(ly - ry, 2) + np.power(lx - rx, 2))

        _z = (0.0043 * np.power(_d, 2) - 1.2678 * _d + 116.02)

        _x = (rx + lx) / 2
        _y = (ry + ly) / 2

        if baseX is None:
            baseX = _x
            baseY = _y
            baseZ = _z

        _x -= baseX
        _y -= baseY
        _z -= baseZ

        face_angle.input(_angle)
        face_distance.input(_z)

        smooth_x.input(_x)
        smooth_y.input(_y)
        smooth_z.input(face_distance.value())
        smooth_a.input(face_angle.value())

        face.append((smooth_x.value(), smooth_y.value(),
                     smooth_z.value(), smooth_a.value()))
        face_x.append(smooth_x.value())
        face_y.append(smooth_y.value())
        face_z.append(smooth_z.value())
        face_a.append(smooth_a.value())

    # pprint.pprint(eyes_list)
    # pprint.pprint(face)

    save_path = "{}/{}.cgx".format(folderpath, "face")
    pickle.dump(face, open(save_path, "wb"))
    print("Data saved at: {}".format(save_path))

    if args.plot_enabled:
        fig, ax = plt.subplots()
        time_data = [i*0.5 for i in range(len(face))]

        ax.plot(time_data, face_x,
                "purple", linewidth=1)
        ax.plot(time_data, face_y,
                "green", linewidth=1)
        ax.plot(time_data, face_z,
                "blue", linewidth=1)

        ax.set_ylim(-10, 10)
        ax.set_xlim(
            left=0,
            right=500)

        ax2 = ax.twinx()
        ax2.set_ylabel("Angle (degrees)",
                       color='red')
        ax2.tick_params(
            axis='y', labelcolor='red')

        ax2.plot(time_data, face_a,
                 'red', linewidth=1)

        ax2.set_ylim(-20, 20)
        ax2.set_xlim(
            left=0,
            right=500)

        plt.show()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print('Keyboard Interrupt')
    except Exception:
        print('{}'.format(traceback.format_exc()))
    finally:
        print('Exit main()')

from __future__ import print_function
import traceback
import json
import argparse
import pprint
import numpy as np
import glob


parser = argparse.ArgumentParser(
    description='Parse json points generated from Open Pose')
parser.add_argument("-f", "--folder", dest="folderpath", required=True,
                    help="Specify the filepath of the log file to process")


def main():
    args = parser.parse_args()
    folderpath = args.folderpath
    eyes_list = []

    filenames = glob.glob(folderpath + "/*.json")
    print("Files:")
    pprint.pprint(filenames)

    for filename in filenames:
        with open(filename) as file:
            data = json.load(file)

            data_array = np.asarray(
                data['people'][0]['pose_keypoints_2d']).reshape((-1, 3))
            eyes = data_array[14:16, :2]
            eyes_list.append(eyes)

    face = []

    baseX = None
    baseY = None
    baseZ = None

    for eyes in eyes_list:
        rx = eyes[0, 0]
        ry = eyes[0, 1]
        lx = eyes[1, 0]
        ly = eyes[1, 1]

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

        face.append((_x, _y, _z, _angle))

    pprint.pprint(eyes_list)
    pprint.pprint(face)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print('Keyboard Interrupt')
    except Exception:
        print('{}'.format(traceback.format_exc()))
    finally:
        print('Exit main()')

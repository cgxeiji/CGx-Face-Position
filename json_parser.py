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

    pprint.pprint(eyes_list)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print('Keyboard Interrupt')
    except Exception:
        print('{}'.format(traceback.format_exc()))
    finally:
        print('Exit main()')

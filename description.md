To detect the user's spatial location and head's roll angle, we designed an image processing interface using OpenCV 3.3 on Python 2.7.
This software takes a color image from a webcam, applies a Local Binary Patterns face cascade classifier (Puttemans, 2017) and defines the Region of Interest (ROI) as a square surrounding the face.
Then, a Haar feature-based eye cascade classifier (Hameed, 2008) is applied to find the location of the user's eyes.
To speed up the detection range, the next image processing is only applied around the previous ROI.
If no face is detected, then the full area of the image is analyzed.
To find the 3D coordinate, the distance between the eyes is converted into the Z position, and center point between the eyes represent X and Y positions.
The angle between the horizontal line and the vector line of the eyes is defined as the head's roll angle.

The coordinates are compared against previously defined volumetric zones with different priorities.
If the user's face is inside multiple zones, the zone with higher priority takes precedence. 
To avoid detection artifacts, the users must maintain their location for at least 1 second before the system detects the change in zones.
Each zone corresponds to a specific posture.
The initial position of the user is defined as 'Safe Pose' and is calibrated at the beginning of the user study.

Finally, if the user stays in a zone for more than 5 seconds, the system will send a message via TCP socket to the robot arm to start a motion.

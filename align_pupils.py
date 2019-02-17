# Align facial features to target coordinates.
#
# Make a movie from the results with ffmpeg or other programs
# https://www.ffmpeg.org/ffmpeg.html#Video-and-Audio-file-format-conversion
# ffmpeg -framerate 12 -s 1080x1440 -f image2 -pattern_type glob -i 'output/aligned/*.jpg' -vcodec libx264 -crf 20 -pix_fmt yuv420p ellora_timelapse_20190128_1080x1440_12fps.mp4
#
# Arno Klein, 2019-02-14

import os
import numpy as np
import argparse
import re
import cv2

# Arguments
parser = argparse.ArgumentParser(description="""
                                 $ python align_pupils.py OUT_DIR
                                 where OUT_DIR is the directory of output files""",
                                 formatter_class=lambda prog:
                                 argparse.HelpFormatter(prog,
                                                        max_help_position=40))
# Folders
parser.add_argument("OUT_DIR", help=("directory containing output files"))
args = parser.parse_args()
OUT_DIR = args.OUT_DIR

IMAGE_DIR = "images"
IMAGE_LIST = os.listdir(IMAGE_DIR)
# Check to make sure each file has an extension -- TO DO: confirm file is an image
IMAGE_LIST = [x for x in IMAGE_LIST if len(os.path.splitext(x)) > 1]
IMAGE_STEM_LIST = [os.path.splitext(x)[0] for x in IMAGE_LIST]
FEATURE_DIR = os.path.join("output", "features")
FEATURE_LIST = os.listdir(FEATURE_DIR)
FEATURE_COORD_LIST = [x for x in FEATURE_LIST if os.path.splitext(x)[1] == '.txt']
IMAGE_LIST = [x for x in FEATURE_LIST if os.path.splitext(x)[1] == '.jpg']

ALIGNED_DIR = os.path.join("output", "aligned")
cmd = 'mkdir {0}'.format(ALIGNED_DIR)
print(cmd)
os.system(cmd)
ALIGNED_LIST = os.listdir(ALIGNED_DIR)

# Face landmark 1-indices for points from left to right and top to bottom in the image
num_exocanthion_right = 37
num_endocanthion_right = 40
num_endocanthion_left = 43
num_exocanthion_left = 46

# Reference coordinates from left to right and top to bottom (modified from 20181017_212247.jpg)
ref_exocanthion_right = [1073.5, 1479.5]
ref_endocanthion_right = [1160., 1555.]
ref_endocanthion_left = [1589., 1479.5]
ref_exocanthion_left = [1675.5, 1555.]
ref_pupil_right = [(ref_exocanthion_right[0] + ref_endocanthion_right[0])/2,
                   (ref_exocanthion_right[1] + ref_endocanthion_right[1])/2]
ref_pupil_left = [(ref_exocanthion_left[0] + ref_endocanthion_left[0])/2,
                  (ref_exocanthion_left[1] + ref_endocanthion_left[1])/2]
ref_interpupillary = ref_pupil_left[0] - ref_pupil_right[0]

# Image crop dimensions
max_ratio = 20
crop_dims1 = [9600, 9600]
crop_dims2 = [2700, 3600]

errorsFileName = os.path.join(OUT_DIR, "no_align.txt")


def writeErrorsToFile(error_string, errorsFileName):
    with open(errorsFileName, 'a') as f:
        f.write(error_string + "\n")


# Loop through feature images (they have the same file names as the source image files)
for IMAGE_FILE in IMAGE_LIST:

    # See if there are any corresponding aligned image files
    IMAGE_STEM = re.sub(r'.jpg', r'', IMAGE_FILE)
    ALIGNED_MATCHES = [x for x in ALIGNED_LIST if IMAGE_STEM in x]

    # If there are no corresponding aligned images, run alignment for each coordinate file
    if len(ALIGNED_MATCHES) == 0:

        # Loop through feature coordinate files corresponding to the image
        failed_alignment = True
        FEATURE_COORD_FILES = [x for x in FEATURE_COORD_LIST if IMAGE_STEM in x]
        for FEATURE_COORD_FILE in FEATURE_COORD_FILES:

            FEATURE_PATH = os.path.join(FEATURE_DIR, FEATURE_COORD_FILE)
            FEATURE_COORD_STEM = re.sub(r'.txt', r'', FEATURE_COORD_FILE)
            outputFileName = os.path.join(ALIGNED_DIR, FEATURE_COORD_STEM + ".jpg")

            # Load corresponding image
            try:
                IMAGE_PATH = os.path.join(IMAGE_DIR, IMAGE_FILE)
                img = cv2.imread(IMAGE_PATH)
                rows, cols, ch = img.shape
            except IOError:
                print("Could not read image file {0}".format(IMAGE_PATH))

            # Load feature coordinates
            try:
                f = open(FEATURE_PATH, "r", encoding="utf-8")
                lines = f.readlines()
                f.close()

                # Feature coordinates
                src_exocanthion_right = np.array(lines[num_exocanthion_right - 1].split(), dtype=float)
                src_endocanthion_right = np.array(lines[num_endocanthion_right - 1].split(), dtype=float)
                src_exocanthion_left = np.array(lines[num_exocanthion_left - 1].split(), dtype=float)
                src_endocanthion_left = np.array(lines[num_endocanthion_left - 1].split(), dtype=float)
                src_pupil_right = [(src_exocanthion_right[0] + src_endocanthion_right[0]) / 2,
                                   (src_exocanthion_right[1] + src_endocanthion_right[1]) / 2]
                src_pupil_left = [(src_exocanthion_left[0] + src_endocanthion_left[0]) / 2,
                                  (src_exocanthion_left[1] + src_endocanthion_left[1]) / 2]
                src_interpupillary = src_pupil_left[0] - src_pupil_right[0]

                image_fraction = cols / src_interpupillary

            except IOError:
                print("Could not read features file {0}".format(FEATURE_PATH))

            # Transform image
            scale = ref_interpupillary / src_interpupillary
            if image_fraction < max_ratio:

                print("Scaling {0} by {1}, then shifting, rotating, and translating...".
                    format(IMAGE_FILE, scale))

                try:
                    # Scale matrix
                    scale_matrix = np.array([[scale, 0, 0],
                                             [0, scale, 0]])

                    # Shift matrix
                    scaled_image_center = (scale * cols / 2.,
                                           scale * rows / 2.)
                    shift_matrix = np.array([[1, 0, scaled_image_center[0]],
                                             [0, 1, scaled_image_center[1]]])

                    # Rotation matrix
                    scaled_right_pupil = (scale * src_pupil_right[0],
                                          scale * src_pupil_right[1])
                    center = (scaled_image_center[0] + scaled_right_pupil[0],
                              scaled_image_center[1] + scaled_right_pupil[1])
                    angle = np.rad2deg(np.arctan((src_pupil_left[1] - src_pupil_right[1]) /
                                                 (src_pupil_left[0] - src_pupil_right[0])))
                    rot_matrix = cv2.getRotationMatrix2D(center, angle, scale=1)

                    # Translation matrix
                    translation = [ref_pupil_right[0] - center[0],
                                   ref_pupil_right[1] - center[1]]
                    trans_matrix = np.array([[1, 0, translation[0]],
                                             [0, 1, translation[1]]])

                    # Apply transforms
                    scaled_width = np.int(scale * cols)
                    scaled_height = np.int(scale * rows)
                    img2 = cv2.warpAffine(img, scale_matrix, (scaled_width, scaled_height))
                    img2 = cv2.warpAffine(img2, shift_matrix, (crop_dims1[0], crop_dims1[1]))
                    img2 = cv2.warpAffine(img2, rot_matrix, (crop_dims1[0], crop_dims1[1]))
                    img2 = cv2.warpAffine(img2, trans_matrix, (crop_dims2[0], crop_dims2[1]))
                except IOError:
                    print("Could not transform {0} using {1}".format(IMAGE_PATH, IMAGE_FILE))

                # Save transformed image
                try:
                    failed_alignment = False
                    print("Saving output image to", outputFileName)
                    cv2.imwrite(outputFileName, img2)
                except IOError:
                    print("Could not write transformed image file {0}".format(outputFileName))

            else:
                print("Image-to-interpupillary distance ratio {0} is greater than {1} for {2}".
                    format(image_fraction, max_ratio, IMAGE_FILE))

        if failed_alignment:
            print("{0} failed to align".format(IMAGE_FILE))
            writeErrorsToFile(IMAGE_FILE, errorsFileName)

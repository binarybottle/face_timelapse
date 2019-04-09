# Create montages of images.  Calls ImageMagick's montage command.
#
# Make a movie from the results with ffmpeg or other programs
# https://www.ffmpeg.org/ffmpeg.html#Video-and-Audio-file-format-conversion
# ffmpeg -framerate 12 -s 1080x810 -f image2 -i 'output/montages/montage%d.jpg' -vcodec libx264 -crf 20 -pix_fmt yuv420p ellora_2x2montage_timelapse_20190128_1080x810_12fps.mp4
#
# Arno Klein, 2019-02-19

import os
import numpy as np
import argparse

# Arguments
parser = argparse.ArgumentParser(description="""
                                 $ python create_montages.py OUT_DIR
                                 where OUT_DIR is the directory of output files""",
                                 formatter_class=lambda prog:
                                 argparse.HelpFormatter(prog,
                                                        max_help_position=40))

n = 2

# Folders
parser.add_argument("OUT_DIR", help=("directory containing output files"))
args = parser.parse_args()
OUT_DIR = args.OUT_DIR
IMAGE_DIR = os.path.join(OUT_DIR, "aligned")
IMAGE_LIST = os.listdir(IMAGE_DIR)
IMAGE_LIST = [x for x in IMAGE_LIST if os.path.splitext(x)[1] == '.jpg']
IMAGE_LIST.sort()
MONTAGE_DIR = os.path.join(OUT_DIR, "montages"+str(n)+"x"+str(n))
cmd = 'mkdir {0}'.format(MONTAGE_DIR)
print(cmd)
os.system(cmd)

# Settings
if n == 2:
    xdim = 405
    ydim = 540
elif n == 3:
    xdim = 270
    ydim = 360

N = n**2

# Build montages
i = 0
n_montages = np.int(np.floor(len(IMAGE_LIST) / N))
for i_montage in range(n_montages):
    file_list = IMAGE_LIST[i:i+N]
    file_list = [os.path.join(IMAGE_DIR, x) for x in file_list]

    outFile = os.path.join(MONTAGE_DIR,
                           'montage' + str(i_montage+1) + '.jpg')

    # Run montage command
    files = ' '.join(file_list)
    cmd = "montage {0} -tile {1}x{1} -geometry {2}x{3}+0+0 {4}".\
        format(files, n, xdim, ydim, outFile)

    #print(cmd)
    os.system(cmd)

    print("Montage {0}".format(i_montage + 1))
    i = i + N

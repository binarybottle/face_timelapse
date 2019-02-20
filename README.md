# face_timelapse
Align faces by their extracted pupils to create a time-lapse movie.
(Optionally create a time-lapse of montages of images as well.)

I use facial feature extraction software
that calls CLandmark [1] and OpenCV [2] to extract 68 facial features
from each of a set of ordered photographs.
There are many implementations out there [3]

Then I use align_pupils.py to estimate pupil coordinates
and align all of the pairs of pupils with a given pair of coordinates.

The only manual steps are to select the initial set of photographs,
making sure the files are named in the order they are to appear in a movie,
then after running align_pupils.py, to remove resulting images that
have detected and aligned faces you don't want to include in the time lapse
in the output/aligned/ directory (this step could be removed if the code 
also did face identification.)

Finally, run a program such as ffmpeg on the command line 
to make a time-lapse movie from the aligned images. 
For 12 frames per second and 1080x1440 resolution with -crf 20 quality:

ffmpeg -framerate 12 -s 1080x1440 -f image2 -pattern_type glob -i 'output/aligned/*.jpg' -vcodec libx264 -crf 20 -pix_fmt yuv420p ellora_timelapse_20190128_1080x1440_12fps.mp4

If you want to make a time-lapse movie of montages, run create_montages.py,
then a program such as ffmpeg (see example in the code's documentation).

----
References:
- [1] http://cmp.felk.cvut.cz/~uricamic/clandmark/index.php?page=installation
- [2] https://www.learnopencv.com/install-opencv-docker-image-ubuntu-macos-windows/
- [3] https://github.com/spmallick/dlib/blob/master/python_examples/face_landmark_detection_to_file.py


### Arno Klein, 2019-02-14, Apache v2.0 License

# import the necessary packages
from skimage.segmentation import slic
from skimage import util
import cv2

def main(img, n_segments):
    image = util.img_as_ubyte(img)
    # loop over the number of segments
    # apply SLIC and extract (approximately) the supplied number
    # of segments
    segments = slic(image, n_segments = n_segments, sigma = 5)

    return segments

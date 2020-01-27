"""
This script renames the images in the current working directory by their label (using Tesseract OCR) and D/V tag (using template matching)

Multiscale template matching taken from https://www.pyimagesearch.com/2015/01/26/multi-scale-template-matching-using-python-opencv/
"""

from PIL import Image
import pytesseract
import os
import sys
import rawpy  # to read raw images
import re
import time
import cv2  # pip install opencv-python
import numpy as np
from multiprocessing import Lock, Pool, Manager, Value
from functools import partial

# make all my prints flush immediately because git bash...
print = partial(print, flush=True)

### Modify the variables here ###
FileExtension = ".CR2"  # File extension of the raw image (if it's not a raw image go change the code in process_image)
threshold = 0.8  # threshold for template match to be accepted

# setup templates
template_D = cv2.imread('Templates/D.png', 0)  # flag 0 for grayscale image
if template_D is None:
	raise FileNotFoundError("Templates/D.png could not be found")
template_V = cv2.imread('Templates/V.png', 0)
if template_V is None:
	raise FileNotFoundError("Templates/V.png could not be found")


def filter_text(imgtext):
    """
    This function takes in the block of text from Tesseract and tries to find the correct string.
    Returns the string if found, else returns None 
    """
    # Search pattern is of the form: <3 capital alphabets>_<3 capital alphabets><8 digits>      e.g. ZRC_ENT00009431
    # accept false O's in the last bit too, and change it later to 0's
    search_pattern = r"\b[A-Z]{3}_[A-Z]{3}([0-9O]){8}\b"
    match = re.search(search_pattern, imgtext)
    if match:
        text = match.group(0)
        if 'O' in text[7:15]:  # replace any O's with 0's
            text = text[0:7] + text[7:15].replace('O', '0')
        return text
    else:
        return None


def rename_img(filename, text, dorsal_ventral):
    """" This function renames the image to its label + D/V/A + <number if filename is taken> """
    global FileExtension
    global renamed_file_counter
    renamed_file_counter.value += 1
    lock.acquire()
    # check if new file name already exists
    if not (f"{text} {dorsal_ventral}{FileExtension}") in os.listdir(os.getcwd()):
        os.rename(filename, f"{text} {dorsal_ventral}{FileExtension}")
        print(f"Renaming {filename} to {text} {dorsal_ventral}{FileExtension}")
    else:
        n = 1
        while (f"{text} {dorsal_ventral}({n}){FileExtension}") in os.listdir(os.getcwd()):
            n += 1
        os.rename(filename, f"{text} {dorsal_ventral}({n}){FileExtension}")
        print(
            f"Renaming {filename} to {text} {dorsal_ventral}({n}){FileExtension}")
    lock.release()
    return


def resize_img(img, new_width):
    """ Resize an OpenCV image to a new width, maintaining Aspect Ratio """
    factor = (new_width / float(img.shape[1]))
    new_height = int(img.shape[0] * factor)
    return cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_AREA)


def match_template(img):
    """ This function tries to match the D or V template images with the img input, 
    and returns the highest correlation coefficient along with the corresponding letter
    """
    global template_D
    global template_V
    res_D = cv2.matchTemplate(img, template_D, cv2.TM_CCOEFF_NORMED)
    res_V = cv2.matchTemplate(img, template_V, cv2.TM_CCOEFF_NORMED)
    val_D = np.amax(res_D)
    val_V = np.amax(res_V)
    if val_D > val_V:
        return ['D', val_D]
    else:
        return ['V', val_V]


def process_image(filename):
    """This function looks at the raw image from filename and renames it"""
    try:
        # Get openCV image from the raw image
        with rawpy.imread(filename) as raw_image:
            rgb = raw_image.postprocess()  # returns a numpy array
        # convert into the correct colour for cv2
        img = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)

        # initialise some variables to keep track of things found
        renamed_flag = 0
        label_found = None  # to hold the finalised label
        labels_found = []  # stores the labels found, needs to have 2 similar hits before accepting
        template_found = None  # to store the D/V string if threshold is reached
        starting_width = 600
        ending_width = 6000
        for width in range(starting_width, ending_width + 1, 100):
            text = None
            img_resized = resize_img(img, width)
            # convert to grayscale for template matching
            img_gray = cv2.cvtColor(img_resized, cv2.COLOR_BGR2GRAY)

            if not label_found:
                # PyTesseract only seems to accept PIL image formats...
                img_text = pytesseract.image_to_string(Image.fromarray(
                    img_resized), config='--psm 3 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ_0123456789')  # Get data output and split into list
                text = filter_text(img_text)
                if text:
                    # print(f"{text} label found for {filename} at width {width}")
                    if text in labels_found:
                        label_found = text
                    else:
                        labels_found.append(text)

            # only for every other width as it seems pretty easy
            if not template_found and width % 200 == 0:
                template_result = match_template(img_gray)
                if template_result[1] > threshold:
                    template_found = template_result[0]
                    # crop part of the image after template is found
                    img = img[int(img.shape[0]/2):img.shape[0], 0:int(3*img.shape[1]/4)]
                    # print(f"template found for {filename} at width {width} with coeff: {template_result[1]}")

            # at the end of the loop
            if width == ending_width:
                if len(labels_found) == 1:
                    label_found = labels_found[0]
                if label_found and not template_found:
                    rename_img(filename, label_found, 'A')
                    renamed_flag = 1
                    break

            if label_found and template_found:
                rename_img(filename, label_found, template_found)
                renamed_flag = 1
                break

        if renamed_flag == 0:
            unrenamed_files.append(filename)
            # print(f"Unable to find the text for file: {filename}")

    except KeyboardInterrupt:
        pass


# initialise the global variables into the processor pool
def init(l, _unrenamed_files, _renamed_file_counter):
    global lock
    global unrenamed_files
    global renamed_file_counter
    lock = l
    unrenamed_files = _unrenamed_files
    renamed_file_counter = _renamed_file_counter


if __name__ == '__main__':
    start = time.time()
    print("Looking at images...")
    l = Lock()
    manager = Manager()
    _unrenamed_files = manager.list()  # holds shared list of unrenamed files during first round of processing
    _renamed_file_counter = Value('i', 0)
    directory = os.getcwd()
    files = [filename for filename in sorted(os.listdir(directory)) if filename.endswith(FileExtension)]  # and not filename.startswith('ZRC_ENT')
    no_of_files = len(files)

    pool = Pool(initializer=init, initargs=(l, _unrenamed_files, _renamed_file_counter))
    try:
        pool.map_async(process_image, files).get(99999)
    except KeyboardInterrupt:
        pool.terminate()
        pool.join()
        print("Shutting down program...")
        sys.exit(1)
    pool.close()
    pool.join()

    print(f"The script took {(time.time() - start):.1f}s to rename {_renamed_file_counter.value} out of {no_of_files} files.")
    if _unrenamed_files:
        print(f"The files that could not be renamed are:")
        print(_unrenamed_files)

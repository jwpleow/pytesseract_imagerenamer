from PIL import Image
import pytesseract
import os
import rawpy # to read raw images
import re
import logging
import time
import cv2 #pip install opencv-python
import numpy as np

# logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)
start = time.time()

### Modify the variables here ###
FileExtension = ".CR2" # File extension of the image
threshold = 0.9 # threshold for template match to be accepted - need to tune

# setup templates
template_D = cv2.imread('Templates/D.png', 0) # flag 0 for grayscale image
template_V = cv2.imread('Templates/V.png', 0)

def filter_text(imgtext):
    """"
    This function takes in the block of text from Tesseract and tries to find the correct string.
    Returns the string if found, else returns None 
    """
    # Search pattern is of the form: <3 capital alphabets>_<3 capital alphabets><8 digits>      e.g. ZRC_ENT00009431
    search_pattern = "[A-Z]{3}_[A-Z]{3}([0-9O]){8}"  # accept false O's in the last bit too, and change it later to 0's 
    match = re.search(search_pattern,imgtext)
    if match:
        log.debug("Match found!")
        text = match.group(0) # get the string from the match object - what if there are multiple matches? hmm
        if 'O' in text[7:15]: #replace any O's with 0's
            text = text[0:7] + text[7:15].replace('O','0')
            log.debug("Replaced O's with 0's")
        return text
    else:
        return None


def rename_img(text, dorsal_ventral):
    """" This function renames the image to its label + A<number> """

    if not (f"{text} {dorsal_ventral}{FileExtension}") in os.listdir(os.getcwd()): #check if new file name already exists
        os.rename(filename, f"{text} {dorsal_ventral}{FileExtension}")
        print(f"Renaming file to: {text} {dorsal_ventral}{FileExtension}", flush=True)
    else:
        n = 1
        while (f"{text} {dorsal_ventral}({n}){FileExtension}") in os.listdir(os.getcwd()):
            n += 1
        os.rename(filename, f"{text} {dorsal_ventral}({n}){FileExtension}")
        print(f"Renaming file to: {text} {dorsal_ventral}({n}){FileExtension}", flush=True)
    return

def resize_img(img, new_width):
    """ Resize an OpenCV image to a new width, maintaining Aspect Ratio """
    factor = (new_width / float(img.shape[1]))
    new_height = int(img.shape[0] * factor)
    return cv2.resize(img, (new_width, new_height), interpolation = cv2.INTER_AREA)

def match_template(img):
    """ This function tries to match the D or V template images with the img input, 
    and returns either a 'D' or 'V' if either match, else returns 'A'
    """
    flag_D = False
    flag_V = False
    ret = ""
    global template_D
    global template_V
    res_D = cv2.matchTemplate(img, template_D, cv2.TM_CCOEFF_NORMED)
    res_V = cv2.matchTemplate(img, template_V, cv2.TM_CCOEFF_NORMED)
    # print(f"res_D: {np.amax(res_D)}, res_V:{np.amax(res_V)}",flush=True)
    if np.amax(res_D) > threshold:
        flag_D = True
    if np.amax(res_V) > threshold:
        flag_V = True

    if flag_D == True and flag_V == True:
        print("Both D and V detected!")
        ret = "A"
    elif flag_D == True:
        ret = "D"
    elif flag_V == True:
        ret = "V"
    else:
        print("Neither D nor V was detected!")
        ret = "A"

    return ret

unrenamed_files = [] #list to store unrenamed files
directory = (os.getcwd())
for filename in sorted(os.listdir(directory)): #iterate over every file
    if filename.endswith(FileExtension): #check for the extension of the file
        print(f"Looking at file: {filename}", flush=True)
        with rawpy.imread(filename) as raw_image: #with so that the file is closed after reading
            rgb = raw_image.postprocess() # return a numpy array
        img = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR) # convert into openCV image
        text_found = 0
        for width in range(600,2501,100): # Try a few different image sizes until OCR detects a long enough string
            img_resized = resize_img(img, width)
            img_for_pytesseract = Image.fromarray(img_resized) # PyTesseract only seems to accept PIL image formats?
            imgtext=pytesseract.image_to_string(img_for_pytesseract, config='--psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ_0123456789') #Get data output and split into list
            log.debug(f"For the {width}-width image, text read is: \n {imgtext}")
            text = filter_text(imgtext)
            if text: 
                text_found = 1
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) # convert to grayscale for template matching
                result = match_template(gray) # use openCV template to find if dorsal or ventral
                rename_img(text, result)
                break
        if text_found == 0:
            unrenamed_files.append(filename)
            print("Unable to find the text for file: {filename}", flush=True)

if unrenamed_files:
    print("Trying further steps on files that could not be renamed.", flush=True)
    print(unrenamed_files, flush=True)
    for filename in unrenamed_files:
        if filename.endswith(FileExtension): #check for the extension of the file
            print("Looking at file: " + filename, flush=True)
            with rawpy.imread(filename) as raw_image: #with so that the file is closed after reading
                rgb = raw_image.postprocess() # return a numpy array
            img = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR) # convert into openCV image
            text_found = 0
            for width in range(600,3051,50): # Try more
                if width % 100 != 0 or width > 2401: #only perform for sizes not already tried
                    img_resized = resize_img(img, width)
                    img_for_pytesseract = Image.fromarray(img_resized) # PyTesseract only seems to accept PIL image formats?
                    imgtext=pytesseract.image_to_string(img_for_pytesseract, config='--psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ_0123456789') #Get data output and split into list
                    log.debug(f"For the {width}-width image, text read is: \n {imgtext}")
                    text = filter_text(imgtext)
                    if text: 
                        text_found = 1
                        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) # convert to grayscale for template matching
                        result = match_template(gray) # use openCV template to find if dorsal or ventral
                        rename_img(text, result)
                        break
                        
                # ## Using a different config on pytesseract seems to cause no output suddenly?? (or was this already the case?) Find out why
                # imgtext=pytesseract.image_to_string(img) #Get data output and split into list
                # log.debug(str(basewidth) + " noconfig width text read is: \n" + imgtext)
                # text = filter_text(imgtext)
                # if text: 
                #     rename_img(text)
                #     text_found = 1
                #     break
            if text_found == 0:
                print("Still unable to find the text for file: " + filename, flush=True)

print(f"The script ran for {(time.time() - start):.1f}s") 
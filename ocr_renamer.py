from PIL import Image
import pytesseract
import os
import rawpy # to read raw images
import re
import logging
import time
import cv2 #pip install opencv-python
import numpy as np
from matplotlib import pyplot as plt

# logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)
start = time.time()

### Modify the variables here ###
FileExtension = ".CR2" # File extension of the image

# setup templates
template_D = cv2.imread('Templates/D.png', 0) # flag 0 for grayscale image
template_V = cv2.imread('Templates/V.png', 0)
threshold = 0.999999 # threshold for template match to be accepted - need to tune

# All the 6 methods for comparison in a list
methods = ['cv2.TM_CCOEFF', 'cv2.TM_CCOEFF_NORMED', 'cv2.TM_CCORR',
            'cv2.TM_CCORR_NORMED', 'cv2.TM_SQDIFF', 'cv2.TM_SQDIFF_NORMED']





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

    if not (f"{text} {dorsal_ventral}{FileExtension}") in os.listdir(directory): #check if new file name already exists
        os.rename(filename, f"{text} {dorsal_ventral}{FileExtension}")
        print(f"Renaming file to: {text} {dorsal_ventral}{FileExtension}", flush=True)
    else:
        n = 1
        while (f"{text} {dorsal_ventral}({n}){FileExtension}") in os.listdir(directory):
            n += 1
        os.rename(filename, f"{text} {dorsal_ventral}({n}){FileExtension}")
        print(f"Renaming file to: {text} {dorsal_ventral}({n}){FileExtension}", flush=True)
    return

def resize_img(img, new_width):
    """ Resize an OpenCV image to a new width, maintaining Aspect Ratio """
    factor = (new_width / float(img.shape[1]))
    new_height = int(img.shape[0] * factor)
    return cv2.resize(img, (new_width, new_height), interpolation = cv2.INTER_AREA)

def match_template(img): # try canny edge detection first?
    flag_D = False
    flag_V = False
    ret = ""
    D_count = 0
    V_count = 0
    global template_D
    global template_V
    res_D = cv2.matchTemplate(img, template_D, cv2.TM_SQDIFF_NORMED)
    res_V = cv2.matchTemplate(img, template_V, cv2.TM_SQDIFF_NORMED)
    for i in res_D:
        if i.any() > threshold:
            flag_D = True
            D_count += 1
    for i in res_V:
        if i.any() > threshold:
            flag_V = True
            V_count += 1
    print(f"D count: {D_count}, V count: {V_count}", flush=True)
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

    # view where the rectangle is...
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res_D)
    top_left = max_loc
    w, h = template_D.shape[::-1]
    bottom_right = (top_left[0] + w, top_left[1] + h)
    cv2.rectangle(img,top_left, bottom_right, 255, 2)
    plt.subplot(121),plt.imshow(res_D,cmap = 'gray')
    plt.title('Matching Result'), plt.xticks([]), plt.yticks([])
    plt.subplot(122),plt.imshow(img,cmap = 'gray')
    plt.title('Detected Point'), plt.xticks([]), plt.yticks([])
    plt.show()
    input("Press Enter to continue...")


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


# print("Trying further steps on files that could not be renamed.", flush=True)
# print(unrenamed_files, flush=True)
# for filename in unrenamed_files:
#     if filename.endswith(FileExtension): #check for the extension of the file
#         print("Looking at file: " + filename, flush=True)
#         with rawpy.imread(filename) as raw_image: #with so that the file is closed after reading
#             rgb = raw_image.postprocess()
#         img = Image.fromarray(rgb)
#         text_found = 0
#         for basewidth in range(600,3051,50): # Try more
#             ## Code to resize the image while keeping aspect ratio - so that OCR can be more accurate
#             wpercent = (basewidth/float(img.size[0]))
#             hsize = int((float(img.size[1])*float(wpercent)))
#             img = img.resize((basewidth,hsize), Image.ANTIALIAS)
#             # End resize
#             if basewidth % 100 != 0 or basewidth > 2401: #only perform for sizes not already tried
#                 imgtext=pytesseract.image_to_string(img,config='--psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ_0123456789') #Get data output and split into list
#                 log.debug(str(basewidth) + " width text read is: \n" + imgtext)
#                 text = filter_text(imgtext)
#                 if text: 
#                     rename_img(text)
#                     text_found = 1
#                     break
                    
#             ## Using a different config on pytesseract seems to cause no output suddenly?? (or was this already the case?) Find out why
#             imgtext=pytesseract.image_to_string(img) #Get data output and split into list
#             log.debug(str(basewidth) + " noconfig width text read is: \n" + imgtext)
#             text = filter_text(imgtext)
#             if text: 
#                 rename_img(text)
#                 text_found = 1
#                 break
#         if text_found == 0:
#             print("Still unable to find the text for file: " + filename, flush=True)

print(f"The script ran for {(time.time() - start):.1f}s") 
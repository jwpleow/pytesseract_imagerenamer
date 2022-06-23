from PIL import Image
import pytesseract
import os
import sys
import rawpy  # to read raw images
import re
import time
import cv2 as cv # pip install opencv-python
import numpy as np
from multiprocessing import Lock
from typing import List, Union
from functools import partial

print = partial(print, flush=True)
CWD = os.getcwd()
FileExtension = ".CR2"  # File extension of the raw image (if it's not a raw image go change the code in process_image)
threshold = 0.8  # threshold for template match to be accepted

# load templates
template_D = cv.imread('Templates/D.png', 0)  # flag 0 for grayscale image
if template_D is None:
	raise FileNotFoundError("Templates/D.png could not be found")
template_D_width = template_D.shape[1]
template_V = cv.imread('Templates/V.png', 0)
if template_V is None:
	raise FileNotFoundError("Templates/V.png could not be found")

def LoadRawCR2Image(filename: str) -> cv.Mat:
    """ Returns a cv.Mat in RGB format """
    with rawpy.imread(filename) as raw_image:
        rgb = raw_image.postprocess()  # returns a numpy array, and we leave it in RGB format
        flipNum = raw_image.sizes.flip # 0=none, 3=180, 5=90CCW, 6=90CW
    
    if flipNum == 3:
        cv.rotate(rgb, rgb, cv.ROTATE_180)
    elif flipNum == 5:
        # this errors out with "Argument 'rotateCode' is required to be an integer" for some reason
        # cv.rotate(rgb, rgb, cv.ROTATE_90_COUNTERCLOCKWISE) 
        rgb = cv.transpose(rgb)
        rgb = cv.flip(rgb, 1)
    elif flipNum == 6:
        cv.rotate(rgb, rgb, cv.ROTATE_90_CLOCKWISE)
    return rgb

def ResizeImg(img: cv.Mat, new_width : int):
    """ Resize an OpenCV image to a new width, maintaining Aspect Ratio """
    factor = (new_width / float(img.shape[1]))
    new_height = int(img.shape[0] * factor)
    return cv.resize(img, (new_width, new_height), interpolation=cv.INTER_AREA)

def GetLargestInterestingRegions(img_rgb : cv.Mat, img_gray : cv.Mat, k: int=6) -> List[cv.Mat]:
    """ 
    This function returns the largest white labels (as list of up to k BGR images) in the image and returns it
    """
    # apply a threshold to only keep the whites
    
    _, thresh = cv.threshold(img_gray, 190, 255, cv.THRESH_BINARY)

    # performing opening and closing to remove unwanted noise - see https://docs.opencv.org/trunk/d9/d61/tutorial_py_morphological_ops.html
    kernel = np.ones((10, 10))
    closing = cv.morphologyEx(thresh, cv.MORPH_OPEN, kernel)
    kernel = np.ones((50, 50))
    opening = cv.morphologyEx(closing, cv.MORPH_CLOSE, kernel)

    # grab the largest 6 contours and return their images
    contours, _ = cv.findContours(opening, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
    segmented_imgs = []
    bgr_image = cv.cvtColor(img_rgb, cv.COLOR_RGB2BGR)
    sortedContours = sorted(contours, key=cv.contourArea, reverse=True)
    numContours = len(sortedContours)
    numContoursToPick = min(numContours, k)
    for contour in sortedContours[:numContoursToPick]:
        left = min(contour[:, 0, 0])
        right = max(contour[:, 0, 0])
        top = min(contour[:, 0, 1])
        bot = max(contour[:, 0, 1])

        segmented_imgs.append(bgr_image[top:bot, left:right])
    return segmented_imgs


def MatchTemplate(gray_img: cv.Mat, scale_factor_min: float, scale_factor_max: float, scale_factor_increment: float = 0.1) -> str:
    """ 
    This function tries to match the D or V template images with the img input, 
    and returns the "Dorsal" for D, "Ventral" for V, else "A"
    """
    # resize images near the template size and hope to find a template match (assuming both templates have same width)
    # probably resizing the template instead would be better
    for factor in np.arange(scale_factor_min, scale_factor_max, scale_factor_increment):
        resized_gray_img = ResizeImg(gray_img, int(template_D_width * factor))
        try:
            res_D = cv.matchTemplate(resized_gray_img, template_D, cv.TM_CCOEFF_NORMED)
            res_V = cv.matchTemplate(resized_gray_img, template_V, cv.TM_CCOEFF_NORMED)
            val_D = np.amax(res_D)
            val_V = np.amax(res_V)
            if val_D > val_V and val_D > threshold:
                return 'Dorsal'
            elif val_V > threshold:
                return 'Ventral'
        except: # todo: is there a better solution to prevent errors where template is smaller than image?
            pass
    return "A"

def FilterText(img_text : str) -> Union[str, None]:
    """
    This function takes in the block of text from Tesseract and tries to find the correct string.
    Returns the string if found, else returns None 
    """
    # Search pattern is of the form: <3 capital alphabets>_<3 capital alphabets><8 digits>      e.g. ZRC_ENT00009431
    # accept false O's or 5's in the last part too, and change it to 0's and 5's
    search_pattern = r"\b[A-Z]{3}_[A-Z]{3}([0-9OS]){8}\b"
    match = re.search(search_pattern, img_text)
    if match:
        text = match.group(0)
        if 'O' in text[7:15]:  # replace any O's with 0's
            text = text[0:7] + text[7:15].replace('O', '0')
        if 'S' in text[7:15]:  # replace any S's with 5's
            text = text[0:7] + text[7:15].replace('S', '5')
        return text
    else:
        return None

def FindLabel(img_bgr: cv.Mat, psm_setting: int, scale_factor_min: float, scale_factor_max: float, scale_factor_increment: float = 0.1) -> Union[str, None]:
    """ 
    Returns the label if found, else None
    psm 3 is better if your image is mostly all text, but 12 is better for sparse text 
    """
    labels_found = []
    img_width = img_bgr.shape[1]
    for scale_factor in np.arange(scale_factor_min, scale_factor_max, scale_factor_increment):
        img_resized = ResizeImg(img_bgr, int(img_width * scale_factor))

        # PyTesseract only seems to accept PIL image formats...
        img_text = pytesseract.image_to_string(Image.fromarray(
            img_resized), config=f'--psm {psm_setting} -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ_0123456789') 
        text = FilterText(img_text)
        if text:
            # print(f"{text} label found for {filename} at width {int(img_width * factor)}")
            if text in labels_found: # Return immmediately if the label was found twice
                return text
            else:
                labels_found.append(text)
    
    if len(labels_found) == 1:
        return labels_found[0]
    return None

# def SortImages(images):
#     """ Sorts so that the 1st image returned is the D/V label (?)
#     (The D/V label is assumed to be the image found that is relatively square-ish)
#     The 2nd image returned is the remaining image with the smaller area, which should be the long label"""
#     for index, image in enumerate(images):
#         hw_ratio = image.shape[0] / image.shape[1]
#         if hw_ratio > 0.5 and hw_ratio < 2:
#             return image, min(images[(index + 1) % 3], images[(index + 2) % 3], key=lambda a: a.size)
#     return None

class ImageRenamerCR2:
    def __init__(self, filename: str, fileLock: Lock):
        self._originalFilename = filename
        self._rawImgRGB = LoadRawCR2Image(filename)
        self._rawImgBGR = cv.cvtColor(self._rawImgRGB, cv.COLOR_RGB2BGR)
        self._rawImgGray = cv.cvtColor(self._rawImgRGB, cv.COLOR_RGB2GRAY)
        self._fileLock = fileLock
    
    def Process(self) -> bool:
        label, template = self.ProcessUsingThresholdSegmentation()
        # Else try some brute force
        if not label:
            label = FindLabel(self._rawImgBGR, 12, 0.4, 2.0, 0.1)
        if not template:
            template = MatchTemplate(self._rawImgGray, 1.0, 10.0, 0.5)

        if label:
            self.RenameImg(label, template)
            return True

        return False
    
    def ProcessUsingThresholdSegmentation(self) -> tuple:
        """ Returns (label or None, template or None) """
        interestingRegionsBGR = GetLargestInterestingRegions(self._rawImgRGB, self._rawImgGray)
        
        templateFound = False
        labelFound = False
        label = None
        template = None
        for interestingRegionBGR in interestingRegionsBGR:
            if templateFound and labelFound:
                break

            interestingRegionGray = cv.cvtColor(interestingRegionBGR, cv.COLOR_BGR2GRAY)
            
            if not templateFound:
                template = MatchTemplate(interestingRegionGray, 0.5, 2.0, 0.2)
                if template != "A":
                    templateFound = True

            if not labelFound:
                label = FindLabel(interestingRegionBGR, 3, 0.4, 1.0, 0.2)
                if label:
                    labelFound = True
        
        # If label is still not found, try FindLabel with more aggressive params
        for interestingRegionBGR in interestingRegionsBGR:
            if not labelFound:
                label = FindLabel(interestingRegionBGR, 1.0, 2.0, 0.1)
                if label:
                    labelFound = True

        return (label, template)

    def RenameImg(self, label: str, template: str):
        """ This function renames the image to its long label + D/V/A + (number if filename is taken) + {FileExtension} """
        self._fileLock.acquire()
        # check if new file name already exists
        new_name = f"{label} {template}{FileExtension}"
        n = 1
        while new_name in os.listdir(CWD):
            new_name = f"{label} {template}({n}){FileExtension}"
            n += 1
        os.rename(self._originalFilename, new_name)
        print(f"Renaming {self._originalFilename} to {new_name}")
        self._fileLock.release()
        return








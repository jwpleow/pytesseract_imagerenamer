from PIL import Image
from rawkit.raw import Raw
import numpy as np
import pytesseract
import os

# print(pytesseract.image_to_data('test.jpg'))

def check_string(string):
    test = 1
    if len(string) != 15: #check if string length is correct
        test = 0
    if not string[7:15].isdigit(): #check if last 8 characters are digit
        test = 0
    if not string[0:3].isalpha(): #check if first 3 characters are alphabets
        test = 0
    if string[3] != '_':
        test = 0
    if not string[4:7].isalpha(): #check if 4-6th digits are alphabets
        test = 0
    return test


directory = (os.getcwd())
for filename in os.listdir(directory): #iterate over every file
    if filename.endswith('.CR2'): #check for the extension of the file
        print("Looking at file: " + filename)
        raw_image = Raw(filename)
        buffered_image = np.array(raw_image.to_buffer())
        img = Image.frombytes('RGB', (raw_image.metadata.width, raw_image.metadata.height), buffered_image)
        change = 0
        for basewidth in range(600,1601,50): # Try a few different image resizes until OCR detects a long enough string
            ## Code to resize the image while keeping aspect ratio - so that OCR can be more accurate
            wpercent = (basewidth/float(img.size[0]))
            hsize = int((float(img.size[1])*float(wpercent)))
            img = img.resize((basewidth,hsize), Image.ANTIALIAS)
            ## End resize
            imgtextlist=pytesseract.image_to_string(img).split('\n') #Get data output and split into list
            longesttext=max(imgtextlist, key=len) #Grab the longest string
            if check_string(longesttext): #If longer than 13 characters, and no O or o, accept the string and use to rename file
                try:
                    os.rename(filename, longesttext + ".jpg")
                    print("Renaming file to: " + longesttext + ".jpg")
                except FileExistsError:
                    os.rename(filename, longesttext + "(1).jpg")
                    print("Renaming file to: " + longesttext + "(1).jpg")
                change = 1
                break
        if change == 0:
            print("Unable to find the text for file: " + filename)

from PIL import Image
import pytesseract
import os
import rawpy
import re

### Modify the variables here ###
FileExtension = ".CR2"


### String parameters that must be fulfilled
def check_string(string):
    if len(string) != 15: #check if string length is correct
        # print("wrong string length",flush=True)
        return 0
    if 'O' in string[7:15]: #replace any O's with 0's
        string = string[0:7] + string[7:15].replace('O','0')
        # print("replacing O with 0",flush=True)
        # print("new string: " + string, flush=True)
    if not string[7:15].isdigit(): #check if last 8 characters are digit
        # print("last few characters are not digits",flush=True)
        return 0
    if not string[0:3].isalpha(): #check if first 3 characters are alphabets
        # print("first 3 chars are not alphabets",flush=True)
        return 0
    if string[3] != '_':
        print("wrong string length",flush=True)
        return 0
    if not string[4:7].isalpha(): #check if 4-6th digits are alphabets
        # print("5-7th characters are not alphabets",flush=True)
        return 0
        # if there is a O in 7:15 replace with 0?
    return 1

unrenamedfiles = [] #list to store unrenamed files
directory = (os.getcwd())
for filename in sorted(os.listdir(directory)): #iterate over every file
    if filename.endswith(FileExtension): #check for the extension of the file
        print("Looking at file: " + filename, flush=True)
        with rawpy.imread(filename) as raw_image: #with so that the file is closed after reading
            rgb = raw_image.postprocess()
        img = Image.fromarray(rgb)
        change = 0
        for basewidth in range(600,2201,100): # Try a few different image resizes until OCR detects a long enough string
            ## Code to resize the image while keeping aspect ratio - so that OCR can be more accurate
            wpercent = (basewidth/float(img.size[0]))
            hsize = int((float(img.size[1])*float(wpercent)))
            img = img.resize((basewidth,hsize), Image.ANTIALIAS)
            ## End resize
            imgtext=pytesseract.image_to_string(img,config='--psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ_0123456789') #Get data output and split into list
            # print(str(basewidth) + " width text read is: \n" + str(imgtext),flush=True)
            longesttext=max(re.split(u'\s', imgtext),key=len) #split by space/tab/newline character
            # print("Longest text is: ", longesttext,flush=True)
            if check_string(longesttext): #If longer than 13 characters, and no O or o, accept the string and use to rename file
                if not (longesttext + ' A' + FileExtension) in os.listdir(directory):
                    os.rename(filename, longesttext + ' A' + FileExtension)
                    print("Renaming file to: " + longesttext + ' A' + FileExtension, flush=True)
                else:
                    n = 1
                    while (longesttext + ' A(' + str(n) + ')' + FileExtension) in os.listdir(directory):
                        n += 1
                    os.rename(filename, longesttext + ' A(' + str(n) + ')'+ FileExtension)
                    print("Renaming file to: " + longesttext + ' A(' + str(n) + ')' + FileExtension, flush=True)
                change = 1
                break
        if change == 0:
            unrenamedfiles.append(filename)
            print("Unable to find the text for file: " + filename, flush=True)


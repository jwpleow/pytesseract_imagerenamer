from PIL import Image
import pytesseract
import os
import rawpy
import re

### Modify the variables here ###
FileExtension = ".CR2"


### String parameters that must be fulfilled
def check_string(text):
    if len(text) != 15: #check if string length is correct
        return False
    if not text[7:15].isdigit(): #check if last 8 characters are digit
        return False
    if not text[0:3].isalpha(): #check if first 3 characters are alphabets
        return False
    if text[3] != '_':
        return False
    if not text[4:7].isalpha(): #check if 4-6th digits are alphabets
        return False
    return True

def check_and_rename(text):
    try:
        if 'O' in text[7:15]: #replace any O's with 0's
            text = text[0:7] + text[7:15].replace('O','0')
    except:
        pass
    if check_string(text): #If text fulfills criteria of check_string, accept the string and use to rename file
        if not (text + ' A' + FileExtension) in os.listdir(directory): #check if newname already exists
            os.rename(filename, text + ' A' + FileExtension)
            print("Renaming file to: " + text + ' A' + FileExtension, flush=True)
        else:
            n = 1
            while (text + ' A(' + str(n) + ')' + FileExtension) in os.listdir(directory):
                n += 1
            os.rename(filename, text + ' A(' + str(n) + ')'+ FileExtension)
            print("Renaming file to: " + text + ' A(' + str(n) + ')' + FileExtension, flush=True)
        return True
    else:
        return False


unrenamedfiles = [] #list to store unrenamed files
directory = (os.getcwd())
for filename in sorted(os.listdir(directory)): #iterate over every file
    if filename.endswith(FileExtension): #check for the extension of the file
        print("Looking at file: " + filename, flush=True)
        with rawpy.imread(filename) as raw_image: #with so that the file is closed after reading
            rgb = raw_image.postprocess()
        img = Image.fromarray(rgb)
        change = 0
        for basewidth in range(600,2501,100): # Try a few different image resizes until OCR detects a long enough string
            ## Code to resize the image while keeping aspect ratio - so that OCR can be more accurate
            wpercent = (basewidth/float(img.size[0]))
            hsize = int((float(img.size[1])*float(wpercent)))
            img = img.resize((basewidth,hsize), Image.ANTIALIAS)
            ## End resize
            imgtext=pytesseract.image_to_string(img,config='--psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ_0123456789') #Get data output and split into list
            # print(str(basewidth) + " width text read is: \n" + str(imgtext),flush=True)
            longesttext=max(re.split(u'\s', imgtext),key=len) #split by space/tab/newline character
            # print("Longest text is: ", longesttext,flush=True)
            if check_and_rename(longesttext): #Checks if string is correct and renames
                change = 1;
                break
        if change == 0:
            unrenamedfiles.append(filename)
            print("Unable to find the text for file: " + filename, flush=True)


print("Trying further steps on files that could not be renamed.", flush=True)
print(unrenamedfiles,flush=True)
for filename in unrenamedfiles:
    if filename.endswith(FileExtension): #check for the extension of the file
        print("Looking at file: " + filename, flush=True)
        with rawpy.imread(filename) as raw_image: #with so that the file is closed after reading
            rgb = raw_image.postprocess()
        img = Image.fromarray(rgb)
        change = 0
        for basewidth in range(600,3051,50): # Try more
            ## Code to resize the image while keeping aspect ratio - so that OCR can be more accurate
            wpercent = (basewidth/float(img.size[0]))
            hsize = int((float(img.size[1])*float(wpercent)))
            img = img.resize((basewidth,hsize), Image.ANTIALIAS)
            # End resize
            if basewidth % 100 != 0 or basewidth > 2401: #only perform for sizes not alr tried
                imgtext=pytesseract.image_to_string(img,config='--psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ_0123456789') #Get data output and split into list
                # print(str(basewidth) + " width text read is: \n" + imgtext,flush=True)
                longesttext=max(re.split(u'\s', imgtext),key=len) #split by space/tab/newline character
                # print("Longest text is: ", longesttext,flush=True)
                if check_and_rename(longesttext): #Checks if string is correct and renames
                    change = 1;
                    break
                    
            ## Using a different config on pytesseract seems to cause no output??!
            imgtext=pytesseract.image_to_string(img) #Get data output and split into list
            # print(str(basewidth) + " noconfig width text read is: \n" + imgtext,flush=True)
            longesttext=max(re.split(u'\s', imgtext),key=len) #split by space/tab/newline character
            # print("Longest text is: ", longesttext,flush=True)
            if check_and_rename(longesttext): #Checks if string is correct and renames
                change = 1;
                print("caught by noconfig",flush=True)
                break
        if change == 0:
            print("Still unable to find the text for file: " + filename, flush=True)

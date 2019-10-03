from PIL import Image
import pytesseract
import os
import rawpy
import re
import logging

# logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

### Modify the variables here ###
# File extension of the image
FileExtension = ".CR2"



def filter_and_rename(text):
    """" This function filters the text found from Tesseract, and if a string is found that matches the criteria, uses it to rename the file
    Returns True if a matching string is found """

    # Search pattern is of the form: <3 capital alphabets>_<3 capital alphabets><8 digits>      e.g. ZRC_ENT00009431
    search_pattern = "[A-Z]{3}_[A-Z]{3}([0-9O]){8}"  # accept false O's in the last bit too, and change it later to 0's 
    match = re.search(search_pattern,text)
    if match: # If a match is found, accept the string and use to rename file
        text = match.group(0) # get the string from the match object

        try:
            if 'O' in text[7:15]: #replace any O's with 0's
                text = text[0:7] + text[7:15].replace('O','0')
        except:
            pass

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
            log.debug(str(basewidth) + " width text read is: \n" + str(imgtext))
            if filter_and_rename(imgtext): #Checks if string is correct and renames
                change = 1;
                break
        if change == 0:
            unrenamedfiles.append(filename)
            print("Unable to find the text for file: " + filename, flush=True)


print("Trying further steps on files that could not be renamed.", flush=True)
print(unrenamedfiles, flush=True)
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
            if basewidth % 100 != 0 or basewidth > 2401: #only perform for sizes not already tried
                imgtext=pytesseract.image_to_string(img,config='--psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ_0123456789') #Get data output and split into list
                log.debug(str(basewidth) + " width text read is: \n" + imgtext)
                if filter_and_rename(imgtext): #Checks if string is correct and renames
                    change = 1;
                    break
                    
            ## Using a different config on pytesseract seems to cause no output??!
            imgtext=pytesseract.image_to_string(img) #Get data output and split into list
            log.debug(str(basewidth) + " noconfig width text read is: \n" + imgtext)
            if filter_and_rename(imgtext): #Checks if string is correct and renames
                change = 1;
                break
        if change == 0:
            print("Still unable to find the text for file: " + filename, flush=True)

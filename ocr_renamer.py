from PIL import Image
import pytesseract
import os
import rawpy

### Modify the variables here ###
FileExtension = ".CR2"


### String parameters that must be fulfilled
def check_string(string):
    if len(string) != 15: #check if string length is correct
        return 0
    if not string[7:15].isdigit(): #check if last 8 characters are digit
        return 0
    if not string[0:3].isalpha(): #check if first 3 characters are alphabets
        return 0
    if string[3] != '_':
        return 0
    if not string[4:7].isalpha(): #check if 4-6th digits are alphabets
        return 0
    return 1


directory = (os.getcwd())
for filename in os.listdir(directory): #iterate over every file
    if filename.endswith(FileExtension): #check for the extension of the file
        print("Looking at file: " + filename, flush=True)
        with rawpy.imread(filename) as raw_image: #with so that the file is closed after reading
            rgb = raw_image.postprocess()
        img = Image.fromarray(rgb)
        change = 0
        for basewidth in range(600,1601,100): # Try a few different image resizes until OCR detects a long enough string
            ## Code to resize the image while keeping aspect ratio - so that OCR can be more accurate
            wpercent = (basewidth/float(img.size[0]))
            hsize = int((float(img.size[1])*float(wpercent)))
            img = img.resize((basewidth,hsize), Image.ANTIALIAS)
            ## End resize
            imgtextlist=pytesseract.image_to_string(img).split('\n') #Get data output and split into list
            longesttext=max(imgtextlist, key=len) #Grab the longest string
            if check_string(longesttext): #If longer than 13 characters, and no O or o, accept the string and use to rename file
                try:
                    os.rename(filename, longesttext + FileExtension)
                    print("Renaming file to: " + longesttext + FileExtension, flush=True)
                except FileExistsError:
                    os.rename(filename, longesttext + "(1)" + FileExtension)
                    print("Renaming file to: " + longesttext + "(1)" + FileExtension, flush=True)
                change = 1
                break
        if change == 0:
            print("Unable to find the text for file: " + filename, flush=True)

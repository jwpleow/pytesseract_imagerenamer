from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
import os

# print(pytesseract.image_to_data('test.jpg'))

directory = (os.getcwd())



for filename in os.listdir(directory): #iterate over every file
    if filename.endswith('.jpg'): #check for the extension of the file
        print("Looking at file: " + filename)
        img=Image.open(filename)
        for basewidth in range(600,1401,100): # Try a few different image resizes until OCR detects a long enough string
            ## Code to resize the image while keeping aspect ratio - so that OCR can be more accurate
            wpercent = (basewidth/float(img.size[0]))
            hsize = int((float(img.size[1])*float(wpercent)))
            img = img.resize((basewidth,hsize), Image.ANTIALIAS)
            ## End resize
            imgtextlist=pytesseract.image_to_string(img).split('\n') #Get data output and split into list
            longesttext=max(imgtextlist, key=len) #Grab the longest string
            if len(longesttext) > 13: #If longer than 13 characters, accept the string and use to rename file
                try:
                    os.rename(filename, longesttext + ".jpg")
                    print("Renaming file to: " + longesttext + ".jpg")
                    if 'O' in longesttext or 'o' in longesttext:
                        print("Warning, an 'o' or 'O' is in the rename of " + longesttext + ".jpg!")
                except FileExistsError:
                    os.rename(filename, longesttext + "(1).jpg")
                    print("Renaming file to: " + longesttext + "(1).jpg")
                    if 'O' in longesttext or 'o' in longesttext:
                        print("Warning, an 'o' or 'O' is in the rename of " + longesttext + "(1).jpg!")
                break

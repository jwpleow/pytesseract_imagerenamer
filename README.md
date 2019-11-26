# Image Renamer thingy
Image renamer using Tesseract OCR and template matching

Finds the relevant string in the image and uses it to rename the image:  

![alt text](https://github.com/jwpleow/pytesseract_imagerenamer/blob/master/docs/example.jpg "Example Image")  
-> Renames image to ZRC_ENT00004017 V.CR2  
(Uses Tesseract to grab the long string and OpenCV's template matching to match the V)  

Written to help label a butterfly collection

### How to use
Download [Anaconda](https://www.anaconda.com/distribution/)  
In your preferred shell/terminal:
```
pip install rawpy pytesseract opencv-python
```
Install the [Tesseract Engine](https://github.com/tesseract-ocr/tesseract/wiki) (and add the directory to PATH if on Windows)

Place the python script in the directory with the image files, and run it:
```
python ocr_renamer.py
```

# Image Renamer thing [![Build Status](https://travis-ci.com/jwpleow/pytesseract_imagerenamer.svg?branch=master)](https://travis-ci.com/jwpleow/pytesseract_imagerenamer)  [![](https://img.shields.io/badge/python-3.6+-blue.svg)](https://www.python.org/download/releases/3.6.0/)


Image renamer using Tesseract OCR and template matching. Written to help label a butterfly collection.

Finds the relevant string and label in the image and uses it to rename the image:  

![alt text](https://github.com/jwpleow/pytesseract_imagerenamer/blob/master/docs/pic.jpg "Example Image")  
-> Renames image to ZRC_ENT00004017 V.CR2  



### How to use
Download [Anaconda](https://www.anaconda.com/distribution/)  
In command/anaconda prompt or your preferred CLI:
```
pip install rawpy pytesseract opencv-python
```
Install the [Tesseract Engine](https://github.com/tesseract-ocr/tesseract/wiki) (and add the directory to PATH if on Windows - e.g. C:\Program Files\Tesseract-OCR)

Place the python script in the directory with the image files, and run it:
```
python ocr_renamer.py
```

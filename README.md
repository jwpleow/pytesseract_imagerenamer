# Butterfly Image Renamer ![Build Status](https://github.com/jwpleow/pytesseract_imagerenamer/actions/workflows/test.yml/badge.svg) [![](https://img.shields.io/badge/python-3.6+-blue.svg)](https://www.python.org/download/releases/3.6.0/)


Image renamer using Tesseract OCR and template matching. Written to help label a butterfly collection.

First applies a threshold to isolate the white labels, and then reads them to rename the image:  

![alt text](https://github.com/jwpleow/pytesseract_imagerenamer/blob/master/docs/pic.jpg "Example Image")  
-> Renames image to ZRC_ENT00004017 V.CR2  



### How to use

Install the [Tesseract Engine](https://github.com/tesseract-ocr/tesseract/wiki) (and add the directory to PATH if on Windows - the path should be something like C:\Program Files\Tesseract-OCR)

Download some distribution of Python 3.6+: [Official Python](https://www.python.org/downloads/) or [Anaconda](https://www.anaconda.com/distribution/)  

Download this [repository](https://github.com/jwpleow/pytesseract_imagerenamer/archive/master.zip)

In command/anaconda prompt or your preferred CLI, navigate to the folder you downloaded this repository to and type:
```
pip install -r requirements.txt
```

Place ocr_renamer.py and the Templates folder in the directory with the image files you want to rename, and run it:
```
python ocr_renamer.py
```

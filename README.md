# pytesseract
Image renamer using Tesseract OCR

Finds the relevant string in the image and uses it to rename the image  

(Written to help label a butterfly collection)  

### How to use
Download [Anaconda](https://www.anaconda.com/distribution/)  
In your preferred shell/terminal/virtualenv:
```
pip install rawpy
pip install pytesseract
pip install opencv-python
```
Install the [Tesseract Engine](https://github.com/tesseract-ocr/tesseract/wiki) (and add the directory to PATH if on Windows)

Place the python script in the directory with the image files, and run it:
```
python ocr_renamer.py
```

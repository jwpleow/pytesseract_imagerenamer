# pytesseract
Image renamer using Tesseract OCR

Reads the longest string in the list of words (delimited by '\n') found in the image and uses it to rename the image

### Dependencies
```
pip install rawpy
pip install pytesseract
```
Install the [Tesseract Engine](https://github.com/tesseract-ocr/tesseract/wiki) (and add the directory to PATH if on Windows)

Place the python script in the directory with all the image files, and run it:
```
python ocr_renamer.py
```

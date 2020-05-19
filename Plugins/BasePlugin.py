from AbstractPlugin import Plugin
import cv2
import pytesseract

class MiningPlugin(Plugin):

    def __init__(self):
        super.__init__(self)
    
    def process_img(self):
        if (pytesseract.image_to_string(screen[8:20, 15:100], lang='eng', config='--psm 13') == 'Star Trek Online'):
            return True
        else:
            return False
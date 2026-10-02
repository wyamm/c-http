import cv2 as cv
from PIL import Image
from matplotlib import pyplot as plt
import pytesseract
import numpy as np
import pyautogui as pyauto
from difflib import SequenceMatcher
import re

from constants import COLS, WIN_H, WIN_W
# import easyocr
CONFIG = '--psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.+-_ '

# reader = easyocr.Reader(['en'], gpu=True)
def thin_font(image):
    image = cv.bitwise_not(image)
    kernel = np.ones((2, 2), np.uint8)
    image = cv.erode(image, kernel, iterations=1)
    image = cv.bitwise_not(image)
    return image

def thick_font(image):
    image = cv.bitwise_not(image)
    kernel = np.ones((2, 2), np.uint8)
    image = cv.dilate(image, kernel, iterations=1)
    image = cv.bitwise_not(image)
    return image


def OCR(img):
    ocr_result = pytesseract.image_to_string(img, config=CONFIG)
    return ocr_result

def process_image(img, name):
    img = cv.resize(img, None, fx=2, fy=2, interpolation=cv.INTER_CUBIC)
    img = cv.cvtColor(img, cv.COLOR_BGR2GRAY) # greyscale
    img = cv.bitwise_not(img) # invert

    img =  thin_font(img)
    _, final = cv.threshold(img, 150, 250, cv.THRESH_BINARY) # binarize

    cv.imwrite(f"images/live_final/{name}.jpg", final) # save the processed image
    return final


def process_single(i : int, name : str, full):
        col = i % COLS if COLS else 0
        row = i // COLS if COLS else i

        x = col * WIN_W  #screen shots
        y = int(row * WIN_H + 1 / 3 * WIN_H)
        cropped = full[y:y + int(WIN_H / 3), x: x + int(WIN_W)] # the width stays the same, but we only take the middle 1/3 of the screenshot
        img = process_image(cropped, name)
        text = OCR(img)
        return text

def fuzzy_match(team: str, abvr: str, line: str, threshold=0.75):
    """Check if team name roughly appears in line, tolerating OCR errors."""
    clean_team = team.lower().replace(" ", "")
    clean_abvr = abvr.lower().replace(" ", "")
    clean_line = line.lower().replace(" ", "").replace(".", "").replace("_", "")

    # Exact substring check
    if clean_team in clean_line or clean_abvr in clean_line:
        return True

    # Slide a clean_window the size of the team name across the line
    team_window = len(clean_team)
    for i in range(len(clean_line) - team_window + 1):
        substring = clean_line[i:i + team_window]
        if SequenceMatcher(None, clean_team, substring).ratio() > threshold:
            return True
    return False

def clean_ocr(text: str) -> str:
     # Only apply near odds patterns
    return re.sub(r'(?<=[+-])([A-Za-z\d]{3,})',
                  lambda m: m.group().replace('T','1').replace('O','0').replace('l','1'),
                  text)
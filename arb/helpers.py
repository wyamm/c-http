
import cv2 as cv
import traceback
from matplotlib import pyplot as plt
import sys
import numpy as np
import pyautogui as pyauto
import re
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from image_process import process_single, fuzzy_match, clean_ocr
from classes import Bookie
from arb_calc import find_best_odds
import mss.tools
import cv2
import mss

def screen_shot():
    with mss.MSS() as sct:
        monitor_number = 2
        mon = sct.monitors[monitor_number]
        # monitor = {"top": mon["top"]}
        sct_img = sct.grab(mon)
        return sct_img

def build_books(website_file: str) -> dict[int, Bookie]:
    books = {}
    with open(website_file, "r") as f:
        for i, line in enumerate(f):
            name = line.strip().split("/")[2].split(".")[0]
            books[i] = Bookie(name)
    return books

# -------- helpers -------------------------
def parse_american(odds_str: str) -> float:
    """Convert American odds string like '+700' or '-714' to decimal."""
    num = float(odds_str[1:])
    if odds_str[0] == '+':
        return round(num / 100 + 1, 2)
    else:
        return round(100 / num + 1, 2)

def extract_decimals(text: str) -> list[float]:
    """Pull all decimal odds from a string"""
    return [float(m) for m in re.findall(r'(\d+\.\d+)', text)]

def extract_american(text: str) -> list[float]:
    """Pull all American odds (e.g. +700, -714) and convert to decimal."""
    return [parse_american(m) for m in re.findall(r'[+-]\d{3,}', text)]

def find_team_line(lines: list[str], team: str, abrv: str) -> int | None:
    """Return the index of the first line that fuzzy-matches the team name or abvr."""
    for i, line in enumerate(lines):
        if fuzzy_match(team, abrv, line):
            return i
    return None

# --------- Stake parsing ------------------
def parse_stake(lines: list[str], team: str, abrv: str, num_odds: int) -> list[float] | None:
    team_idx = find_team_line(lines, team, abrv)
    if team_idx is None:
        print("stake: team not found")
        return None
    # outcome all on the same line
    #   "France 1.48"
    #   "Draw 4.30"
    #   "Senegal 6.60"

    odds = []
    scan_end = min(team_idx + num_odds * 2, len(lines))

    for i in range(team_idx, scan_end):
        found_decimal = extract_decimals(lines[i])
        found_american = extract_american(lines[i])

        # all odds on one line
        if len(found_decimal) == num_odds:
            return [round(o, 2) for o in found_decimal]
        if len(found_american) == num_odds:
            return [round(o, 2) for o in found_american]

        # single odds per line (e.g. "France 1.48")
        if len(found_decimal) == 1:
            odds.extend(found_decimal)
        elif len(found_american) == 1:
            odds.extend(found_american)

        if len(odds) >= num_odds:
            return [round(o, 2) for o in odds[:num_odds]]

    print("stake odds not found")
    return None

# ---- General parsing, where the odds are on the same line and the team are also on the same line
def parse_general(lines: list[str], team: str, abrv: str, num_odds: int) -> list[float] | None:
    team_idx = find_team_line(lines, team, abrv)
    if team_idx is None:
        print("could not find team idx")
        return None

    # try american odds first
    odds_american = extract_american(lines[team_idx])
    if len(odds_american) == num_odds:
        return [round(o, 2) for o in odds_american]

    odds_decimals = extract_decimals(lines[team_idx])
    if len(odds_decimals) == num_odds:
        return [round(o, 2) for o in odds_decimals]

    return None

def text_to_odds(book_name: str, text: str, team: str, abrv: str, num_odds: int) -> list[float] | None:
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    lines = [l for l in lines if l.strip()]
    result = None
    if book_name == "stake":
        result = parse_stake(lines, team, abrv, num_odds)
    else:
        result = parse_general(lines, team, abrv, num_odds)

    if result == None:
        print(f"{book_name}: not found")
    if result and len(result) != num_odds:
        print(f"{book_name}: got {len(result)} odds, expected {num_odds}")
        return None
    return result


def main_loop(books : dict[int, Bookie], team : str, abrv : str, num_odds: int):
    executor = ProcessPoolExecutor(max_workers=len(books)) # create the process

    try:
        while True:
            full = screen_shot() # take a whole screenshot
            full = cv.cvtColor(np.array(full), cv.COLOR_RGB2BGR) # convert PIL obkect into IMG object

            iteration = int(time.time())  # rough timestamp

            futures = {
                    executor.submit(process_single, i, book.name, full): book
                    for i, book in books.items()
                } # get each of the process to execute and process the image


            for future in as_completed(futures): # the results are saved
                book = futures[future]
                try:
                    text = clean_ocr(future.result())
                    # print(f"=== {book.name} iter {iteration} ===")
                    # print(text[:200])
                    # print("===")
                    result = text_to_odds(book.name, text, team, abrv, num_odds)
                    if result:
                        book.odds = result
                    else:
                        book.odds = [0.0] * num_odds
                except Exception as e:
                    print(f"ERROR: {e}")
                    traceback.print_exc()
                    book.odds = [0.0] * num_odds

                # continue from here
                # for _, b in books.items():
                #     print(b.name, b.odds)
            margin, selected_bookies = find_best_odds(books, num_odds)
            print(f"house edge: {margin}")
            for i, b in enumerate(selected_bookies):
                print(b.name, b.odds[i])

        time.sleep(1)
    except Exception as e:
        print(f"ERROR : {e}")
    finally:
        executor.shutdown(wait=True)

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("requires 3 input")
        sys.exit()

    name1, abrv, num_odds = sys.argv[1], sys.argv[2], int(sys.argv[3])
    index_to_name_dict = build_books("websites.txt")

    main_loop(index_to_name_dict, name1, abrv, num_odds)


import subprocess
import time
import pygetwindow as gw
import pyautogui as pyauto
import ctypes
from constants import MONITOR2_X, COLS, WIN_W, WIN_H, MONITOR2_Y
import sys

ctypes.windll.user32.SetProcessDPIAware()
user32 = ctypes.windll.user32  # type: ignore
SW_RESTORE = 9
FIREFOX_PATH = r"C:\Program Files\Mozilla Firefox\firefox.exe"
BORDER = 8
def get_websites():
    webistes = []

    with open("websites.txt", 'r') as file:
        for line in file.readlines():
            webistes.append(line)

    return webistes

def open_windows() -> list[int]:

    links = get_websites()
    hwnds = []
    for i in range(6):
        col = i % COLS if COLS else 0
        row = i // COLS if COLS else i

        x = MONITOR2_X + col * WIN_W - BORDER
        y = MONITOR2_Y + row * WIN_H
        w = WIN_W + BORDER * 2
        h = WIN_H + BORDER
        # print(x, y, w, h)
        before = set(w._hWnd for w in gw.getWindowsWithTitle("Mozilla Firefox")) # this grabs every other fire fox that is open right now
        subprocess.Popen([FIREFOX_PATH,  "--new-window", links[i]]) # opens a new fire fox
        # time.sleep(1) # wait a second

        hwnd = None
        for _ in range(20):
            time.sleep(0.2)
            after = set(w._hWnd for w in gw.getWindowsWithTitle("Mozilla Firefox"))
            new = after - before
            if new:
                hwnd = new.pop()
                break

        if hwnd:

            user32.ShowWindow(hwnd, SW_RESTORE)
            user32.MoveWindow(hwnd, x, y, w, h, True)
            hwnds.append(hwnd)

    return hwnds

def close_windows(hwnds: list[int]):
    WM_CLOSE = 0x0010
    for w in hwnds:
        user32.PostMessageW(w, WM_CLOSE, 0, 0)

if __name__ == '__main__':
    hwnds = []
    while True:
        command = input("o = open fire fox, c = close fire fox, q = quit: ")
        if command == "o":
            hwnds = open_windows()
        elif command == "c":
            if hwnds:
                close_windows(hwnds)
                hwnds = []
            else:
                print("no open fire fox")
        elif command == "q":
            if hwnds:
                close_windows(hwnds)
            break
# for win in gw.getWindowsWithTitle("Mozilla Firefox"):
#     print(f"x={win.left}, y={win.top}, w={win.width}, h={win.height}")
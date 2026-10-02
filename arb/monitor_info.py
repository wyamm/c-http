from screeninfo import get_monitors
import ctypes, ctypes.wintypes
import pygetwindow as gw
from constants import WIN_W, WIN_H, MONITOR2_X, MONITOR2_Y

for m in get_monitors():
    print(m.x, m.y, m.width, m.height, "primary" if m.is_primary else "secondary")


ctypes.windll.user32.SetProcessDPIAware()
user32 = ctypes.windll.user32

hwnd = gw.getAllWindows()[0]._hWnd   # or pick a specific Firefox hwnd
w = gw.getAllWindows()[0]
print(w.topleft)
user32.ShowWindow(hwnd, 9)
user32.MoveWindow(hwnd, MONITOR2_X, MONITOR2_Y, WIN_W, WIN_H, True)
print(w.topleft)


r = ctypes.wintypes.RECT()
user32.GetWindowRect(hwnd, ctypes.byref(r))
print("asked:", WIN_W, WIN_H)
print("got:  ", r.right - r.left, r.bottom - r.top)
print("origin:", r.left, r.top)

def get_class(hwnd):
    buf = ctypes.create_unicode_buffer(256)
    user32.GetClassNameW(hwnd, buf, 256)
    return buf.value

moz = [w for w in gw.getAllWindows()
       if get_class(w._hWnd) == "MozillaWindowClass"
       and user32.IsWindowVisible(w._hWnd)
       and user32.GetWindowTextLengthW(w._hWnd) > 0]
print("real Firefox windows:", len(moz))
for w in moz:
    print(w._hWnd, repr(w.title), w.left, w.top, w.width, w.height)
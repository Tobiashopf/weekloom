"""Native Windows notification-area adapter; no shell scripts or external packages."""
import ctypes as C
from ctypes import wintypes as W
import sys
import time


def show_notification(count):
    if sys.platform != "win32":
        raise RuntimeError("Windows notifications require Windows.")

    class GUID(C.Structure):
        _fields_ = [("Data1", W.DWORD), ("Data2", W.WORD), ("Data3", W.WORD), ("Data4", C.c_ubyte * 8)]

    class IconData(C.Structure):
        _fields_ = [("cbSize", W.DWORD), ("hWnd", W.HWND), ("uID", W.UINT),
                    ("uFlags", W.UINT), ("uCallbackMessage", W.UINT), ("hIcon", W.HICON),
                    ("szTip", W.WCHAR * 128), ("dwState", W.DWORD), ("dwStateMask", W.DWORD),
                    ("szInfo", W.WCHAR * 256), ("uTimeout", W.UINT),
                    ("szInfoTitle", W.WCHAR * 64), ("dwInfoFlags", W.DWORD),
                    ("guidItem", GUID), ("hBalloonIcon", W.HICON)]

    user = C.WinDLL("user32", use_last_error=True)
    shell = C.WinDLL("shell32", use_last_error=True)
    user.CreateWindowExW.argtypes = [W.DWORD, W.LPCWSTR, W.LPCWSTR, W.DWORD,
                                    C.c_int, C.c_int, C.c_int, C.c_int,
                                    W.HWND, W.HMENU, W.HINSTANCE, W.LPVOID]
    user.CreateWindowExW.restype = W.HWND
    user.LoadIconW.argtypes = [W.HINSTANCE, C.c_void_p]
    user.LoadIconW.restype = W.HICON
    user.DestroyWindow.argtypes = [W.HWND]
    user.PeekMessageW.argtypes = [C.POINTER(W.MSG), W.HWND, W.UINT, W.UINT, W.UINT]
    user.TranslateMessage.argtypes = [C.POINTER(W.MSG)]
    user.DispatchMessageW.argtypes = [C.POINTER(W.MSG)]
    user.DispatchMessageW.restype = C.c_ssize_t
    shell.Shell_NotifyIconW.argtypes = [W.DWORD, C.POINTER(IconData)]
    shell.Shell_NotifyIconW.restype = W.BOOL
    window = user.CreateWindowExW(0, "STATIC", "Weekloom reminder", 0, 0, 0, 0, 0, None, None, None, None)
    if not window:
        raise C.WinError(C.get_last_error())
    data = IconData()
    data.cbSize = C.sizeof(IconData)
    data.hWnd, data.uID, data.uFlags = window, 1, 2 | 4 | 16
    data.hIcon = user.LoadIconW(None, 32516)
    data.szTip = data.szInfoTitle = "Weekloom"
    data.szInfo = ("Teste de notificação do Weekloom." if count == 0 else
                   f"{count} tarefa(s) precisam de sua atenção. Abra o Weekloom para revisar os prazos e lembretes.")
    data.dwInfoFlags, data.uTimeout = 1, 10000
    added = False
    try:
        added = bool(shell.Shell_NotifyIconW(0, C.byref(data)))
        if not added:
            raise RuntimeError("Windows did not accept the notification-area request.")
        deadline = time.monotonic() + 12
        message = W.MSG()
        while time.monotonic() < deadline:
            while user.PeekMessageW(C.byref(message), None, 0, 0, 1):
                user.TranslateMessage(C.byref(message))
                user.DispatchMessageW(C.byref(message))
            time.sleep(0.05)
    finally:
        if added:
            shell.Shell_NotifyIconW(2, C.byref(data))
        user.DestroyWindow(window)

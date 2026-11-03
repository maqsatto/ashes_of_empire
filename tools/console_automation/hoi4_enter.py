"""Send a hardware-style Enter scan-code to foreground Hearts of Iron IV.

Windows only; no third-party Python packages. Use this only while the in-game
console is focused. The program verifies the active window is hoi4.exe and
reports only whether input was submitted to Windows, not whether HOI4 executed
any command.

Examples:
  python tools/hoi4_enter.py
  python tools/hoi4_enter.py --wait 8 --hold-ms 100
  python tools/hoi4_enter.py --numpad
"""
from __future__ import annotations

import argparse
import ctypes
from ctypes import wintypes
import os
import sys
import time


def scan_code_for(key: str) -> int:
    return {"enter": 0x1C, "console": 0x29}[key]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--clear-line', action='store_true', help='Send held Backspace pulses to clear the visibly open console input; does not execute a command.')
    parser.add_argument('--pause-key', action='store_true', help='Send the Space scan-code to toggle game pause; console must be closed. Inspect the result.')
    parser.add_argument('--text', help='Type ASCII letters, digits, space, underscore and dot into a visibly focused HOI4 field; does not send Enter.')
    parser.add_argument("--wait", type=float, default=5.0,
                        help="seconds to wait for HOI4 to be the active window (default: 5)")
    parser.add_argument("--hold-ms", type=int, default=90,
                        help="milliseconds to hold Enter before release (default: 90)")
    parser.add_argument("--numpad", action="store_true",
                        help="send the extended Numpad Enter scan-code instead")
    parser.add_argument("--console-key", action="store_true",
                        help="send the physical grave key to toggle the console")
    args = parser.parse_args()
    if sys.platform != "win32":
        print("ERROR: This script only works on native Windows.", file=sys.stderr)
        return 2
    if args.numpad and args.console_key:
        parser.error("--numpad and --console-key cannot be combined")
    if args.wait < 0 or not 15 <= args.hold_ms <= 1000:
        parser.error("--wait must be nonnegative and --hold-ms must be 15..1000")

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

    user32.GetForegroundWindow.restype = wintypes.HWND
    user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    user32.GetWindowThreadProcessId.restype = wintypes.DWORD
    kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel32.OpenProcess.restype = wintypes.HANDLE
    kernel32.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD,
                                                    wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
    kernel32.QueryFullProcessImageNameW.restype = wintypes.BOOL
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL
    user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    user32.GetWindowTextW.restype = ctypes.c_int

    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000

    def foreground_exe() -> tuple[str, str]:
        hwnd = user32.GetForegroundWindow()
        if not hwnd:
            return "", "No active window"
        title_buf = ctypes.create_unicode_buffer(512)
        user32.GetWindowTextW(hwnd, title_buf, len(title_buf))
        title = title_buf.value
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        process = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid.value)
        if not process:
            return "", f"PID={pid.value}, title={title!r}, executable inaccessible"
        try:
            buf = ctypes.create_unicode_buffer(32768)
            length = wintypes.DWORD(len(buf))
            if kernel32.QueryFullProcessImageNameW(process, 0, buf, ctypes.byref(length)):
                path = buf.value
                return os.path.basename(path).lower(), f"PID={pid.value}, title={title!r}, exe={path!r}"
            return "", f"PID={pid.value}, title={title!r}, executable query failed"
        finally:
            kernel32.CloseHandle(process)

    deadline = time.monotonic() + args.wait
    while True:
        exe, context = foreground_exe()
        if exe == "hoi4.exe":
            break
        if time.monotonic() >= deadline:
            print(f"ERROR: HOI4 is not the active window. {context}", file=sys.stderr)
            print("Activate the running game and make sure its console is open. "
                  "Do not type into another app.", file=sys.stderr)
            return 3
        time.sleep(0.15)

    # Use native-sized structures. INPUT's union MUST include MOUSEINPUT,
    # otherwise SendInput receives the wrong cbSize on 64-bit Windows.
    class MOUSEINPUT(ctypes.Structure):
        _fields_ = [("dx", ctypes.c_int32), ("dy", ctypes.c_int32),
                    ("mouseData", ctypes.c_uint32), ("dwFlags", ctypes.c_uint32),
                    ("time", ctypes.c_uint32), ("dwExtraInfo", ctypes.c_size_t)]

    class KEYBDINPUT(ctypes.Structure):
        _fields_ = [("wVk", ctypes.c_uint16), ("wScan", ctypes.c_uint16),
                    ("dwFlags", ctypes.c_uint32), ("time", ctypes.c_uint32),
                    ("dwExtraInfo", ctypes.c_size_t)]

    class HARDWAREINPUT(ctypes.Structure):
        _fields_ = [("uMsg", ctypes.c_uint32), ("wParamL", ctypes.c_uint16),
                    ("wParamH", ctypes.c_uint16)]

    class INPUTUNION(ctypes.Union):
        _fields_ = [("mi", MOUSEINPUT), ("ki", KEYBDINPUT), ("hi", HARDWAREINPUT)]

    class INPUT(ctypes.Structure):
        _fields_ = [("type", ctypes.c_uint32), ("u", INPUTUNION)]

    user32.SendInput.argtypes = [wintypes.UINT, ctypes.POINTER(INPUT), ctypes.c_int]
    user32.SendInput.restype = wintypes.UINT

    KEYEVENTF_EXTENDEDKEY = 0x0001
    KEYEVENTF_KEYUP = 0x0002
    KEYEVENTF_SCANCODE = 0x0008

    if args.text is not None:
        if any(not (c.isascii() and (c.isalnum() or c in ' _.')) for c in args.text):
            print('ERROR: Unsupported text character.', file=sys.stderr)
            return 2
        def raw(scan, up=False):
            event = INPUT()
            event.type = 1
            event.u.ki = KEYBDINPUT(0, scan, KEYEVENTF_SCANCODE | (KEYEVENTF_KEYUP if up else 0), 0, 0)
            return user32.SendInput(1, ctypes.byref(event), ctypes.sizeof(INPUT)) == 1
        for c in args.text:
            if foreground_exe()[0] != 'hoi4.exe':
                return 3
            shifted = c == '_' or c.isupper()
            vk = 0xBD if c == '_' else 0xBE if c == '.' else 0x20 if c == ' ' else ord(c.upper())
            scan = user32.MapVirtualKeyW(vk, 0)
            if shifted:
                raw(0x2A)
            if not raw(scan):
                return 4
            time.sleep(0.035)
            raw(scan, True)
            if shifted:
                raw(0x2A, True)
            time.sleep(0.035)
        print('SENT text only; verify the visible input before submitting.')
        return 0

    def send_key(is_keyup: bool) -> bool:
        flags = KEYEVENTF_SCANCODE
        if args.numpad:
            flags |= KEYEVENTF_EXTENDEDKEY
        if is_keyup:
            flags |= KEYEVENTF_KEYUP
        event = INPUT()
        event.type = 1  # INPUT_KEYBOARD
        scan = 0x0E if args.clear_line else 0x39 if args.pause_key else scan_code_for("console" if args.console_key else "enter")
        event.u.ki = KEYBDINPUT(0, scan, flags, 0, 0)
        ctypes.set_last_error(0)
        count = user32.SendInput(1, ctypes.byref(event), ctypes.sizeof(INPUT))
        if count != 1:
            error = ctypes.get_last_error()
            print(f"ERROR: SendInput returned {count}, GetLastError={error}.", file=sys.stderr)
            print("Possible causes: no access to interactive desktop, mismatched "
                  "elevation/integrity, or sandbox restrictions.", file=sys.stderr)
            return False
        return True

    if args.clear_line:
        for _ in range(100):
            if foreground_exe()[0] != 'hoi4.exe':
                return 3
            if not send_key(False):
                return 4
            time.sleep(0.025)
            if not send_key(True):
                return 4
            time.sleep(0.025)
        print('SENT Backspace pulses; verify the console input is empty.')
        return 0
    if not send_key(False):
        return 4
    try:
        time.sleep(args.hold_ms / 1000.0)
    finally:
        if not send_key(True):
            return 4
    label = 'Space' if args.pause_key else 'console' if args.console_key else 'Enter'
    print(f"SENT {label} scan-code to foreground HOI4 ({context}). "
          "Verify in the game that the command executed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Windows 11の最前面アプリ名とウィンドウタイトルを記録する。標準ライブラリのみ使用する。"""
import ctypes as C
from ctypes import wintypes as W
from datetime import datetime
from pathlib import Path
import sys

INTERVAL_MS = 1000
EVENT_NAME = r"Local\MinimalForegroundLogger.Stop.v1"


def main():
    """ロガーの起動・停止を処理し、デスクトップ上のログへ状態変化を追記する。"""
    if sys.platform != "win32":
        raise SystemExit("Windows only")
    kernel = C.WinDLL("kernel32", use_last_error=True)
    user = C.WinDLL("user32", use_last_error=True)
    shell = C.WinDLL("shell32", use_last_error=True)

    def bind(dll, name, result, *args):
        fn = getattr(dll, name)
        fn.restype, fn.argtypes = result, args
        return fn

    close = bind(kernel, "CloseHandle", W.BOOL, W.HANDLE)
    create_event = bind(kernel, "CreateEventW", W.HANDLE, W.LPVOID, W.BOOL, W.BOOL, W.LPCWSTR)
    open_event = bind(kernel, "OpenEventW", W.HANDLE, W.DWORD, W.BOOL, W.LPCWSTR)
    set_event = bind(kernel, "SetEvent", W.BOOL, W.HANDLE)
    wait = bind(kernel, "WaitForSingleObject", W.DWORD, W.HANDLE, W.DWORD)
    foreground = bind(user, "GetForegroundWindow", W.HWND)
    window_pid = bind(user, "GetWindowThreadProcessId", W.DWORD, W.HWND, C.POINTER(W.DWORD))
    window_text = bind(user, "GetWindowTextW", C.c_int, W.HWND, W.LPWSTR, C.c_int)
    open_process = bind(kernel, "OpenProcess", W.HANDLE, W.DWORD, W.BOOL, W.DWORD)
    image_name = bind(kernel, "QueryFullProcessImageNameW", W.BOOL, W.HANDLE, W.DWORD, W.LPWSTR, C.POINTER(W.DWORD))
    desktop_path = bind(shell, "SHGetFolderPathW", C.c_long, W.HWND, C.c_int, W.HANDLE, W.DWORD, W.LPWSTR)
    current_process = bind(kernel, "GetCurrentProcess", W.HANDLE)
    priority = bind(kernel, "SetPriorityClass", W.BOOL, W.HANDLE, W.DWORD)

    if sys.argv[1:] == ["--stop"]:
        event = open_event(0x0002, False, EVENT_NAME)  # EVENT_MODIFY_STATE
        if event:
            try:
                if not set_event(event):
                    raise C.WinError(C.get_last_error())
            finally:
                close(event)
        return
    if sys.argv[1:]:
        raise SystemExit("Usage: foreground_logger.py [--stop]")

    event = create_event(None, True, False, EVENT_NAME)
    if not event:
        raise C.WinError(C.get_last_error())
    if C.get_last_error() == 183:  # ERROR_ALREADY_EXISTS: another copy owns it
        close(event)
        return

    try:
        priority(current_process(), 0x00004000)  # BELOW_NORMAL_PRIORITY_CLASS
        buffer = C.create_unicode_buffer(260)
        hr = desktop_path(None, 0x0010, None, 0, buffer)  # CSIDL_DESKTOPDIRECTORY
        if hr != 0:
            raise OSError(f"Desktop lookup failed: HRESULT {hr:#x}")
        log_path = Path(buffer.value) / "foreground.log"
        name_buffer = C.create_unicode_buffer(32768)
        title_buffer = C.create_unicode_buffer(32768)
        previous_pid = None
        previous_state = None
        app = None

        # Line buffering flushes each event; no writes while the app is unchanged.
        with log_path.open("a", encoding="utf-8", buffering=1) as log:
            def write(kind, app_name="", title=""):
                """現在時刻、イベント、アプリ名、タイトルをTSV形式で追記する。"""
                stamp = datetime.now().astimezone().isoformat(timespec="seconds")
                safe_title = " ".join(title.splitlines()).replace("\t", " ")
                log.write(f"{stamp}\t{kind}\t{app_name}\t{safe_title}\n")

            write("START")
            try:
                while True:
                    hwnd = foreground()
                    pid = W.DWORD()
                    if hwnd:
                        window_pid(hwnd, C.byref(pid))
                    if pid.value != previous_pid:
                        app = "NO_FOREGROUND" if not pid.value else "UNKNOWN"
                        process = open_process(0x1000, False, pid.value) if pid.value else None
                        if process:
                            try:
                                size = W.DWORD(len(name_buffer))
                                if image_name(process, 0, name_buffer, C.byref(size)):
                                    app = Path(name_buffer.value).name
                            finally:
                                close(process)
                        previous_pid = pid.value
                    title = ""
                    if hwnd and window_text(hwnd, title_buffer, len(title_buffer)):
                        title = title_buffer.value
                    state = (app, title)
                    if state != previous_state:
                        write("APP", app, title)
                        previous_state = state
                    result = wait(event, INTERVAL_MS)
                    if result == 0:
                        break
                    if result != 258:  # WAIT_TIMEOUT
                        raise C.WinError(C.get_last_error())
            except KeyboardInterrupt:
                pass
            finally:
                write("STOP")
    finally:
        close(event)


if __name__ == "__main__":
    main()

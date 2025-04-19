import ctypes
import ctypes.wintypes as wintypes
import time

def get_foreground_event_observer(tracker):
    user32 = ctypes.WinDLL('user32', use_last_error=True)
    winevent_out_of_context = 0x0000
    event_system_foreground = 0x0003

    win_event_proc_type = ctypes.WINFUNCTYPE(
        None,
        wintypes.HANDLE,
        wintypes.DWORD,
        wintypes.HWND,
        wintypes.LONG,
        wintypes.LONG,
        wintypes.DWORD,
        wintypes.DWORD
    )

    def handle_foreground_event(hWinEventHook, event, hwnd, idObject, idChild, dwEventThread, dwmsEventTime):
        time.sleep(0.2)
        tracker.current_foreground_hwnd = hwnd

    win_event_proc = win_event_proc_type(handle_foreground_event)

    def set_foreground_hook():
        hook = user32.SetWinEventHook(
            event_system_foreground, event_system_foreground,
            0,
            win_event_proc,
            0, 0,
            winevent_out_of_context
        )
        if not hook:
            raise ctypes.WinError(ctypes.get_last_error())
        return hook

    def observer_function():
        hook = set_foreground_hook()
        msg = wintypes.MSG()
        while user32.GetMessageW(ctypes.byref(msg), 0, 0, 0) != 0:
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))
            time.sleep(0.1)
        user32.UnhookWinEvent(hook)

    return observer_function
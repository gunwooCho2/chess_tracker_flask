import os
import mss
import cv2
import numpy as np
import time
from dataclasses import dataclass
import json
import threading

from chess.chess_tracker_util import where_chess_board, BoardChangeDetection, is_chess_board
from chess.window_hook import get_foreground_event_observer


class ChessTrackerError(Exception):
    def __init__(self, code, message):
        self.code = code
        self.message = message
        super().__init__(f"[{code}] {message}")

@dataclass
class BoardInfo:
    coords: tuple or None = None
    location_window_hwnd: int = 0

@dataclass
class AppState:
    is_top: bool = False
    coords: tuple or None = None

class ChessTracker:
    def __init__(self):
        self.board_info = BoardInfo()
        self._observer_running = False
        self.main_monitor_num = 0
        self.app_state = AppState()
        self.current_foreground_hwnd = 0
        self.shells_center = np.full((64, 64, 3), 0).astype(np.uint8)
        self.notations = []
        self.chess_pattern = None
        self.board_change_detection = BoardChangeDetection()

    def set_app_state(self, app_state: dict) -> None:
        self.app_state.coords = app_state['coords']
        self.app_state.is_top = app_state['is_top']

    def _observer(self, sct, observing_monitors, run_function, sleep_time: float) -> None:
        self._observer_running = True
        while self._observer_running:
            for index, observing_monitor in enumerate(observing_monitors):
                screenshot = sct.grab(observing_monitor)
                monitor_image = np.array(screenshot)

                if self.app_state.is_top:
                    app_coords = self.app_state.coords
                    monitor_image[app_coords[0]:app_coords[1], app_coords[2]:app_coords[3]] = np.array([0, 0, 0]).astype(np.uint8)

                run_function(monitor_image, index)
                if sleep_time > 0:
                    time.sleep(sleep_time)

    def find_chess_board(self):
        self.board_info.coords = None

        def _find_chess_board(monitor_image, index):
            chess_board_info = where_chess_board(monitor_image, self)

            if chess_board_info[0]:
                self.board_info.coords = chess_board_info[1]
                self.main_monitor_num = index
                self._observer_running = False
                self.board_info.location_window_hwnd = self.current_foreground_hwnd
                self.board_observer()

        with mss.mss() as sct:
            monitors = sct.monitors
            monitor_count = len(monitors) - 1
            observing_monitors = [monitors[i] for i in range(1, monitor_count + 1)]
            self._observer(sct, observing_monitors, _find_chess_board, 1)

    def board_observer(self):
        print(self.board_info.coords)
        def _board_observer(monitor_image, index):
            if self.board_info.location_window_hwnd != self.current_foreground_hwnd:
                return
            start_y, end_y, start_x, end_x = self.board_info.coords
            board_image = monitor_image[start_y:end_y, start_x:end_x]
            board_image = cv2.cvtColor(board_image, cv2.COLOR_BGRA2BGR)

            if not is_chess_board(board_image, self):
                self._observer_running = False
                self.find_chess_board()
                return
            self.board_change_detection.detection(board_image, self)

        with mss.mss() as sct:
            monitors = sct.monitors
            main_monitor = [monitors[self.main_monitor_num]]
            self._observer(sct, main_monitor, _board_observer, 0.1)

    def end(self, notation_dir_path):
        current_time = time.strftime("%Y%m%d_%H%M%S", time.localtime())
        save_data = {
            "notations": self.notations,
        }
        file_name = f"{current_time}.json"
        file_path = os.path.join(notation_dir_path, file_name)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(save_data, f, indent=4)

if __name__ == "__main__":
    chess_tracker_obj = ChessTracker()
    foreground_observer = get_foreground_event_observer(chess_tracker_obj)
    hook_thread = threading.Thread(target=foreground_observer, daemon=True)
    hook_thread.start()

    chess_tracker_obj.find_chess_board()












import time

import cv2
import numpy as np
from dataclasses import dataclass, field

from flask_util import load_json

board_pattern_datas = load_json("patterns.json")

def get_edge_image(image: np.ndarray) -> np.ndarray:
    threshold_val = 127

    edge_filter = np.array([
        [-1, -1, -1],
        [-1, 8, -1],
        [-1, -1, -1],
    ])
    edge_image = cv2.filter2D(image, -1, edge_filter)
    return cv2.threshold(edge_image, threshold_val, 255, cv2.THRESH_BINARY)[1]

def apply_chess_filter(image: np.ndarray, filter_patterns) -> np.ndarray:
    h, w = image.shape[:2]
    filter_patterns = np.array(filter_patterns)

    def _filter_apply(image: np.ndarray, apply_filter: np.ndarray, pattern_val: int) -> np.ndarray:
        filtered_image = cv2.filter2D(image, -1, apply_filter)
        filtered_image[filtered_image != pattern_val] = 0
        filtered_image[filtered_image != 0] = 1
        return filtered_image

    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    edge_image = get_edge_image(gray_image)
    edge_image[edge_image == 255] = 1
    black_image = np.zeros((h, w), np.uint8)

    filtered_images = [_filter_apply(edge_image, cross_filter, 6) for cross_filter in filter_patterns]
    for filtered_image in filtered_images:
        black_image[filtered_image == 1] = 1

    return black_image

def where_chess_board(recorded_image: np.ndarray, tracker) -> (bool, (int, int, int, int)) or (bool, None):
    def _check_indies(indies: np.ndarray) -> np.ndarray or None:
        indies, count = np.unique(indies, return_counts=True)
        indies = indies[count >= 7]
        if np.sum(indies) == 0:
            return None

        diff = np.diff(np.diff(indies))
        leading_false_count = np.argmax(diff)
        trailing_false_count = np.argmax(diff[::-1])

        indies = indies[leading_false_count:]
        if trailing_false_count > 0:
            indies = indies[:-trailing_false_count]
        return indies

    def _check_is_board(filtered_image: np.ndarray) -> (int, int, int, int) or None:
        if np.sum(filtered_image) < 49:
            return None

        y_indies, x_indies = np.where(black_image == 1)
        y_indies, x_indies = _check_indies(y_indies), _check_indies(x_indies)

        if x_indies is None or y_indies is None:
            return None

        x_diff = x_indies[1] - x_indies[0]
        y_diff = y_indies[1] - y_indies[0]

        if x_diff != y_diff:
            return None

        y_start = min(y_indies) - y_diff
        y_end = max(y_indies) + y_diff
        x_start = min(x_indies) - x_diff
        x_end = max(x_indies) + x_diff
        return y_start, y_end, x_start, x_end

    for pattern in board_pattern_datas:
        black_image = apply_chess_filter(recorded_image, pattern)
        check_info = _check_is_board(black_image)
        if check_info is not None:
            tracker.chess_pattern = pattern
            return True, check_info

    return False, None

def is_chess_board(recorded_image: np.ndarray, tracker) -> bool:
    black_image = apply_chess_filter(recorded_image, tracker.chess_pattern)
    return 49 == np.sum(black_image)

@dataclass
class BoardChangeDetection:
    shell_size: int or None = None
    board_mask: np.ndarray or None = None
    board_pattern: np.ndarray or None = None
    prev_image: np.ndarray or None = None

    def _set_board_mask(self, recorded_image: np.ndarray) -> None:
        pixels = recorded_image.reshape(-1, 3)
        unique_colors, counts = np.unique(pixels, axis=0, return_counts=True)
        order = np.argsort(counts)[::-1]
        top_colors = unique_colors[order]
        top1, top2 = top_colors[:2]

        mask2d = (np.all(recorded_image == top1, axis=2) |
                  np.all(recorded_image == top2, axis=2))
        mask3d = mask2d[:, :, None]

        self.board_mask = mask3d.astype(np.uint8)

    def detection(self, recorded_image: np.ndarray, tracker) -> None:
        def _compression_image(image: np.ndarray) -> np.ndarray:
            blocks = image.reshape(self.shell_size,8,self.shell_size,8)
            return blocks.any(axis=(2, 3))

        gray = cv2.cvtColor(recorded_image, cv2.COLOR_BGR2GRAY)

        if self.shell_size is None:
            self.shell_size = recorded_image.shape[:2][0] // 8
            self.prev_image = gray
            self._set_board_mask(recorded_image)
            return

        changed_mask = self.prev_image != gray
        pool_mask = _compression_image(changed_mask)

        if np.sum(pool_mask) == 2:
            filtered = recorded_image * self.board_mask
            gray_filtered = cv2.cvtColor(filtered, cv2.COLOR_BGR2GRAY)
            pool_mask = _compression_image(gray_filtered)

            if np.sum(pool_mask) == 62:
                ys, xs = np.where(pool_mask == 0)
                coords_list = list(zip(ys, xs))
                print(coords_list)


if __name__ == '__main__':
    a = 0


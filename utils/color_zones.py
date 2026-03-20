"""
utils/color_zones.py
Renders the top header strip with colour swatches, eraser, and size controls.
"""

import cv2
import numpy as np
from typing import Optional, Tuple


# Palette: (BGR, display-name)
PALETTE = [
    ((255,  50,  50), "Red"),
    ((50,  120, 255), "Blue"),
    ((50,  220,  50), "Green"),
    ((0,  220, 220), "Cyan"),
    ((220,  50, 220), "Magenta"),
    ((0,  200, 255), "Yellow"),
    ((255, 160,  20), "Orange"),
    ((160,  30, 255), "Purple"),
    ((255, 255, 255), "White"),
    ((30,   30,  30), "Black"),
]


class ColorZones:
    """
    Builds the header UI strip and maps pixel coordinates to actions.
    """

    def __init__(self, canvas_w: int, header_h: int):
        self.canvas_w = canvas_w
        self.header_h = header_h
        self._zones: list[dict] = []   # [{x1,x2,y1,y2,action}]
        self._build_zones()

    # ──────────────────────────────────────────
    def _build_zones(self):
        pad = 10
        swatch_size = self.header_h - 2 * pad
        total_items = len(PALETTE) + 3   # palette + eraser + size+/-
        spacing = (self.canvas_w - 2 * pad) // total_items
        x = pad

        for bgr, name in PALETTE:
            self._zones.append(dict(
                x1=x, y1=pad, x2=x + swatch_size, y2=pad + swatch_size,
                action=bgr, label=name,
            ))
            x += spacing

        # Eraser zone
        self._zones.append(dict(
            x1=x, y1=pad, x2=x + swatch_size, y2=pad + swatch_size,
            action="__ERASER__", label="Erase",
        ))
        x += spacing

        # Size − zone
        self._zones.append(dict(
            x1=x, y1=pad, x2=x + swatch_size // 2, y2=pad + swatch_size,
            action="__SIZE_DN__", label="-",
        ))
        x += spacing // 2

        # Size + zone
        self._zones.append(dict(
            x1=x, y1=pad, x2=x + swatch_size // 2, y2=pad + swatch_size,
            action="__SIZE_UP__", label="+",
        ))

    # ──────────────────────────────────────────
    def render_header(self, active_color: tuple, brush_size: int) -> np.ndarray:
        """Return a rendered header numpy image (header_h × canvas_w × 3)."""
        header = np.zeros((self.header_h, self.canvas_w, 3), dtype=np.uint8)
        # Dark background
        header[:] = (18, 18, 28)
        # Subtle gradient line at bottom
        header[-3:, :] = (60, 60, 80)

        for z in self._zones:
            x1, y1, x2, y2 = z["x1"], z["y1"], z["x2"], z["y2"]
            act = z["action"]

            if act == "__ERASER__":
                bgr = (40, 40, 55)
                cv2.rectangle(header, (x1, y1), (x2, y2), bgr, -1, cv2.LINE_AA)
                cv2.rectangle(header, (x1, y1), (x2, y2), (180, 180, 200), 1)
                cv2.putText(header, "⌫", (x1 + 4, y2 - 8),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.55, (220, 220, 255), 1, cv2.LINE_AA)

            elif act in ("__SIZE_UP__", "__SIZE_DN__"):
                sym = "+" if act == "__SIZE_UP__" else "-"
                cv2.rectangle(header, (x1, y1), (x2, y2), (35, 55, 80), -1)
                cv2.rectangle(header, (x1, y1), (x2, y2), (80, 120, 180), 1)
                cv2.putText(header, sym, (x1 + 8, y2 - 8),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (180, 220, 255), 2, cv2.LINE_AA)

            else:
                # Colour swatch
                cv2.rectangle(header, (x1, y1), (x2, y2), act, -1, cv2.LINE_AA)
                # Highlight active colour
                if tuple(act) == tuple(active_color):
                    cv2.rectangle(header, (x1 - 2, y1 - 2), (x2 + 2, y2 + 2),
                                  (255, 255, 255), 3, cv2.LINE_AA)
                else:
                    cv2.rectangle(header, (x1, y1), (x2, y2), (80, 80, 80), 1)

        # Brush-size preview
        bx, by = self.canvas_w - 60, self.header_h // 2
        cv2.circle(header, (bx, by), brush_size, active_color, -1, cv2.LINE_AA)
        cv2.circle(header, (bx, by), brush_size, (200, 200, 200), 1, cv2.LINE_AA)

        # Label
        cv2.putText(header, "GesturePainter", (10, self.header_h - 10),
                    cv2.FONT_HERSHEY_DUPLEX, 0.55, (120, 120, 160), 1, cv2.LINE_AA)

        return header

    # ──────────────────────────────────────────
    def pick_color(self, px: int, py: int) -> Optional[object]:
        """
        Return BGR tuple, '__ERASER__', '__SIZE_UP__', '__SIZE_DN__',
        or None if no zone was hit.
        """
        for z in self._zones:
            if z["x1"] <= px <= z["x2"] and z["y1"] <= py <= z["y2"]:
                return z["action"]
        return None

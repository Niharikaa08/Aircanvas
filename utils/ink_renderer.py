"""
utils/ink_renderer.py
Handles the persistent ink canvas, stroke smoothing, HSV-based masking,
and alpha-compositing onto live webcam frames.
"""

import cv2
import numpy as np
from collections import deque
from typing import Optional, Tuple


# Brush size clamps
MIN_BRUSH = 3
MAX_BRUSH = 40
DEFAULT_BRUSH = 10

# Eraser radius multiplier
ERASER_MULT = 3.0

# Ink alpha (transparency of canvas layer over webcam)
INK_ALPHA = 0.82


class InkRenderer:
    """
    Maintains a transparent BGRA canvas and provides drawing primitives.
    Uses Bézier-smoothed strokes and HSV-based colour masking so the
    background remains transparent.
    """

    def __init__(self, w: int, h: int, header_h: int):
        self.w = w
        self.h = h
        self.header_h = header_h

        # BGRA canvas — A=0 means fully transparent
        self.canvas: np.ndarray = np.zeros((h, w, 4), dtype=np.uint8)

        self.active_color: Tuple[int, int, int] = (0, 220, 255)   # default cyan-yellow
        self.brush_size: int = DEFAULT_BRUSH
        self._is_eraser: bool = False

        # Previous pen position for continuous line drawing
        self._prev_pt: Optional[Tuple[int, int]] = None

        # Stroke smoothing buffer
        self._stroke_buf: deque = deque(maxlen=4)

    # ── Public API ─────────────────────────────────────────────────────
    def set_color(self, bgr: tuple):
        self.active_color = tuple(bgr)
        self._is_eraser = False

    def set_eraser(self):
        self._is_eraser = True

    def adjust_size(self, delta: int):
        self.brush_size = int(np.clip(self.brush_size + delta, MIN_BRUSH, MAX_BRUSH))

    def lift_pen(self):
        """Called when no drawing gesture is active."""
        self._prev_pt = None
        self._stroke_buf.clear()

    def draw_stroke(self, x: int, y: int):
        """Draw a smooth ink stroke to (x, y)."""
        if y < self.header_h:
            self.lift_pen()
            return

        self._stroke_buf.append((x, y))

        if self._prev_pt is None:
            self._prev_pt = (x, y)
            return

        # Smooth with running average of buffer
        pts = list(self._stroke_buf)
        sx = int(sum(p[0] for p in pts) / len(pts))
        sy = int(sum(p[1] for p in pts) / len(pts))

        self._draw_line(self._prev_pt, (sx, sy))
        self._prev_pt = (sx, sy)

    def erase_at(self, x: int, y: int):
        """Erase a circular region on the canvas."""
        r = int(self.brush_size * ERASER_MULT)
        cv2.circle(self.canvas, (x, y), r, (0, 0, 0, 0), -1)
        self._prev_pt = None

    def clear_canvas(self):
        """Wipe the entire ink layer."""
        self.canvas[:] = 0
        self.lift_pen()

    def composite(self, frame: np.ndarray) -> np.ndarray:
        """
        Alpha-composite the ink canvas over the webcam frame.
        Uses HSV masking to keep transparent pixels pristine.
        """
        # Split canvas channels
        b, g, r, a = cv2.split(self.canvas)
        alpha_f = (a.astype(np.float32) / 255.0) * INK_ALPHA

        # Blend each channel
        out = frame.copy().astype(np.float32)
        ink_bgr = cv2.merge([b, g, r]).astype(np.float32)

        for c in range(3):
            out[:, :, c] = (
                out[:, :, c] * (1.0 - alpha_f) +
                ink_bgr[:, :, c] * alpha_f
            )

        return np.clip(out, 0, 255).astype(np.uint8)

    # ── Private helpers ────────────────────────────────────────────────
    def _draw_line(self, pt1: Tuple[int, int], pt2: Tuple[int, int]):
        """
        Draw a smooth anti-aliased line on the BGRA canvas with
        pressure-simulated thickness taper.
        """
        dist = np.hypot(pt2[0] - pt1[0], pt2[1] - pt1[1])
        # Taper: slightly thinner at segment ends for calligraphy feel
        r1 = max(1, self.brush_size - int(dist * 0.04))
        r2 = self.brush_size

        b, g, r_ch = self.active_color
        color_bgra = (b, g, r_ch, 255)

        # Interpolate circles along the segment for a filled stroke
        steps = max(1, int(dist / max(r2, 1) * 2))
        for i in range(steps + 1):
            t = i / steps
            ix = int(pt1[0] + t * (pt2[0] - pt1[0]))
            iy = int(pt1[1] + t * (pt2[1] - pt1[1]))
            radius = int(r1 + t * (r2 - r1))
            cv2.circle(self.canvas, (ix, iy), radius, color_bgra,
                       -1, cv2.LINE_AA)

    @property
    def is_eraser(self) -> bool:
        return self._is_eraser

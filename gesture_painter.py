"""
GesturePainter — Real-time hand-landmark drawing app
Uses the NEW MediaPipe Tasks API (compatible with mediapipe 0.10+ / Python 3.13)
Pipeline: Capture → Detect → Track → Render
"""

import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision as mp_vision
from mediapipe.tasks.python.components import containers as mp_containers
import time
import math
import urllib.request
import os
from collections import deque
from utils.color_zones import ColorZones
from utils.gesture_state import GestureStateMachine
from utils.ink_renderer import InkRenderer


# ─────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────
CANVAS_W, CANVAS_H = 1280, 720
HEADER_H = 120
SMOOTHING_WINDOW = 6
FPS_SMOOTH = 20

# Landmark indices
LM_WRIST       = 0
LM_THUMB_TIP   = 4
LM_INDEX_TIP   = 8
LM_INDEX_MCP   = 5
LM_MIDDLE_TIP  = 12
LM_MIDDLE_MCP  = 9
LM_RING_TIP    = 16
LM_RING_MCP    = 13
LM_PINKY_TIP   = 20
LM_PINKY_MCP   = 17

MODEL_PATH = "hand_landmarker.task"
MODEL_URL  = (
    "https://storage.googleapis.com/mediapipe-models/"
    "hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task"
)


def download_model():
    if not os.path.exists(MODEL_PATH):
        print("[INFO] Downloading hand_landmarker.task model (~5 MB)…")
        urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
        print("[INFO] Model downloaded successfully.")
    else:
        print("[INFO] Model file found locally.")


def finger_is_up(landmarks, tip_id, mcp_id):
    return landmarks[tip_id].y < landmarks[mcp_id].y


def euclidean(p1, p2, w, h):
    return math.hypot((p1.x - p2.x) * w, (p1.y - p2.y) * h)


# ─────────────────────────────────────────────
# Main App
# ─────────────────────────────────────────────
def run():
    download_model()

    # ── MediaPipe Tasks setup (new API) ──────
    base_options = mp_python.BaseOptions(model_asset_path=MODEL_PATH)
    options = mp_vision.HandLandmarkerOptions(
        base_options=base_options,
        running_mode=mp_vision.RunningMode.VIDEO,
        num_hands=1,
        min_hand_detection_confidence=0.7,
        min_hand_presence_confidence=0.7,
        min_tracking_confidence=0.6,
    )
    landmarker = mp_vision.HandLandmarker.create_from_options(options)

    # Skeleton drawing removed — mp.solutions unavailable in mediapipe 0.10+

    # ── OpenCV capture ───────────────────────
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  CANVAS_W)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CANVAS_H)
    cap.set(cv2.CAP_PROP_FPS, 60)

    if not cap.isOpened():
        print("[ERROR] Cannot open webcam.")
        return

    # ── App components ───────────────────────
    color_zones   = ColorZones(CANVAS_W, HEADER_H)
    state_machine = GestureStateMachine()
    renderer      = InkRenderer(CANVAS_W, CANVAS_H, HEADER_H)

    x_buf = deque(maxlen=SMOOTHING_WINDOW)
    y_buf = deque(maxlen=SMOOTHING_WINDOW)
    fps_buf   = deque(maxlen=FPS_SMOOTH)
    prev_time = time.time()
    frame_ts  = 0  # millisecond timestamp for VIDEO mode

    print("┌─────────────────────────────────────────┐")
    print("│        GesturePainter  ✋🎨              │")
    print("├─────────────────────────────────────────┤")
    print("│  ☝  Index up only     → DRAW             │")
    print("│  ✌  Index + Middle up → SELECT / HOVER   │")
    print("│  ✊  Fist (0 fingers)  → ERASE stroke     │")
    print("│  🤙  Pinky only up    → CLEAR canvas      │")
    print("│  [S]                  → Save canvas PNG   │")
    print("│  [Q] or [ESC]         → Quit              │")
    print("└─────────────────────────────────────────┘")

    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        frame    = cv2.flip(frame, 1)
        h, w     = frame.shape[:2]
        frame_ts += 33  # ~30 fps timestamp increment (ms)

        # ── MediaPipe Tasks inference ────────
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image  = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=rgb_frame,
        )
        result = landmarker.detect_for_video(mp_image, frame_ts)

        # ── Draw colour-zone header ──────────
        header = color_zones.render_header(renderer.active_color,
                                           renderer.brush_size)
        frame[:HEADER_H, :] = header

        ix_smooth, iy_smooth = None, None

        if result.hand_landmarks:
            lm = result.hand_landmarks[0]   # list of NormalizedLandmark

            ix_raw = int(lm[LM_INDEX_TIP].x * w)
            iy_raw = int(lm[LM_INDEX_TIP].y * h)

            x_buf.append(ix_raw)
            y_buf.append(iy_raw)
            ix_smooth = int(sum(x_buf) / len(x_buf))
            iy_smooth = int(sum(y_buf) / len(y_buf))

            # ── Gesture classification ───────
            idx_up = finger_is_up(lm, LM_INDEX_TIP,  LM_INDEX_MCP)
            mid_up = finger_is_up(lm, LM_MIDDLE_TIP, LM_MIDDLE_MCP)
            rng_up = finger_is_up(lm, LM_RING_TIP,   LM_RING_MCP)
            pnk_up = finger_is_up(lm, LM_PINKY_TIP,  LM_PINKY_MCP)

            fingers_up = sum([idx_up, mid_up, rng_up, pnk_up])

            if fingers_up == 0:
                gesture = "ERASE"
            elif idx_up and mid_up and not rng_up and not pnk_up:
                gesture = "SELECT"
            elif idx_up and not mid_up and not rng_up and not pnk_up:
                gesture = "DRAW"
            elif pnk_up and not idx_up and not mid_up and not rng_up:
                gesture = "CLEAR"
            else:
                gesture = "IDLE"

            state_machine.update(gesture)
            current = state_machine.current

            # ── Action dispatch ──────────────
            if current == "SELECT" and iy_smooth < HEADER_H:
                picked = color_zones.pick_color(ix_smooth, iy_smooth)
                if picked == "__ERASER__":
                    renderer.set_eraser()
                elif picked == "__SIZE_UP__":
                    renderer.adjust_size(+2)
                elif picked == "__SIZE_DN__":
                    renderer.adjust_size(-2)
                elif picked is not None:
                    renderer.set_color(picked)

            elif current == "DRAW" and iy_smooth >= HEADER_H:
                renderer.draw_stroke(ix_smooth, iy_smooth)

            elif current == "ERASE":
                renderer.erase_at(ix_smooth, iy_smooth)

            elif current == "CLEAR":
                renderer.clear_canvas()
                x_buf.clear(); y_buf.clear()

            else:
                renderer.lift_pen()

            # ── Draw skeleton manually ───────
            _draw_skeleton(frame, lm, w, h)

            # ── Cursor ───────────────────────
            cursor_colour = (0, 255, 180) if current == "DRAW" else (200, 200, 200)
            cv2.circle(frame, (ix_smooth, iy_smooth),
                       renderer.brush_size + 4, cursor_colour, 2)
            cv2.circle(frame, (ix_smooth, iy_smooth), 4, (255, 255, 255), -1)

            _gesture_pill(frame, current, w)

        else:
            renderer.lift_pen()
            x_buf.clear(); y_buf.clear()

        # ── Composite ink layer ──────────────
        frame = renderer.composite(frame)

        # ── FPS ──────────────────────────────
        now = time.time()
        fps_buf.append(1.0 / max(now - prev_time, 1e-6))
        prev_time = now
        fps = sum(fps_buf) / len(fps_buf)
        cv2.putText(frame, f"FPS {fps:.0f}", (w - 110, h - 18),
                    cv2.FONT_HERSHEY_DUPLEX, 0.6, (180, 255, 180), 1, cv2.LINE_AA)

        cv2.imshow("GesturePainter", frame)

        key = cv2.waitKey(1) & 0xFF
        if key in (ord('q'), ord('Q'), 27):
            break
        elif key == ord('s'):
            fname = f"gesture_art_{int(time.time())}.png"
            cv2.imwrite(fname, renderer.canvas)
            print(f"[SAVE] Canvas saved → {fname}")

    cap.release()
    cv2.destroyAllWindows()
    landmarker.close()
    print("[EXIT] GesturePainter closed.")


def _gesture_pill(frame, gesture, w):
    colours = {
        "DRAW":   (0, 200, 80),
        "SELECT": (0, 160, 255),
        "ERASE":  (0, 80, 220),
        "CLEAR":  (0, 60, 200),
        "IDLE":   (80, 80, 80),
    }
    icons = {
        "DRAW": "DRAW", "SELECT": "SELECT",
        "ERASE": "ERASE", "CLEAR": "CLEAR", "IDLE": "IDLE",
    }
    c     = colours.get(gesture, (80, 80, 80))
    label = icons.get(gesture, gesture)
    (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_DUPLEX, 0.65, 1)
    px, py = w - tw - 28, 145
    cv2.rectangle(frame, (px - 10, py - th - 8), (px + tw + 10, py + 8), c, -1)
    cv2.putText(frame, label, (px, py), cv2.FONT_HERSHEY_DUPLEX,
                0.65, (255, 255, 255), 1, cv2.LINE_AA)


def _draw_skeleton(frame, lm, w, h):
    """Draw hand skeleton manually without mp.solutions."""
    # Connections: (start, end) landmark index pairs
    connections = [
        (0,1),(1,2),(2,3),(3,4),         # thumb
        (0,5),(5,6),(6,7),(7,8),          # index
        (0,9),(9,10),(10,11),(11,12),     # middle
        (0,13),(13,14),(14,15),(15,16),   # ring
        (0,17),(17,18),(18,19),(19,20),   # pinky
        (5,9),(9,13),(13,17),             # palm
    ]
    pts = [(int(l.x * w), int(l.y * h)) for l in lm]
    for a, b in connections:
        cv2.line(frame, pts[a], pts[b], (255, 80, 80), 2, cv2.LINE_AA)
    for x, y in pts:
        cv2.circle(frame, (x, y), 4, (0, 220, 255), -1, cv2.LINE_AA)


if __name__ == "__main__":
    run()

# ✋ Air Canvas — Draw in Mid-Air with Your Hand

> Turn your webcam into an invisible paintbrush. Wave your hand and watch smooth digital ink appear in real time — no touch, no mouse, just you.

![Air Canvas Demo](gif.gif)
*(Add your screen recording GIF here — see instructions below)*

---

## 🧠 How it works

The app runs a real-time computer vision pipeline in three stages:

```
Webcam feed → MediaPipe Hands (landmark detection) → OpenCV (render ink)
```

1. **Capture** — OpenCV grabs each frame from your webcam
2. **Detect** — MediaPipe Hands identifies 21 hand landmarks per frame
3. **Track** — The tip of your index finger (landmark #8) is used as the drawing point
4. **Render** — OpenCV draws smooth lines between consecutive fingertip positions on a persistent canvas overlay

Colour selection zones sit at the top of the screen — hover your finger over them to switch colour. A closed-fist gesture clears the canvas.

---

## 🛠 Tech Stack

| Tool | Purpose |
|---|---|
| Python 3.x | Core language |
| OpenCV (`cv2`) | Webcam capture, frame processing, HSV masking, rendering |
| MediaPipe Hands | Real-time 21-point hand landmark detection |
| NumPy | Array operations on frame data |

---

## ⚙️ Setup & Run

```bash
# 1. Clone the repo
git clone https://github.com/Niharikaa08/air-canvas.git
cd air-canvas

# 2. Install dependencies
pip install opencv-python mediapipe numpy

# 3. Run
python air_canvas.py
```

**Requirements:** Python 3.7+, a working webcam

---

## 🎮 Controls

| Gesture | Action |
|---|---|
| Index finger up | Draw |
| Hover over colour zone (top bar) | Switch colour |
| All fingers closed (fist) | Clear canvas |

---

## 📁 Project Structure

```
air-canvas/
├── air_canvas.py       # Main application
├── requirements.txt    # Dependencies
└── README.md
```

---

## 💡 What I learned

- Designing a **real-time computer vision pipeline** (capture → detect → track → render)
- Working with **MediaPipe's landmark model** for gesture-based state machines
- **Frame-level signal processing** with OpenCV — HSV colour spaces, bitwise masking, canvas overlays
- Handling **latency and smoothing** for a fluid drawing experience

---

## 🗺 Roadmap

- [ ] Gesture classifier (thumbs up, peace sign) using a trained ML model on landmark coordinates
- [ ] Eraser mode
- [ ] Save canvas as PNG
- [ ] Multi-hand support

---

## 📜 License

MIT License — free to use, modify and share.

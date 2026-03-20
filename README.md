# ✋🎨 GesturePainter

**Real-time gesture-controlled drawing app** — turn any webcam into a mid-air paintbrush using MediaPipe Hands landmark tracking and OpenCV rendering.

```
Pipeline:  Capture → Detect → Track → Render
           OpenCV     MediaPipe  State    Ink
           VideoCapture  21-pt   Machine  Compositor
```

---

## ✨ Features

| Gesture | Action |
|---------|--------|
| ☝ Index finger up | **Draw** — paint on canvas |
| ✌ Index + Middle up | **Select** — hover header to pick colour |
| ✊ Fist (all fingers down) | **Erase** stroke at cursor |
| 🤙 Pinky only up | **Clear** entire canvas |
| `S` key | **Save** canvas as PNG |
| `Q` / `ESC` | Quit |

### What's under the hood

- **MediaPipe Hands** — 21-point hand landmark detection at 30+ FPS
- **Landmark state machine** — debounced gesture classification (DRAW / SELECT / ERASE / CLEAR / IDLE)
- **Stroke smoothing** — running-average buffer reduces jitter to sub-pixel noise
- **BGRA ink canvas** — alpha-composited over live webcam feed (no flicker)
- **HSV colour zones** — header strip with 10 colours, eraser, and brush-size controls
- **Calligraphy taper** — brush radius tapers with stroke velocity

---

## 🖥️ Requirements

- Python **3.10 – 3.13**
- Webcam (built-in or USB)
- OS: macOS / Windows / Linux (any with OpenCV webcam support)

---

## 🚀 Quick Start

```bash
# 1. Clone
git clone https://github.com/YOUR_USERNAME/gesture-painter.git
cd gesture-painter

# 2. Create virtual environment (recommended)
python3.13 -m venv .venv
source .venv/bin/activate        # macOS/Linux
# .venv\Scripts\activate         # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run
python gesture_painter.py
```

---

## 📁 Project Structure

```
gesture-painter/
├── gesture_painter.py       # Main entry point — CV pipeline orchestrator
├── requirements.txt
├── README.md
├── .gitignore
└── utils/
    ├── __init__.py
    ├── color_zones.py       # Header UI — colour swatches & zone hit-testing
    ├── gesture_state.py     # Debounced landmark-based state machine
    └── ink_renderer.py      # BGRA canvas, stroke drawing, compositing
```

---

## 🏗️ Architecture

```
┌─────────────┐    ┌──────────────────┐    ┌─────────────────────┐
│  OpenCV     │    │  MediaPipe Hands │    │  GestureStateMachine│
│  cap.read() │───▶│  21 landmarks    │───▶│  DRAW/SELECT/ERASE  │
│  flip/RGB   │    │  0.75 confidence │    │  debounce N frames  │
└─────────────┘    └──────────────────┘    └─────────┬───────────┘
                                                       │
                    ┌──────────────────────────────────▼──────┐
                    │           Action Dispatch               │
                    │  DRAW   → InkRenderer.draw_stroke()     │
                    │  SELECT → ColorZones.pick_color()       │
                    │  ERASE  → InkRenderer.erase_at()        │
                    │  CLEAR  → InkRenderer.clear_canvas()    │
                    └──────────────────────────────────┬──────┘
                                                       │
                    ┌──────────────────────────────────▼──────┐
                    │         InkRenderer.composite()         │
                    │   BGRA canvas α-blended over webcam     │
                    └──────────────────────────────────┬──────┘
                                                       │
                                              cv2.imshow()
```

---

## 🐙 GitHub — Step-by-Step Setup

### First time: Create the repository

1. **Create repo on GitHub**
   - Go to [github.com/new](https://github.com/new)
   - Name it `gesture-painter`
   - Set to Public (or Private)
   - **Do NOT** tick "Add a README" — we already have one
   - Click **Create repository**

2. **Initialise Git locally** (inside the project folder)
   ```bash
   cd gesture-painter
   git init
   git add .
   git commit -m "feat: initial GesturePainter — MediaPipe + OpenCV pipeline"
   ```

3. **Connect to GitHub & push**
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/gesture-painter.git
   git branch -M main
   git push -u origin main
   ```

---

### Ongoing workflow as the project grows

```bash
# After adding/editing files:
git add .                                    # stage all changes
git add gesture_painter.py                   # OR stage specific files

git commit -m "feat: add velocity-based brush taper"   # descriptive message
git push                                     # push to GitHub
```

#### Recommended commit message prefixes

| Prefix | When to use |
|--------|-------------|
| `feat:` | New feature or gesture |
| `fix:` | Bug fix |
| `refactor:` | Code restructured, no behaviour change |
| `docs:` | README / comments |
| `chore:` | Deps, config, tooling |

---

### Branches (when adding big features)

```bash
git checkout -b feature/multi-hand-support   # create feature branch
# ... make your changes ...
git add .
git commit -m "feat: support two-hand drawing"
git push origin feature/multi-hand-support

# Merge back via GitHub Pull Request, or locally:
git checkout main
git merge feature/multi-hand-support
git push
```

---

### Tags (marking milestones)

```bash
git tag -a v1.0.0 -m "Release v1.0.0 — gesture drawing MVP"
git push origin --tags
```

---

## 🔧 Troubleshooting

| Problem | Fix |
|---------|-----|
| `No module named mediapipe` | `pip install mediapipe>=0.10.14` |
| Webcam not opening | Try `cv2.VideoCapture(1)` — try index 0, 1, 2 |
| Low FPS | Lower `model_complexity` from 1 → 0 in `gesture_painter.py` |
| macOS camera permission denied | System Settings → Privacy → Camera → allow Terminal |
| Windows: DLL errors | Install [Visual C++ Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe) |

---

## 🗺️ Roadmap

- [ ] Multi-hand support (two-colour simultaneous painting)
- [ ] Shape-snapping (circle / line inference from stroke)
- [ ] Undo stack (pinch gesture)
- [ ] Custom brush patterns (spray, pencil texture)
- [ ] WebRTC browser version

---

## 📄 Licence

MIT — see [LICENSE](LICENSE)

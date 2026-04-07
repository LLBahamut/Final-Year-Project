# Gesture Recognition System

A real-time hand gesture recognition system that translates webcam hand movements and gestures into keyboard inputs. Built with MediaPipe and OpenCV, it enables hands-free control of games or any application that uses keyboard input — no additional hardware required.

***

## Demo

> Work in progress!

***

## Requirements

- Python 3.8+
- A working webcam
- Windows OS (required for Picture-in-Picture / always-on-top overlay)

***

## Installation

1. Clone the repository
```bash
git clone https://github.com/LLBahamut/Final-Year-Project.git
cd "Final-Year-Project"
```

2. Create and activate a virtual environment
```bash
python -m venv .venv
.venv\Scripts\activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

***

## Running the Application

### GUI Mode (recommended)
Launches the Settings window. Configure everything visually, then click **Start**.
```bash
python gui.py
```

### Headless Mode
Runs the detection pipeline directly in a terminal + OpenCV window, using saved settings from `config.json` (or defaults if none exist).
```bash
python main.py
```

***

## How It Works

1. **Capture:** Frames are captured from the webcam at up to 1920×1080, horizontally flipped for a natural mirror view, and capped at 30 fps to keep the camera driver stable.
2. **Detect:** Each frame is queued asynchronously to MediaPipe's `HandLandmarker`, which returns up to 2 sets of 21 3D landmarks per frame via a background callback thread.
3. **Cache:** The latest valid detection result is cached so landmarks are drawn on every frame — even frames where the async callback hasn't fired yet. This eliminates landmark flickering.
4. **Left Hand — Movement Control:**
   - **Palm open:** When at least `palm_min_fingers` fingers are extended, the hand is classified as an open palm and control is activated.
   - **Reference lock:** The palm-centre position at the moment the palm first opens is saved as the reference point.
   - **Movement mapping:** Subsequent palm-centre positions are compared to the reference. Displacement beyond `movement_threshold_activate` triggers the corresponding directional key; displacement below `movement_threshold_release` releases it. This hysteresis gap prevents key chatter.
   - **Palm closed:** Releases all active keys and clears the reference point.
5. **Right Hand — Gesture Control:** The right hand is classified into one of four gestures (in priority order: pinch → thumbs-up → point → flat palm). Each gesture maps to a configurable key that is held while the gesture is held and released when the hand changes or disappears.
6. **Key Injection:** Active keys are sent to the OS in real time via `pynput`.
7. **PiP Overlay:** The annotated camera feed is displayed in a frameless, always-on-top, draggable Picture-in-Picture window via PyQt6, so the feed stays visible while using any other application.

***

## Controls

### Left Hand — Movement

| Gesture | Default Key | Action |
|---|---|---|
| Open palm | — | Activate control and lock reference point |
| Move hand up | `W` | Move forward |
| Move hand down | `S` | Move backward |
| Move hand left | `A` | Move left |
| Move hand right | `D` | Move right |
| Diagonal movement | Two keys | Two directional keys pressed simultaneously |
| Close palm | — | Release all keys and clear reference point |

### Right Hand — Gestures

| Gesture | Default Key | Description |
|---|---|---|
| 👌 Pinch | `E` | Thumb tip and index tip close together |
| 👍 Thumbs Up | `Space` | Thumb extended upward, all other fingers curled |
| 👆 Point | `Q` | Index finger extended, others curled |
| 🖐 Flat Palm | `F` | Open palm (all fingers extended) |

> All gesture-to-key bindings are fully remappable in the GUI or via `config.json`.

### Headless Mode Keyboard Shortcuts

These shortcuts apply only when running `main.py` (the OpenCV window must be in focus).

| Key | Action |
|---|---|
| `Q` | Quit the application |
| `R` | Reset reference point and release all keys |

***

## GUI Settings

Launching `gui.py` opens a settings window with five tabs.

| Tab | What you can configure |
|---|---|
| **Camera & Detection** | Camera index, resolution, MediaPipe confidence thresholds |
| **Gesture Thresholds** | Palm detection sensitivity, movement activate/release thresholds, hand loss grace period, proximity, pinch distance, finger curl ratio |
| **Keys & Controls** | Enable/disable actual keypresses and debug output; remap all WASD keys and right-hand gesture keys |
| **Display & Overlay** | PiP scale, WASD overlay toggle, key box size/spacing, overlay position |
| **Colors** | Hand skeleton colors (left/right), WASD key active/inactive colors, label text colors |

Click **Start** to launch the PiP overlay with your current settings. Click **Stop** (same button) to stop. **Restore Defaults** resets all fields to their default values without stopping a running session.

Settings are not auto-saved to disk — copy your `GestureConfig` values into a `config.json` file (see below) to persist them between runs.

***

## Configuration File

Settings can be persisted by saving a `config.json` in the project root. `main.py` automatically loads it on startup if present. You can generate one programmatically:

```python
from config import GestureConfig
GestureConfig().to_json("config.json")        # write defaults
cfg = GestureConfig.from_json("config.json")  # load back
```

### Full Config Reference

| Field | Default | Description |
|---|---|---|
| `camera_index` | `0` | Index of the webcam to use |
| `desired_width` | `1920` | Camera capture width in pixels |
| `desired_height` | `1080` | Camera capture height in pixels |
| `min_hand_detection_confidence` | `0.7` | Minimum confidence for initial hand detection |
| `min_hand_presence_confidence` | `0.5` | Minimum confidence to confirm hand presence |
| `min_tracking_confidence` | `0.5` | Minimum confidence for landmark tracking |
| `palm_extension_threshold` | `1.1` | Ratio of tip-to-wrist vs. base-to-wrist distance for a finger to count as extended |
| `palm_min_fingers` | `3` | Number of extended fingers required to classify the hand as an open palm |
| `movement_threshold_activate` | `0.12` | Normalised displacement from reference point to press a directional key |
| `movement_threshold_release` | `0.08` | Normalised displacement to release a directional key (hysteresis) |
| `hand_loss_grace_period` | `2.0` | Seconds of hand-not-visible before control state resets |
| `hand_proximity_threshold` | `0.2` | Max 3D distance (normalised) to identify a re-appearing hand as the same one |
| `enable_actual_keypresses` | `True` | `False` = print keys to console only (useful for testing without a target app) |
| `enable_debug_output` | `True` | `False` = suppress press/release log lines |
| `key_forward` | `"w"` | Key sent when moving hand up |
| `key_backward` | `"s"` | Key sent when moving hand down |
| `key_left` | `"a"` | Key sent when moving hand left |
| `key_right` | `"d"` | Key sent when moving hand right |
| `enable_right_hand_gestures` | `True` | Enable/disable right-hand gesture detection entirely |
| `gesture_pinch_key` | `"e"` | Key sent when a pinch is detected |
| `gesture_thumbsup_key` | `"space"` | Key sent when thumbs-up is detected |
| `gesture_palm_key` | `"f"` | Key sent when a flat palm is detected (right hand) |
| `gesture_point_key` | `"q"` | Key sent when a point gesture is detected |
| `pinch_distance_threshold` | `0.06` | Max normalised 3D distance between thumb and index tips to trigger pinch |
| `finger_curl_max_ratio` | `0.9` | Max tip-to-wrist / base-to-wrist ratio for a finger to be considered curled |
| `pip_scale` | `0.4` | PiP overlay scale factor relative to capture resolution |
| `color_left_hand` | `[255, 0, 0]` | Left-hand skeleton colour in BGR |
| `color_right_hand` | `[0, 0, 255]` | Right-hand skeleton colour in BGR |
| `wasd_overlay_enabled` | `True` | Show/hide the on-screen WASD key overlay |
| `wasd_key_size` | `50` | Pixel size of each key box in the WASD overlay |
| `wasd_key_spacing` | `10` | Gap in pixels between key boxes |
| `wasd_overlay_x` | `20` | X position (pixels from left edge) of the WASD overlay |
| `wasd_overlay_y_offset` | `150` | Y offset (pixels from bottom edge) of the WASD overlay |
| `wasd_key_color_inactive` | `[60, 60, 60]` | Key box colour when not pressed (BGR) |
| `wasd_key_color_active` | `[0, 255, 0]` | Key box colour when pressed (BGR) |
| `wasd_text_color_inactive` | `[180, 180, 180]` | Key label colour when not pressed (BGR) |
| `wasd_text_color_active` | `[0, 0, 0]` | Key label colour when pressed (BGR) |

***

## Project Structure

```
Final Year Project/
├── main.py                 # Headless entry point — OpenCV window, terminal output
├── gui.py                  # PyQt6 Settings window + entry point
├── processor.py            # GestureProcessor — detection, gesture logic, rendering
├── pip_overlay.py          # CameraWorker (QThread) + PipOverlay (frameless Qt window)
├── config.py               # GestureConfig dataclass with JSON load/save
├── config.json             # Saved user settings (auto-generated, not tracked by git)
├── hand_landmarker.task    # Pre-trained MediaPipe hand landmark model (7.8 MB)
├── requirements.txt        # Python dependencies
└── README.md               # This file
```

> `config.json` is created automatically the first time you save settings.

***

## Tech Stack

| Library | Version | Role |
|---|---|---|
| [MediaPipe](https://ai.google.dev/edge/mediapipe/solutions/vision/hand_landmarker) | 0.10.31 | Hand landmark detection — 21 3D points per hand, async LIVE_STREAM mode |
| [OpenCV](https://opencv.org/) | 4.10.0 | Video capture, frame processing, on-screen annotation |
| [NumPy](https://numpy.org/) | ≥ 1.24 | Array operations |
| [pynput](https://pynput.readthedocs.io/) | latest | OS-level keyboard press/release injection |
| [PyQt6](https://pypi.org/project/PyQt6/) | ≥ 6.5 | Settings GUI, PiP overlay window, camera worker thread |

***

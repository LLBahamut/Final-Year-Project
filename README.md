# LumineGesture

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![MediaPipe](https://img.shields.io/badge/MediaPipe-0.10.31-green?logo=google&logoColor=white)](https://ai.google.dev/edge/mediapipe/solutions/vision/hand_landmarker)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.10.0-red?logo=opencv&logoColor=white)](https://opencv.org/)
[![PyQt6](https://img.shields.io/badge/PyQt6-%E2%89%A56.5-41CD52?logo=qt&logoColor=white)](https://pypi.org/project/PyQt6/)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows-0078D6?logo=windows&logoColor=white)](https://www.microsoft.com/windows)

## Description

LumineGesture turns your webcam into a game controller. It watches your hands in real time and translates their movement into keyboard and mouse input, so you can move, click, and trigger actions in any PC game or application without touching a key.

Under the hood, LumineGesture uses Google's [MediaPipe Hand Landmarker](https://ai.google.dev/edge/mediapipe/solutions/vision/hand_landmarker) to track 21 points on each hand, 30 times a second, then runs that through a gesture classifier that decides what you're doing with your hands and sends the matching key or mouse event to your PC.

Unlike Kinect based or glove based motion controllers, LumineGesture needs nothing extra: just the webcam you already have. It also runs its own lighting correction in the background, so it keeps working whether you're sitting in a bright room or a dim one.

### Features

- **Two hands, two jobs**: your left hand handles WASD style movement while your right hand fires off separate actions at the same time.
- **Four ready to use gestures**: Pinch, Thumbs Up, Point, and Flat Palm, each one assignable to any key or mouse button you like.
- **Works in changing light**: brightness is measured continuously and corrected automatically, so you don't need to reposition lights or recalibrate.
- **Floating camera preview**: a small, draggable window shows your hand tracking on top of whatever you're playing, so you always know what the system sees.
- **A settings window, not a config file**: pick your camera, resolution, gestures, and key bindings from a simple graphical interface. No code editing required.
- **Every key is remappable**: arrows, letters, F-keys, modifiers, and mouse buttons can all be bound to a gesture from inside the app.

### Background

LumineGesture was built as a Final Year Project in Human-Computer Interaction, evaluated across roughly 16,000 frames of hand tracking data and tested with first time users. In that evaluation it reached 98.65% gesture recognition accuracy with its lighting correction turned on, with fatigue (rather than accuracy) identified as the main thing that affects comfort over long sessions.

## Installation

### Requirements

- Windows (needed for the floating camera preview window)
- Python 3.8 or newer
- A webcam

### Steps

1. **Download the project**

   If you have Git installed:

   ```bash
   git clone https://github.com/LLBahamut/Final-Year-Project.git
   cd Final-Year-Project
   ```

   Otherwise, download the ZIP from the project's GitHub page and extract it, then open a terminal in that folder.

2. **Create a virtual environment** (keeps LumineGesture's dependencies separate from the rest of your Python setup)

   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. **Install the required packages**

   ```bash
   pip install -r requirements.txt
   ```

4. **Launch LumineGesture**

   ```bash
   python gui.py
   ```

   This opens the settings window. Pick your camera, adjust anything you like, and click **Start** to begin controlling your PC with your hands.

   Prefer a lighter weight, no interface option? Run `python main.py` instead to launch straight into detection mode using your last saved settings.

## Controls

### Left hand: movement

| Gesture | Default key | Action |
|---|---|---|
| Open palm | - | Lock in a starting position |
| Move hand up | `W` | Move forward |
| Move hand down | `S` | Move backward |
| Move hand left | `A` | Move left |
| Move hand right | `D` | Move right |
| Close palm | - | Release all movement keys |

### Right hand: gestures

| Gesture | Default key | Description |
|---|---|---|
| Pinch | `Z` | Touch your thumb and index finger together |
| Thumbs Up | `X` | Thumb out, other fingers curled in |
| Point | `Q` | Index finger out, other fingers curled in |
| Flat Palm | `C` | Open hand facing the camera |

All of these are just the defaults. Every gesture and direction can be reassigned to a different key or mouse button from the **Bindings** tab in the settings window.

## Author

Built by **Arya Cenggata** ([@LLBahamut](https://github.com/LLBahamut)) as a final year undergraduate project exploring real time computer vision for accessible human-computer interaction.
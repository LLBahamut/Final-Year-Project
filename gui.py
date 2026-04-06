import sys
import os
import subprocess
import tempfile

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QFormLayout, QSpinBox, QDoubleSpinBox, QSlider, QCheckBox, QPushButton,
    QLabel, QColorDialog, QGroupBox,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QKeyEvent

from config import GestureConfig


# ---------------------------------------------------------------------------
# Custom widgets
# ---------------------------------------------------------------------------

class KeyCaptureButton(QPushButton):
    """Button that captures a single keypress for key binding."""

    def __init__(self, key: str, parent=None):
        super().__init__(key.upper(), parent)
        self._key = key
        self._listening = False
        self.setFixedWidth(60)
        self.clicked.connect(self._start_listening)

    def _start_listening(self):
        self._listening = True
        self.setText("...")
        self.grabKeyboard()

    def keyPressEvent(self, event: QKeyEvent):
        if not self._listening:
            super().keyPressEvent(event)
            return
        if event.key() == Qt.Key.Key_Escape:
            self._stop_listening()
            return
        text = event.text()
        if text and text.isprintable() and len(text) == 1:
            self._key = text.lower()
            self._stop_listening()

    def _stop_listening(self):
        self._listening = False
        self.releaseKeyboard()
        self.setText(self._key.upper())

    def get_key(self) -> str:
        return self._key

    def set_key(self, key: str):
        self._key = key
        self.setText(key.upper())


class ColorPickerButton(QPushButton):
    """Button that shows a color swatch and opens a color picker dialog."""

    def __init__(self, bgr: list, parent=None):
        super().__init__(parent)
        self._bgr = list(bgr)
        self.setFixedSize(60, 30)
        self._update_swatch()
        self.clicked.connect(self._pick_color)

    def _update_swatch(self):
        b, g, r = self._bgr
        self.setStyleSheet(
            f"background-color: rgb({r},{g},{b}); border: 1px solid #888;"
        )

    def _pick_color(self):
        b, g, r = self._bgr
        initial = QColor(r, g, b)
        color = QColorDialog.getColor(initial, self, "Pick a color")
        if color.isValid():
            self._bgr = [color.blue(), color.green(), color.red()]
            self._update_swatch()

    def get_bgr(self) -> list:
        return list(self._bgr)

    def set_bgr(self, bgr: list):
        self._bgr = list(bgr)
        self._update_swatch()


# ---------------------------------------------------------------------------
# Helper: labelled slider for float values 0.0 – 1.0
# ---------------------------------------------------------------------------

def _make_confidence_row(label_text: str, value: float):
    """Return (layout, slider, value_label) for a 0-100 int slider mapped to 0.0-1.0."""
    row = QHBoxLayout()
    lbl = QLabel(label_text)
    lbl.setFixedWidth(200)
    slider = QSlider(Qt.Orientation.Horizontal)
    slider.setRange(0, 100)
    slider.setValue(int(value * 100))
    val_label = QLabel(f"{value:.2f}")
    val_label.setFixedWidth(40)
    slider.valueChanged.connect(lambda v: val_label.setText(f"{v / 100:.2f}"))
    row.addWidget(lbl)
    row.addWidget(slider)
    row.addWidget(val_label)
    return row, slider, val_label


# ---------------------------------------------------------------------------
# Main window
# ---------------------------------------------------------------------------

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gesture Recognition - Settings")
        self.setFixedWidth(520)
        self.process = None
        self.poll_timer = QTimer()
        self.poll_timer.timeout.connect(self._check_process)

        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)

        # Tabs
        self.tabs = QTabWidget()
        root_layout.addWidget(self.tabs)

        self._build_camera_tab()
        self._build_gesture_tab()
        self._build_keys_tab()
        self._build_display_tab()
        self._build_colors_tab()

        # Bottom bar
        bottom = QHBoxLayout()
        self.btn_defaults = QPushButton("Restore Defaults")
        self.btn_defaults.clicked.connect(self._restore_defaults)
        self.status_label = QLabel("Ready")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.btn_start = QPushButton("Start")
        self.btn_start.setFixedWidth(100)
        self.btn_start.clicked.connect(self._toggle_start_stop)
        bottom.addWidget(self.btn_defaults)
        bottom.addStretch()
        bottom.addWidget(self.status_label)
        bottom.addStretch()
        bottom.addWidget(self.btn_start)
        root_layout.addLayout(bottom)

        # Populate with defaults
        self._populate(GestureConfig())

    # ------------------------------------------------------------------
    # Tab builders
    # ------------------------------------------------------------------

    def _build_camera_tab(self):
        tab = QWidget()
        layout = QFormLayout(tab)

        self.spin_camera_index = QSpinBox()
        self.spin_camera_index.setRange(0, 10)
        layout.addRow("Camera Index:", self.spin_camera_index)

        self.spin_width = QSpinBox()
        self.spin_width.setRange(320, 3840)
        self.spin_width.setSingleStep(160)
        layout.addRow("Resolution Width:", self.spin_width)

        self.spin_height = QSpinBox()
        self.spin_height.setRange(240, 2160)
        self.spin_height.setSingleStep(120)
        layout.addRow("Resolution Height:", self.spin_height)

        # Confidence sliders
        row1, self.slider_detection, _ = _make_confidence_row("Hand Detection Confidence:", 0.7)
        layout.addRow(row1)
        row2, self.slider_presence, _ = _make_confidence_row("Hand Presence Confidence:", 0.5)
        layout.addRow(row2)
        row3, self.slider_tracking, _ = _make_confidence_row("Tracking Confidence:", 0.5)
        layout.addRow(row3)

        self.tabs.addTab(tab, "Camera && Detection")

    def _build_gesture_tab(self):
        tab = QWidget()
        layout = QFormLayout(tab)

        self.spin_palm_ext = QDoubleSpinBox()
        self.spin_palm_ext.setRange(0.5, 2.0)
        self.spin_palm_ext.setSingleStep(0.05)
        self.spin_palm_ext.setDecimals(2)
        layout.addRow("Palm Extension Threshold:", self.spin_palm_ext)

        self.spin_palm_fingers = QSpinBox()
        self.spin_palm_fingers.setRange(1, 4)
        layout.addRow("Palm Min Fingers:", self.spin_palm_fingers)

        self.spin_move_activate = QDoubleSpinBox()
        self.spin_move_activate.setRange(0.01, 0.50)
        self.spin_move_activate.setSingleStep(0.01)
        self.spin_move_activate.setDecimals(2)
        layout.addRow("Movement Activate Threshold:", self.spin_move_activate)

        self.spin_move_release = QDoubleSpinBox()
        self.spin_move_release.setRange(0.01, 0.50)
        self.spin_move_release.setSingleStep(0.01)
        self.spin_move_release.setDecimals(2)
        layout.addRow("Movement Release Threshold:", self.spin_move_release)

        self.spin_grace = QDoubleSpinBox()
        self.spin_grace.setRange(0.0, 10.0)
        self.spin_grace.setSingleStep(0.5)
        self.spin_grace.setDecimals(1)
        self.spin_grace.setSuffix(" sec")
        layout.addRow("Hand Loss Grace Period:", self.spin_grace)

        self.spin_proximity = QDoubleSpinBox()
        self.spin_proximity.setRange(0.01, 1.0)
        self.spin_proximity.setSingleStep(0.01)
        self.spin_proximity.setDecimals(2)
        layout.addRow("Hand Proximity Threshold:", self.spin_proximity)

        self.tabs.addTab(tab, "Gesture Thresholds")

    def _build_keys_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Checkboxes
        self.chk_keypresses = QCheckBox("Enable Actual Keypresses")
        self.chk_debug = QCheckBox("Enable Debug Output")
        layout.addWidget(self.chk_keypresses)
        layout.addWidget(self.chk_debug)

        # Key mapping
        group = QGroupBox("Key Mapping")
        form = QFormLayout(group)

        self.key_forward = KeyCaptureButton("w")
        self.key_backward = KeyCaptureButton("s")
        self.key_left = KeyCaptureButton("a")
        self.key_right = KeyCaptureButton("d")

        form.addRow("Forward:", self.key_forward)
        form.addRow("Backward:", self.key_backward)
        form.addRow("Left:", self.key_left)
        form.addRow("Right:", self.key_right)

        layout.addWidget(group)
        layout.addStretch()
        self.tabs.addTab(tab, "Keys && Controls")

    def _build_display_tab(self):
        tab = QWidget()
        layout = QFormLayout(tab)

        self.spin_pip_scale = QDoubleSpinBox()
        self.spin_pip_scale.setRange(0.1, 1.0)
        self.spin_pip_scale.setSingleStep(0.05)
        self.spin_pip_scale.setDecimals(2)
        layout.addRow("PiP Scale:", self.spin_pip_scale)

        self.chk_wasd_overlay = QCheckBox("WASD Overlay Enabled")
        layout.addRow(self.chk_wasd_overlay)

        self.spin_key_size = QSpinBox()
        self.spin_key_size.setRange(20, 100)
        self.spin_key_size.setSingleStep(5)
        layout.addRow("WASD Key Size:", self.spin_key_size)

        self.spin_key_spacing = QSpinBox()
        self.spin_key_spacing.setRange(0, 30)
        self.spin_key_spacing.setSingleStep(2)
        layout.addRow("WASD Key Spacing:", self.spin_key_spacing)

        self.spin_overlay_x = QSpinBox()
        self.spin_overlay_x.setRange(0, 500)
        self.spin_overlay_x.setSingleStep(10)
        layout.addRow("WASD Overlay X:", self.spin_overlay_x)

        self.spin_overlay_y = QSpinBox()
        self.spin_overlay_y.setRange(50, 500)
        self.spin_overlay_y.setSingleStep(10)
        layout.addRow("WASD Overlay Y Offset:", self.spin_overlay_y)

        self.tabs.addTab(tab, "Display && Overlay")

    def _build_colors_tab(self):
        tab = QWidget()
        layout = QFormLayout(tab)

        self.color_left_hand = ColorPickerButton([255, 0, 0])
        layout.addRow("Left Hand Color:", self.color_left_hand)

        self.color_right_hand = ColorPickerButton([0, 0, 255])
        layout.addRow("Right Hand Color:", self.color_right_hand)

        self.color_key_inactive = ColorPickerButton([60, 60, 60])
        layout.addRow("Key Inactive Color:", self.color_key_inactive)

        self.color_key_active = ColorPickerButton([0, 255, 0])
        layout.addRow("Key Active Color:", self.color_key_active)

        self.color_text_inactive = ColorPickerButton([180, 180, 180])
        layout.addRow("Text Inactive Color:", self.color_text_inactive)

        self.color_text_active = ColorPickerButton([0, 0, 0])
        layout.addRow("Text Active Color:", self.color_text_active)

        self.tabs.addTab(tab, "Colors")

    # ------------------------------------------------------------------
    # Config ↔ widgets
    # ------------------------------------------------------------------

    def _populate(self, cfg: GestureConfig):
        # Camera
        self.spin_camera_index.setValue(cfg.camera_index)
        self.spin_width.setValue(cfg.desired_width)
        self.spin_height.setValue(cfg.desired_height)
        self.slider_detection.setValue(int(cfg.min_hand_detection_confidence * 100))
        self.slider_presence.setValue(int(cfg.min_hand_presence_confidence * 100))
        self.slider_tracking.setValue(int(cfg.min_tracking_confidence * 100))

        # Gesture
        self.spin_palm_ext.setValue(cfg.palm_extension_threshold)
        self.spin_palm_fingers.setValue(cfg.palm_min_fingers)
        self.spin_move_activate.setValue(cfg.movement_threshold_activate)
        self.spin_move_release.setValue(cfg.movement_threshold_release)
        self.spin_grace.setValue(cfg.hand_loss_grace_period)
        self.spin_proximity.setValue(cfg.hand_proximity_threshold)

        # Keys
        self.chk_keypresses.setChecked(cfg.enable_actual_keypresses)
        self.chk_debug.setChecked(cfg.enable_debug_output)
        self.key_forward.set_key(cfg.key_forward)
        self.key_backward.set_key(cfg.key_backward)
        self.key_left.set_key(cfg.key_left)
        self.key_right.set_key(cfg.key_right)

        # Display
        self.spin_pip_scale.setValue(cfg.pip_scale)
        self.chk_wasd_overlay.setChecked(cfg.wasd_overlay_enabled)
        self.spin_key_size.setValue(cfg.wasd_key_size)
        self.spin_key_spacing.setValue(cfg.wasd_key_spacing)
        self.spin_overlay_x.setValue(cfg.wasd_overlay_x)
        self.spin_overlay_y.setValue(cfg.wasd_overlay_y_offset)

        # Colors
        self.color_left_hand.set_bgr(cfg.color_left_hand)
        self.color_right_hand.set_bgr(cfg.color_right_hand)
        self.color_key_inactive.set_bgr(cfg.wasd_key_color_inactive)
        self.color_key_active.set_bgr(cfg.wasd_key_color_active)
        self.color_text_inactive.set_bgr(cfg.wasd_text_color_inactive)
        self.color_text_active.set_bgr(cfg.wasd_text_color_active)

    def _collect(self) -> GestureConfig:
        return GestureConfig(
            camera_index=self.spin_camera_index.value(),
            desired_width=self.spin_width.value(),
            desired_height=self.spin_height.value(),
            min_hand_detection_confidence=self.slider_detection.value() / 100,
            min_hand_presence_confidence=self.slider_presence.value() / 100,
            min_tracking_confidence=self.slider_tracking.value() / 100,
            palm_extension_threshold=self.spin_palm_ext.value(),
            palm_min_fingers=self.spin_palm_fingers.value(),
            movement_threshold_activate=self.spin_move_activate.value(),
            movement_threshold_release=self.spin_move_release.value(),
            hand_loss_grace_period=self.spin_grace.value(),
            hand_proximity_threshold=self.spin_proximity.value(),
            enable_actual_keypresses=self.chk_keypresses.isChecked(),
            enable_debug_output=self.chk_debug.isChecked(),
            key_forward=self.key_forward.get_key(),
            key_backward=self.key_backward.get_key(),
            key_left=self.key_left.get_key(),
            key_right=self.key_right.get_key(),
            pip_scale=self.spin_pip_scale.value(),
            color_left_hand=self.color_left_hand.get_bgr(),
            color_right_hand=self.color_right_hand.get_bgr(),
            wasd_overlay_enabled=self.chk_wasd_overlay.isChecked(),
            wasd_key_size=self.spin_key_size.value(),
            wasd_key_spacing=self.spin_key_spacing.value(),
            wasd_overlay_x=self.spin_overlay_x.value(),
            wasd_overlay_y_offset=self.spin_overlay_y.value(),
            wasd_key_color_inactive=self.color_key_inactive.get_bgr(),
            wasd_key_color_active=self.color_key_active.get_bgr(),
            wasd_text_color_inactive=self.color_text_inactive.get_bgr(),
            wasd_text_color_active=self.color_text_active.get_bgr(),
        )

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def _restore_defaults(self):
        self._populate(GestureConfig())

    def _toggle_start_stop(self):
        if self.process is not None:
            self._stop()
        else:
            self._start()

    def _start(self):
        cfg = self._collect()
        config_path = os.path.join(tempfile.gettempdir(), "gesture_config.json")
        cfg.to_json(config_path)

        main_py = os.path.join(os.path.dirname(os.path.abspath(__file__)), "main.py")
        self.process = subprocess.Popen(
            [sys.executable, main_py, "--config", config_path],
            cwd=os.path.dirname(os.path.abspath(__file__)),
        )

        self.btn_start.setText("Stop")
        self.status_label.setText("Running...")
        self.poll_timer.start(500)

    def _stop(self):
        if self.process:
            self.process.terminate()

    def _check_process(self):
        if self.process and self.process.poll() is not None:
            self.poll_timer.stop()
            code = self.process.returncode
            self.process = None
            self.btn_start.setText("Start")
            self.status_label.setText(f"Stopped (exit code {code})")

    def closeEvent(self, event):
        if self.process:
            self.process.terminate()
            self.process.wait(timeout=5)
        event.accept()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

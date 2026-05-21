import time
import signal
import sys

import cv2

from config import GestureConfig
from processor import GestureProcessor
from metrics import PerformanceLogger, NullLogger, GESTURE_LABELS, LIGHTING_LABELS

_MAX_CONSECUTIVE_FAILURES = 5
_TARGET_FPS               = 30
_TARGET_INTERVAL          = 1.0 / _TARGET_FPS

# Ground-truth labelling hotkeys: 0=none, 1=pinch, 2=thumbs_up, 3=point, 4=flat_palm
_GT_KEYMAP = {ord(str(i)): GESTURE_LABELS[i] for i in range(len(GESTURE_LABELS))}


def _draw_paused_indicator(frame, paused: bool):
    """Overlay a status badge in the top-right corner so the recorder can
    always tell at a glance whether the CSV is being written.

    RED 'REC' when actively logging, GRAY 'PAUSED' otherwise. Drawn directly
    on the displayed frame after process_frame() and draw_fps() have run."""
    if frame is None:
        return
    label = "REC" if not paused else "PAUSED"
    color = (0, 0, 255) if not paused else (160, 160, 160)
    text_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)
    x = frame.shape[1] - text_size[0] - 20
    y = 35
    # Filled dot for REC, hollow square for PAUSED — extra visual cue
    if not paused:
        cv2.circle(frame, (x - 18, y - 6), 8, color, -1)
    else:
        cv2.rectangle(frame, (x - 26, y - 14), (x - 10, y + 2), color, 2)
    cv2.putText(frame, label, (x, y), cv2.FONT_HERSHEY_SIMPLEX,
                0.8, color, 2)


def main():
    # Load config from file if it exists, otherwise use defaults
    try:
        cfg = GestureConfig.from_json("config.json")
        print("Loaded config from config.json")
    except FileNotFoundError:
        cfg = GestureConfig()
        print("Using default configuration")

    proc = GestureProcessor(cfg)

    if cfg.enable_metrics_logging:
        # start_paused=True: session opens muted so warmup frames don't pollute
        # the CSV. Press 'p' once you're ready to record the first gesture.
        logger = PerformanceLogger(
            output_dir=cfg.metrics_output_dir,
            session_label=cfg.metrics_session_label,
            fps_window=cfg.metrics_fps_window,
            start_paused=True,
        )
        logger.set_lighting_condition(cfg.metrics_initial_lighting)
        proc.attach_logger(logger)
        print(f"Metrics logging ON  → {logger.path}")
        print("  Hotkeys: 0=none 1=pinch 2=thumbs_up 3=point 4=flat_palm")
        print("           l=cycle lighting condition")
        print("           p=toggle pause (session starts PAUSED)")
        print("           r=reset control / debouncer  b=quit")
    else:
        logger = NullLogger()

    try:
        cap, width, height = proc.init_camera()
    except RuntimeError as e:
        print(f"Error: {e}")
        sys.exit(1)

    proc.init_keyboard()

    try:
        proc.init_landmarker()
    except Exception as e:
        print(f"Error initializing MediaPipe: {e}")
        cap.release()
        sys.exit(1)

    # Graceful shutdown on Ctrl+C
    def _signal_handler(sig, frame):
        print("\nShutting down...")
        logger.close()
        proc.cleanup()
        cap.release()
        cv2.destroyAllWindows()
        sys.exit(0)

    signal.signal(signal.SIGINT, _signal_handler)

    print("\nGesture controller running.")
    print("  Left hand  - open palm to enable WASD control")
    print("  Right hand - pinch / thumbs-up / flat palm / point")
    print("  Press Ctrl+C to quit\n")

    prev_time            = time.time()
    consecutive_failures = 0
    lighting_idx         = (
        LIGHTING_LABELS.index(cfg.metrics_initial_lighting)
        if cfg.metrics_initial_lighting in LIGHTING_LABELS else 0
    )

    while True:
        frame_start = time.time()

        # Start the metrics timer BEFORE cap.read() so camera capture latency
        # is included in processing_time_ms. The logger is a NullLogger no-op
        # when metrics are disabled, so this is free in the non-eval path.
        logger.start_frame()
        ret, frame = cap.read()
        if not ret:
            consecutive_failures += 1
            if consecutive_failures >= _MAX_CONSECUTIVE_FAILURES:
                print(
                    f"Error: Failed to capture frame {consecutive_failures} times in a row."
                )
                break
            print(
                f"Warning: Dropped frame ({consecutive_failures}/{_MAX_CONSECUTIVE_FAILURES}), retrying..."
            )
            time.sleep(0.01)
            continue

        consecutive_failures = 0  # reset on successful read

        annotated = proc.process_frame(frame)

        now       = time.time()
        fps       = 1 / max(now - prev_time, 1e-6)
        prev_time = now
        proc.draw_fps(annotated, fps)

        # Recording-status indicator. Always drawn so the recorder can see at
        # a glance whether the CSV is being written. Cheap (a single putText).
        _draw_paused_indicator(annotated, logger.is_paused())

        cv2.imshow("Gesture Controller", annotated)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("b"):
            print("\nQuitting...")
            break
        elif key == ord("r"):
            proc.reset_control()
        elif key == ord("p"):
            # Toggle pause. On RESUME, also reset the right-hand gesture
            # debouncer so the next recording window starts from a clean
            # state — otherwise stale 'confirming' counts from before the
            # pause could leak across the boundary and contaminate the
            # first few frames after resume.
            new_state = not logger.is_paused()
            logger.set_paused(new_state)
            if not new_state:
                # Resuming — clear the debouncer.
                proc.reset_right_hand_gesture()
            if cfg.enable_metrics_logging:
                print(f"Metrics logging {'PAUSED' if new_state else 'RESUMED'}")
        elif key in _GT_KEYMAP:
            label = _GT_KEYMAP[key]
            logger.set_ground_truth(label)
            if cfg.enable_metrics_logging:
                print(f"Ground truth → {label}")
        elif key == ord("l"):
            lighting_idx = (lighting_idx + 1) % len(LIGHTING_LABELS)
            logger.set_lighting_condition(LIGHTING_LABELS[lighting_idx])
            if cfg.enable_metrics_logging:
                print(f"Lighting condition → {LIGHTING_LABELS[lighting_idx]}")

        # Rate cap — keep loop at TARGET_FPS, don't overwhelm the driver
        elapsed   = time.time() - frame_start
        remaining = _TARGET_INTERVAL - elapsed
        if remaining > 0:
            time.sleep(remaining)

    logger.close()
    proc.cleanup()
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
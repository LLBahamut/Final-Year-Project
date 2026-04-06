import time
import ctypes
import argparse

import cv2

from config import GestureConfig
from processor import GestureProcessor

# Picture-in-Picture mode configuration
PIP_WINDOW_NAME = "Gesture Recognition System"


def set_window_always_on_top(window_name, enable=True):
    """Set the OpenCV window to always stay on top of other windows (Windows only)."""
    try:
        HWND_TOPMOST = -1
        HWND_NOTOPMOST = -2
        SWP_NOMOVE = 0x0002
        SWP_NOSIZE = 0x0001
        SWP_NOACTIVATE = 0x0010

        hwnd = ctypes.windll.user32.FindWindowW(None, window_name)

        if hwnd:
            flag = HWND_TOPMOST if enable else HWND_NOTOPMOST
            ctypes.windll.user32.SetWindowPos(
                hwnd, flag, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE
            )
            return True
        return False
    except Exception:
        return False


def main():
    """Main function to run the gesture recognition system."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str, default=None)
    args = parser.parse_args()

    if args.config:
        cfg = GestureConfig.from_json(args.config)
    else:
        cfg = GestureConfig()

    proc = GestureProcessor(cfg)

    # Initialize camera
    print("Initializing camera...")
    try:
        cap, width, height = proc.init_camera()
    except RuntimeError as e:
        print(f"Error: {e}")
        print("Please check that your webcam is connected and not in use by another application.")
        return

    # Initialize keyboard
    proc.init_keyboard()

    # Initialize MediaPipe
    print("Initializing HandLandmarker...")
    try:
        proc.init_landmarker()
    except Exception as e:
        print(f"Error initializing HandLandmarker: {e}")
        print("Please ensure 'hand_landmarker.task' exists in the current directory.")
        cap.release()
        return

    print("\nGesture Recognition System Started!")
    print("Controls:")
    print("  - Press 'Q' or 'ESC' to quit")
    print("  - Press 'R' to reset reference point")
    print("  - Show OPEN PALM with LEFT hand (closest to camera) to set/activate keyboard control")
    print("  - Move hand: LEFT/RIGHT (A/D), FORWARD/BACK (W/S)")
    print("  - Control stays active once reference point is set")
    print("  - Multi-person support: Closest left hand to camera controls")
    print("  - Press 'P' to toggle Picture-in-Picture mode (always-on-top)")
    print("\nStarting camera feed...\n")

    # Create OpenCV window
    cv2.namedWindow(PIP_WINDOW_NAME, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(PIP_WINDOW_NAME, width, height)

    pip_mode = False
    prev_time = time.time()

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Error: Failed to capture frame.")
                break

            # Process frame (flip, detect, draw landmarks, controls, overlay)
            annotated = proc.process_frame(frame)

            # FPS
            now = time.time()
            fps = 1 / max(now - prev_time, 1e-6)
            prev_time = now
            proc.draw_fps(annotated, fps)

            # PiP scaling
            if pip_mode:
                pw = int(annotated.shape[1] * cfg.pip_scale)
                ph = int(annotated.shape[0] * cfg.pip_scale)
                display_frame = cv2.resize(annotated, (pw, ph), interpolation=cv2.INTER_AREA)
            else:
                display_frame = annotated

            cv2.imshow(PIP_WINDOW_NAME, display_frame)

            key = cv2.waitKey(1) & 0xFF
            if key in (ord("q"), ord("Q"), 27):
                print("\nShutting down...")
                break
            elif key in (ord("r"), ord("R")):
                proc.reset_control()
            elif key in (ord("p"), ord("P")):
                pip_mode = not pip_mode
                if pip_mode:
                    pw = int(width * cfg.pip_scale)
                    ph = int(height * cfg.pip_scale)
                    cv2.resizeWindow(PIP_WINDOW_NAME, pw, ph)
                    time.sleep(0.05)
                    set_window_always_on_top(PIP_WINDOW_NAME, True)
                    print("\nPicture-in-Picture mode ENABLED (always-on-top, no-focus)")
                else:
                    cv2.resizeWindow(PIP_WINDOW_NAME, width, height)
                    set_window_always_on_top(PIP_WINDOW_NAME, False)
                    print("\nPicture-in-Picture mode DISABLED (normal window)")

    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Shutting down...")

    except Exception as e:
        print(f"\nError occurred: {e}")
        import traceback
        traceback.print_exc()

    finally:
        print("Cleaning up...")
        proc.cleanup()
        cap.release()
        cv2.destroyAllWindows()
        print("Cleanup complete. Goodbye!")


if __name__ == "__main__":
    main()

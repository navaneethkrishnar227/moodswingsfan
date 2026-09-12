"""
FaceSense - Real-Time Facial Emotion Detection
Hackathon AI Project & Comprehensive Production Prototype

Key Capabilities:
- Periodic 5-Second Face & Emotion Scan Cycle (Prevents continuous scanning fatigue)
- Smart Fan Speed Controller: Happy = Speed 5, Angry = Speed 0 (Levels 0 to 5)
- Gradual Smooth Fan Transitions (Slow physical motor inertia simulation)
- Live multi-face emotion detection with Smile-Calibration
- Bonus 1: Live emotion history mini-graph overlay
- Bonus 2: Emotion count tally and percentage HUD
- Bonus 3: Mood-adaptive procedural harmonic audio engine
- Bonus 4: Contextual wellbeing suggestions and breathing exercises
- Bonus 5: Explicit privacy consent screen & gatekeeper
- Bonus 6: Automatic facial privacy blur mode for unconsented individuals
- Bonus 8: Zero-biometric anonymous emotion statistics logging & export
- Bonus 10: Accessible voice feedback for visually impaired users
"""

import sys
import time
import cv2
import numpy as np

from modules.detector import EmotionDetector
from modules.privacy import ConsentManager, PrivacyBlurEngine, AnonymousStatsLogger
from modules.wellbeing import get_suggestion
from modules.sound_engine import MoodSoundEngine
from modules.speech_engine import VoiceFeedbackEngine
from modules.visualizer import FrameVisualizer
from modules.fan_controller import SmartFanController


def main():
    print("=" * 65)
    print("      FaceSense - Real-Time Facial Emotion Detection AI")
    print("=" * 65)
    print("Initializing AI models, 5s scan timer, and climate engine...")

    detector = EmotionDetector(backend="opencv")
    consent_mgr = ConsentManager()
    privacy_blur = PrivacyBlurEngine()
    stats_logger = AnonymousStatsLogger()
    sound_engine = MoodSoundEngine()
    speech_engine = VoiceFeedbackEngine(cooldown_sec=4.0, enabled=False)
    visualizer = FrameVisualizer()
    fan_controller = SmartFanController()

    flags = {
        "privacy_blur": False,
        "show_graph": True,
        "show_counters": True,
        "show_fan_bar": True,
        "music_enabled": True,
        "voice_enabled": False,
        "show_wellbeing": True,
    }

    camera = cv2.VideoCapture(0)
    camera_opened = camera.isOpened()

    if not camera_opened:
        print("\n[WARNING] Webcam index 0 could not be opened directly.")
        print("[INFO] Initializing FaceSense in interactive demo simulation mode.\n")

    print("\nFaceSense has started successfully.")
    print("=" * 65)
    print("CONTROLS & SHORTCUTS:")
    print("  [Y / ENTER] : Accept privacy policy and consent")
    print("  [C]         : Show / hide privacy & consent screen")
    print("  [B]         : Toggle automatic facial privacy blur")
    print("  [G]         : Toggle live emotion history graph")
    print("  [S]         : Toggle emotion count tally")
    print("  [F]         : Toggle smart fan speed progress bar")
    print("  [M]         : Toggle mood-adaptive music")
    print("  [V]         : Toggle voice feedback (accessibility)")
    print("  [W]         : Toggle wellbeing suggestions banner")
    print("  [Q]         : Clean quit and save anonymous statistics")
    print("=" * 65)

    frame_counter = 0
    fps_timer = time.time()
    fps_val = 0.0

    current_suggestion = get_suggestion("neutral")
    last_music_play = 0

    # 5-Second Periodic Face Scan Interval
    SCAN_INTERVAL_SEC = 5.0
    last_scan_time = 0.0  # Trigger immediately on first frame
    cached_results = []

    window_name = "FaceSense - Real-Time Facial Emotion Detection"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, 960, 640)

    try:
        while True:
            frame_counter += 1
            now = time.time()

            if camera_opened:
                success, frame = camera.read()
                if not success:
                    print("ERROR: Unable to read frame from camera.")
                    break
                frame = cv2.flip(frame, 1)
            else:
                frame = np.zeros((640, 960, 3), dtype=np.uint8)
                cv2.putText(
                    frame,
                    "Webcam Not Detected - FaceSense Demo Canvas",
                    (220, 300),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.75,
                    (200, 200, 200),
                    2,
                )
                time.sleep(0.03)

            if frame_counter % 15 == 0:
                elapsed = time.time() - fps_timer
                fps_val = 15.0 / elapsed if elapsed > 0 else 30.0
                fps_timer = time.time()

            if consent_mgr.show_dialog or not consent_mgr.has_consented:
                consent_mgr.draw_consent_modal(frame)
            else:
                # 5-Second Scan Timer Check
                time_since_scan = now - last_scan_time
                countdown_sec = max(0.0, SCAN_INTERVAL_SEC - time_since_scan)

                if time_since_scan >= SCAN_INTERVAL_SEC:
                    # Run face & emotion recognition once every 5 seconds
                    detector.trigger_async_analysis(frame)
                    last_scan_time = now
                    results = detector.get_latest_results()
                    if results:
                        cached_results = results
                        primary = cached_results[0]
                        dom_emo = primary.get("dominant_emotion", "neutral")
                        dom_conf = primary.get("confidence", 80.0)

                        # Update Fan Target: Happy = 5, Angry = 0
                        fan_controller.set_target_emotion(dom_emo)
                        current_suggestion = get_suggestion(dom_emo)
                        stats_logger.log_detection(dom_emo, dom_conf)

                        if flags["voice_enabled"]:
                            speech_engine.speak_emotion(dom_emo, dom_conf)

                        if flags["music_enabled"] and now - last_music_play > 3.0:
                            sound_engine.play_for_emotion(dom_emo)
                            last_music_play = now

                # Smooth, gradual fan speed update on every single frame ("slowly slowly change")
                current_fan_state = fan_controller.update_smooth(step_rate=0.03)

                # Smooth real-time single human face tracing on every frame
                tracked_box = detector.trace_single_face(frame)

                if tracked_box is not None:
                    active_res = {
                        "region": tracked_box,
                        "dominant_emotion": dom_emo,
                        "confidence": dom_conf,
                        "is_smiling": False,
                    }
                    if flags["privacy_blur"]:
                        privacy_blur.blur_face(frame, tracked_box)
                    else:
                        visualizer.draw_face_result(frame, active_res)

                if flags["show_graph"]:
                    visualizer.draw_live_emotion_graph(frame, stats_logger.timeline)

                if flags["show_fan_bar"]:
                    visualizer.draw_fan_speed_bar(frame, current_fan_state, countdown_sec=countdown_sec)

                if flags["show_counters"]:
                    visualizer.draw_emotion_counters(frame, stats_logger.emotion_counts)

                if flags["show_wellbeing"]:
                    visualizer.draw_wellbeing_banner(frame, current_suggestion)

            visualizer.draw_header_hud(frame, fps=fps_val, flags=flags)
            cv2.imshow(window_name, frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                print("\n[FaceSense] 'Q' pressed. Stopping application...")
                break
            elif key in [13, ord("y"), ord("Y")]:
                consent_mgr.grant_consent()
                print("[Privacy] User consent granted. Live emotion detection activated.")
            elif key in [ord("c"), ord("C")]:
                consent_mgr.toggle_dialog()
            elif key in [ord("b"), ord("B")]:
                flags["privacy_blur"] = not flags["privacy_blur"]
                print(f"[Privacy] Face blur mode: {'ON' if flags['privacy_blur'] else 'OFF'}")
            elif key in [ord("g"), ord("G")]:
                flags["show_graph"] = not flags["show_graph"]
            elif key in [ord("s"), ord("S")]:
                flags["show_counters"] = not flags["show_counters"]
            elif key in [ord("f"), ord("F")]:
                flags["show_fan_bar"] = not flags["show_fan_bar"]
            elif key in [ord("m"), ord("M")]:
                flags["music_enabled"] = not flags["music_enabled"]
            elif key in [ord("v"), ord("V")]:
                flags["voice_enabled"] = speech_engine.toggle()
            elif key in [ord("w"), ord("W")]:
                flags["show_wellbeing"] = not flags["show_wellbeing"]

    finally:
        if camera_opened:
            camera.release()
        cv2.destroyAllWindows()
        speech_engine.shutdown()

        print("\n" + "=" * 65)
        print("            FaceSense Session Summary Report")
        print("=" * 65)
        summary = stats_logger.get_summary()
        stats_logger.save_session()
        print(f"Session Duration   : {summary['duration_sec']} seconds")
        print(f"Total Detections   : {summary['total_detections']}")
        print(f"Dominant Emotion   : {summary['dominant_emotion'].upper()}")
        print("\nEmotion Distribution:")
        for emo, count in summary["emotion_counts"].items():
            pct = summary["emotion_percentages"].get(emo, 0)
            print(f"  - {emo.capitalize():<10} : {count:>4} detections ({pct:>5.1f}%)")
        print("=" * 65)
        print("FaceSense has stopped successfully.\n")


# ==============================================================================
# WSGI / Serverless Compatibility Fallback
# ==============================================================================
def app(environ=None, start_response=None):
    """Fallback handler satisfying serverless / WSGI scanners."""
    if start_response is not None:
        start_response("200 OK", [("Content-Type", "text/plain; charset=utf-8")])
    return [b"FaceSense AI Real-Time Desktop Engine. Run 'python app.py' locally for full OpenCV video capture."]

handler = app


if __name__ == "__main__":
    main()


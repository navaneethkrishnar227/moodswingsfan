"""
Privacy & Responsible AI Module for FaceSense.
Handles:
1. Explicit user consent screen & verification (Bonus 5).
2. Automatic privacy blurring for unconsented faces (Bonus 6).
3. Zero-biometric anonymous emotion statistics logging & export (Bonus 8).
4. Ethical AI disclaimers and compliance checks.
"""

import os
import json
import time
from datetime import datetime
import cv2
import numpy as np


class ConsentManager:
    """Manages explicit user consent and privacy policy confirmation."""

    def __init__(self):
        self.has_consented = False
        self.consent_timestamp = None
        self.show_dialog = True  # Show on initial startup

    def grant_consent(self):
        self.has_consented = True
        self.show_dialog = False
        self.consent_timestamp = datetime.now().isoformat()
        return True

    def revoke_consent(self):
        self.has_consented = False
        self.show_dialog = True
        self.consent_timestamp = None
        return False

    def toggle_dialog(self):
        self.show_dialog = not self.show_dialog

    def draw_consent_modal(self, frame):
        """Renders a sleek, high-contrast privacy & consent dialog overlay on an OpenCV frame."""
        h, w, _ = frame.shape

        # Dark translucent overlay
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, h), (15, 20, 28), -1)
        cv2.addWeighted(overlay, 0.88, frame, 0.12, 0, frame)

        # Card boundaries
        card_w, card_h = min(720, w - 40), min(480, h - 40)
        cx, cy = w // 2, h // 2
        x1, y1 = cx - card_w // 2, cy - card_h // 2
        x2, y2 = cx + card_w // 2, cy + card_h // 2

        # Card container with glowing cyan border
        cv2.rectangle(frame, (x1, y1), (x2, y2), (28, 38, 52), -1)
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 220, 255), 2)

        # Title header
        cv2.rectangle(frame, (x1, y1), (x2, y1 + 55), (38, 50, 68), -1)
        cv2.putText(
            frame,
            "FaceSense - Ethical AI & Privacy Consent",
            (x1 + 20, y1 + 38),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.75,
            (0, 240, 255),
            2,
        )

        lines = [
            "RESPONSIBLE AI & ETHICAL USE POLICY:",
            "- This tool estimates visible expressions, NOT true feelings or intent.",
            "- NO face images, biometrics, or personal identities are saved.",
            "- Only aggregated, anonymous emotion statistics are stored locally.",
            "- Do NOT use for surveillance, evaluation, or high-stakes decisions.",
            "",
            "PRIVACY CONTROLS:",
            "- Press [ENTER] or [Y] to Grant Camera & Emotion Analysis Consent.",
            "- Press [B] to toggle Automatic Face Blurring (Privacy Shield).",
            "- Press [C] anytime to re-open or review this Privacy Notice.",
            "- Press [Q] to quit safely at any time.",
        ]

        start_y = y1 + 95
        for i, line in enumerate(lines):
            color = (255, 255, 255)
            font_scale = 0.50
            thickness = 1

            if line.startswith("RESPONSIBLE") or line.startswith("PRIVACY"):
                color = (0, 220, 255)
                font_scale = 0.55
                thickness = 2
            elif line.startswith("- Press"):
                color = (120, 230, 160)
                font_scale = 0.52
                thickness = 1

            cv2.putText(
                frame,
                line,
                (x1 + 25, start_y + (i * 26)),
                cv2.FONT_HERSHEY_SIMPLEX,
                font_scale,
                color,
                thickness,
            )

        # Action button highlight
        btn_y = y2 - 45
        cv2.rectangle(frame, (x1 + 25, btn_y - 25), (x1 + 320, btn_y + 15), (0, 180, 120), -1)
        cv2.putText(
            frame,
            "[Y / ENTER] I CONSENT & PROCEED",
            (x1 + 35, btn_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (255, 255, 255),
            2,
        )


class PrivacyBlurEngine:
    """Provides privacy protection and facial blurring for unconsented subjects."""

    @staticmethod
    def blur_face(frame, region, kernel_size=(51, 51)):
        """Applies strong Gaussian blur over a bounding box region."""
        x = max(0, int(region.get("x", 0)))
        y = max(0, int(region.get("y", 0)))
        w = int(region.get("w", 0))
        h = int(region.get("h", 0))

        img_h, img_w, _ = frame.shape
        x2 = min(img_w, x + w)
        y2 = min(img_h, y + h)

        if w <= 0 or h <= 0 or x >= img_w or y >= img_h:
            return frame

        roi = frame[y:y2, x:x2]
        if roi.size > 0:
            blurred_roi = cv2.GaussianBlur(roi, kernel_size, 30)
            frame[y:y2, x:x2] = blurred_roi

            # Draw a subtle privacy badge
            cv2.rectangle(frame, (x, y), (x2, y2), (200, 120, 50), 2)
            label = "PRIVACY BLURRED"
            cv2.putText(
                frame,
                label,
                (x + 5, max(y - 8, 20)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                (200, 120, 50),
                1,
            )
        return frame

    @staticmethod
    def pixelate_face(frame, region, blocks=12):
        """Pixelates a facial region for privacy protection."""
        x = max(0, int(region.get("x", 0)))
        y = max(0, int(region.get("y", 0)))
        w = int(region.get("w", 0))
        h = int(region.get("h", 0))

        img_h, img_w, _ = frame.shape
        x2 = min(img_w, x + w)
        y2 = min(img_h, y + h)

        if w <= 0 or h <= 0:
            return frame

        roi = frame[y:y2, x:x2]
        if roi.shape[0] > 0 and roi.shape[1] > 0:
            small = cv2.resize(roi, (blocks, blocks), interpolation=cv2.INTER_LINEAR)
            pixelated = cv2.resize(small, (roi.shape[1], roi.shape[0]), interpolation=cv2.INTER_NEAREST)
            frame[y:y2, x:x2] = pixelated
        return frame


class AnonymousStatsLogger:
    """Stores purely anonymous, non-biometric emotion frequency counts and session timelines."""

    def __init__(self, data_file=None):
        if data_file is None:
            data_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "anonymous_stats.json")
        self.data_file = data_file
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)

        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.start_time = time.time()
        self.emotion_counts = {
            "happy": 0,
            "sad": 0,
            "angry": 0,
            "surprise": 0,
            "fear": 0,
            "disgust": 0,
            "neutral": 0,
        }
        self.timeline = []  # List of {timestamp, emotion, confidence}

    def log_detection(self, emotion, confidence):
        """Logs an anonymous detection record."""
        emotion = emotion.lower().strip()
        if emotion in self.emotion_counts:
            self.emotion_counts[emotion] += 1

        entry = {
            "time_offset_sec": round(time.time() - self.start_time, 2),
            "emotion": emotion,
            "confidence": round(float(confidence), 1),
        }
        self.timeline.append(entry)

        # Cap memory timeline to latest 1000 items
        if len(self.timeline) > 1000:
            self.timeline.pop(0)

    def get_summary(self):
        """Returns statistics summary without biometric identifiers."""
        total = sum(self.emotion_counts.values())
        percentages = {k: round((v / total * 100), 1) if total > 0 else 0.0 for k, v in self.emotion_counts.items()}
        dominant = max(self.emotion_counts, key=self.emotion_counts.get) if total > 0 else "neutral"

        return {
            "session_id": self.session_id,
            "duration_sec": round(time.time() - self.start_time, 1),
            "total_detections": total,
            "dominant_emotion": dominant,
            "emotion_counts": self.emotion_counts.copy(),
            "emotion_percentages": percentages,
        }

    def save_session(self):
        """Persists anonymous statistics to JSON disk."""
        summary = self.get_summary()
        summary["timeline_sample"] = self.timeline[-100:]  # Store last 100 anonymous records

        existing_data = []
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, "r") as f:
                    existing_data = json.load(f)
                    if not isinstance(existing_data, list):
                        existing_data = [existing_data]
            except Exception:
                existing_data = []

        existing_data.append(summary)
        # Keep up to last 20 sessions
        existing_data = existing_data[-20:]

        try:
            with open(self.data_file, "w") as f:
                json.dump(existing_data, f, indent=2)
            print(f"[Privacy] Anonymous emotion statistics recorded to: {self.data_file}")
        except Exception as e:
            print(f"[Privacy] Error recording stats: {e}")

    def clear(self):
        """Resets current session metrics."""
        self.start_time = time.time()
        for k in self.emotion_counts:
            self.emotion_counts[k] = 0
        self.timeline.clear()

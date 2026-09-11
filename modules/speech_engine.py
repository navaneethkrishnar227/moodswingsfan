"""
Voice Feedback Engine for FaceSense.
Provides spoken feedback and audio cues for visually impaired accessibility.
Thread-safe, rate-limited, and non-blocking.
"""

import threading
import queue
import time

try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False


class VoiceFeedbackEngine:
    """Provides non-blocking voice narration for detected emotions."""

    def __init__(self, cooldown_sec=4.0, enabled=False):
        self.cooldown_sec = cooldown_sec
        self.is_enabled = enabled
        self.last_spoken_emotion = None
        self.last_spoken_time = 0
        self.speech_queue = queue.Queue()
        self._stop_event = threading.Event()
        self._worker_thread = None

        if PYTTSX3_AVAILABLE:
            self._start_worker()

    def _start_worker(self):
        def _speech_worker():
            try:
                engine = pyttsx3.init()
                engine.setProperty("rate", 160)
                engine.setProperty("volume", 0.9)
            except Exception as e:
                print(f"[SpeechEngine] Warning initializing pyttsx3: {e}")
                return

            while not self._stop_event.is_set():
                try:
                    text = self.speech_queue.get(timeout=0.5)
                    if text:
                        try:
                            engine.say(text)
                            engine.runAndWait()
                        except Exception as e:
                            print(f"[SpeechEngine] Error speaking: {e}")
                    self.speech_queue.task_done()
                except queue.Empty:
                    continue

        self._worker_thread = threading.Thread(target=_speech_worker, daemon=True)
        self._worker_thread.start()

    def speak_emotion(self, emotion, confidence, force=False):
        """Speaks the detected emotion if cooldown has expired or emotion changed."""
        if not self.is_enabled or not PYTTSX3_AVAILABLE:
            return

        now = time.time()
        emotion = emotion.capitalize()

        # Cooldown check or distinct emotion transition check
        if force or (emotion != self.last_spoken_emotion and now - self.last_spoken_time > 2.5) or (now - self.last_spoken_time > self.cooldown_sec):
            self.last_spoken_emotion = emotion
            self.last_spoken_time = now
            text = f"Emotion: {emotion}, confidence {int(confidence)} percent."
            # Only queue if not already flooded
            if self.speech_queue.qsize() < 2:
                self.speech_queue.put(text)

    def speak_custom(self, text):
        """Speaks any custom feedback or accessibility announcement."""
        if not self.is_enabled or not PYTTSX3_AVAILABLE:
            return
        if self.speech_queue.qsize() < 2:
            self.speech_queue.put(text)

    def toggle(self):
        """Toggles voice feedback on/off."""
        self.is_enabled = not self.is_enabled
        state = "enabled" if self.is_enabled else "disabled"
        if self.is_enabled:
            self.speak_custom("Voice assistance enabled.")
        return self.is_enabled

    def shutdown(self):
        self._stop_event.set()

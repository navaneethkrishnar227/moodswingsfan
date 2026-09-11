"""
Smart Fan Speed & Climate Controller for FaceSense (Moodswings).
Maps emotions to discrete Speed Levels (0 to 5):
- Happy -> Speed 5 (Max)
- Angry -> Speed 0 (Off)
Applies gradual, smooth physical inertia (slow, gradual transitions) without abrupt jumping.
"""

import time


class SmartFanController:
    """Calculates mood-adaptive fan speeds (Levels 0-5) with gradual smooth transitions."""

    # Explicit user rules: Happy = 5, Angry = 0
    EMOTION_LEVELS = {
        "happy": 5,
        "surprise": 4,
        "neutral": 3,
        "sad": 2,
        "fear": 1,
        "disgust": 1,
        "angry": 0,
    }

    LEVEL_INFO = {
        0: {"mode": "Fan Stopped (0 / 5)", "rpm": 0, "color": "#e74c3c", "desc": "Angry state: Fan turned completely OFF (Speed 0)."},
        1: {"mode": "Ultra Whisper (1 / 5)", "rpm": 450, "color": "#9b59b6", "desc": "Low circulation comfort mode (Speed 1)."},
        2: {"mode": "Gentle Draft (2 / 5)", "rpm": 850, "color": "#95a5a6", "desc": "Warm comforting low-speed airflow (Speed 2)."},
        3: {"mode": "Balanced Flow (3 / 5)", "rpm": 1350, "color": "#3498db", "desc": "Calm neutral baseline focus mode (Speed 3)."},
        4: {"mode": "Active Breeze (4 / 5)", "rpm": 1850, "color": "#f1c40f", "desc": "Elevated airflow ventilation (Speed 4)."},
        5: {"mode": "Turbo Full Power (5 / 5)", "rpm": 2400, "color": "#2ecc71", "desc": "Happy state: Maximum Fan Speed 5 (Full cooling)."},
    }

    def __init__(self):
        self.manual_override = False
        self.manual_level = 3
        self.current_speed_float = 3.0  # Smooth continuous float between 0.0 and 5.0
        self.target_speed_float = 3.0
        self.last_update_time = time.time()

    def set_target_emotion(self, emotion):
        """Sets target fan level from detected emotion."""
        emotion = emotion.lower().strip()
        target = self.EMOTION_LEVELS.get(emotion, 3)
        self.target_speed_float = float(target)

    def update_smooth(self, target_level=None, step_rate=0.04):
        """
        Slowly and gradually transitions the fan speed towards target level.
        Prevents sudden jumps, mimicking natural physical fan motor acceleration.
        """
        if target_level is not None:
            self.target_speed_float = float(target_level)
        elif self.manual_override:
            self.target_speed_float = float(self.manual_level)

        diff = self.target_speed_float - self.current_speed_float
        if abs(diff) > 0.01:
            # Move slowly towards target
            step = diff * step_rate
            # Ensure minimum movement so it eventually reaches the target
            if abs(step) < 0.005:
                step = 0.005 if diff > 0 else -0.005
            self.current_speed_float += step
            self.current_speed_float = max(0.0, min(5.0, self.current_speed_float))
        else:
            self.current_speed_float = self.target_speed_float

        return self.get_current_state()

    def get_current_state(self):
        """Returns the current smoothed fan speed metrics."""
        display_level = round(self.current_speed_float, 1)
        discrete_level = int(round(self.current_speed_float))
        discrete_level = max(0, min(5, discrete_level))

        info = self.LEVEL_INFO[discrete_level]
        percent = int((self.current_speed_float / 5.0) * 100)
        rpm = int((self.current_speed_float / 5.0) * 2400) if self.current_speed_float > 0.1 else 0

        return {
            "speed_level": display_level,
            "target_level": int(self.target_speed_float),
            "discrete_level": discrete_level,
            "speed_percent": percent,
            "rpm": rpm,
            "mode": info["mode"],
            "description": info["desc"],
            "color": info["color"],
        }

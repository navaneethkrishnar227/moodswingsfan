"""
Visualizer Module for FaceSense.
Provides modern HUD graphics, bounding boxes, glowing badges, live history graph,
counters, 5-second scan countdown, and an Animated Rotating Fan with side-by-side RPM
and Speed Level 0-5 indicators on OpenCV frames.
"""

import time
import math
import cv2
import numpy as np

EMOTION_COLORS_BGR = {
    "happy": (113, 204, 46),       # Vibrant Emerald Green
    "sad": (219, 152, 52),         # Calming Ocean Blue
    "angry": (60, 76, 231),        # Crimson Red
    "surprise": (15, 196, 241),    # Radiant Gold
    "fear": (182, 89, 155),        # Electric Purple
    "disgust": (96, 174, 39),      # Deep Teal / Olive
    "neutral": (230, 220, 210),    # Cool Clean White / Silver
    "unknown": (180, 180, 180),
}


class FrameVisualizer:
    """Renders modern aesthetic overlays, graphs, and bounding boxes on frames."""

    def __init__(self):
        self.fan_angle = 0.0

    @staticmethod
    def get_emotion_color(emotion):
        return EMOTION_COLORS_BGR.get(emotion.lower(), (255, 255, 255))

    @staticmethod
    def draw_corner_box(frame, x, y, w, h, color, thickness=2, corner_len=18):
        """Draws a sleek tech bounding box with highlighted futuristic corners."""
        cv2.rectangle(frame, (x, y), (x + w, y + h), color, 1)

        # Top-Left
        cv2.line(frame, (x, y), (x + corner_len, y), color, thickness + 1)
        cv2.line(frame, (x, y), (x, y + corner_len), color, thickness + 1)

        # Top-Right
        cv2.line(frame, (x + w, y), (x + w - corner_len, y), color, thickness + 1)
        cv2.line(frame, (x + w, y), (x + w, y + corner_len), color, thickness + 1)

        # Bottom-Left
        cv2.line(frame, (x, y + h), (x + corner_len, y + h), color, thickness + 1)
        cv2.line(frame, (x, y + h), (x, y + h - corner_len), color, thickness + 1)

        # Bottom-Right
        cv2.line(frame, (x + w, y + h), (x + w - corner_len, y + h), color, thickness + 1)
        cv2.line(frame, (x + w, y + h), (x + w, y + h - corner_len), color, thickness + 1)

    def draw_face_result(self, frame, result):
        """Draws face box, glowing pill badge, emotion name, and confidence bar."""
        region = result.get("region", {})
        x = max(0, int(region.get("x", 0)))
        y = max(0, int(region.get("y", 0)))
        w = int(region.get("w", 0))
        h = int(region.get("h", 0))

        if w <= 10 or h <= 10:
            return

        dominant = result.get("dominant_emotion", "neutral").lower()
        confidence = float(result.get("confidence", 0.0))
        color = self.get_emotion_color(dominant)

        self.draw_corner_box(frame, x, y, w, h, color)

        is_smiling = result.get("is_smiling", False)
        smile_text = " [SMILE]" if is_smiling else ""
        label = f"{dominant.upper()}{smile_text} : {confidence:.1f}%"

        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.55
        (tw, th), baseline = cv2.getTextSize(label, font, font_scale, 2)

        badge_y = max(y - 10, th + 15)
        cv2.rectangle(
            frame,
            (x, badge_y - th - 8),
            (x + tw + 14, badge_y + 4),
            color,
            -1,
        )

        cv2.putText(
            frame,
            label,
            (x + 7, badge_y - 2),
            font,
            font_scale,
            (10, 15, 20),
            2,
        )

        bar_y = y + h + 6
        bar_w = w
        bar_h = 4
        if bar_y + bar_h < frame.shape[0]:
            cv2.rectangle(frame, (x, bar_y), (x + bar_w, bar_y + bar_h), (50, 50, 50), -1)
            filled_w = int((confidence / 100.0) * bar_w)
            cv2.rectangle(frame, (x, bar_y), (x + filled_w, bar_y + bar_h), color, -1)

    def draw_fan_speed_bar(self, frame, fan_state, countdown_sec=0.0, x=20, y=225, w=300, h=92):
        """
        Renders an Animated Rotating Fan on the left, with RPM Speed and 0 1 2 3 4 5
        Speed Level indicators side-by-side on the right.
        """
        sub_img = frame[y : y + h, x : x + w]
        if sub_img.shape[0] != h or sub_img.shape[1] != w:
            return

        overlay = sub_img.copy()
        cv2.rectangle(overlay, (0, 0), (w, h), (16, 22, 32), -1)
        cv2.addWeighted(overlay, 0.85, sub_img, 0.15, 0, sub_img)
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 230, 184), 1)

        level = fan_state.get("speed_level", 3.0)
        discrete = fan_state.get("discrete_level", 3)
        rpm = fan_state.get("rpm", 1350)
        mode = fan_state.get("mode", "Balanced Flow")

        # Update animated rotation angle based on user requirements:
        # Speed 5: Rotates heavily (fast turbo spin)
        # Speed 2: Small speed rotate (calm gentle spin)
        # Speed 0: No rotate at all (stationary)
        if discrete == 0 or level <= 0.05:
            spin_step = 0.0  # 0 RPM - NO ROTATION AT 0
        elif discrete == 1:
            spin_step = 2.0   # Whisper slow
        elif discrete == 2:
            spin_step = 4.5   # SMALL SPEED ROTATE (Gentle breeze)
        elif discrete == 3:
            spin_step = 12.0  # Moderate flow
        elif discrete == 4:
            spin_step = 25.0  # Fast airflow
        else:  # discrete >= 5
            spin_step = 52.0  # ROTATES HEAVILY ON 5TH SPEED (Turbo Vortex)

        if spin_step > 0.0:
            self.fan_angle = (self.fan_angle + spin_step) % 360.0

        # --- LEFT SIDE: ANIMATED ROTATING FAN ---
        fan_cx = x + 44
        fan_cy = y + 46
        fan_r = 34

        # Outer casing & protective grill
        fan_border_col = (0, 230, 184) if discrete >= 4 else ((0, 200, 255) if discrete >= 2 else ((100, 100, 220) if discrete == 1 else (60, 60, 220)))
        cv2.circle(frame, (fan_cx, fan_cy), fan_r, (20, 28, 42), -1)
        cv2.circle(frame, (fan_cx, fan_cy), fan_r, fan_border_col, 2)
        cv2.circle(frame, (fan_cx, fan_cy), fan_r - 4, (45, 60, 80), 1)

        # Cross wire grill
        cv2.line(frame, (fan_cx - fan_r + 4, fan_cy), (fan_cx + fan_r - 4, fan_cy), (35, 50, 70), 1)
        cv2.line(frame, (fan_cx, fan_cy - fan_r + 4), (fan_cx, fan_cy + fan_r - 4), (35, 50, 70), 1)

        # High-Speed Vortex Streaks for Level 5 (Heavy Turbo Spin Visuals)
        if discrete >= 5:
            for arc_offset in [0, 90, 180, 270]:
                arc_start = int(self.fan_angle + arc_offset) % 360
                cv2.ellipse(frame, (fan_cx, fan_cy), (fan_r - 2, fan_r - 2), 0, arc_start, arc_start + 45, (0, 240, 180), 2)

        # Draw 4 rotating curved aerodynamic blades
        rad_base = math.radians(self.fan_angle)
        if discrete >= 5:
            blade_col = (0, 230, 184)  # Vivid Turbo Emerald
        elif discrete >= 3:
            blade_col = (0, 210, 240)  # Bright Cyan
        elif discrete >= 2:
            blade_col = (0, 170, 230)  # Calm Sky Blue (Speed 2)
        elif discrete == 1:
            blade_col = (140, 140, 200) # Soft Violet
        else:
            blade_col = (70, 70, 140)   # Inactive Slate (Speed 0)

        for i in range(4):
            blade_angle = rad_base + (i * math.pi / 2.0)
            tip_x = int(fan_cx + (fan_r - 6) * math.cos(blade_angle))
            tip_y = int(fan_cy + (fan_r - 6) * math.sin(blade_angle))
            perp_angle = blade_angle + math.pi / 4.0
            mid_x = int(fan_cx + (fan_r * 0.55) * math.cos(perp_angle))
            mid_y = int(fan_cy + (fan_r * 0.55) * math.sin(perp_angle))

            pts = np.array([[fan_cx, fan_cy], [mid_x, mid_y], [tip_x, tip_y]], np.int32)
            cv2.fillPoly(frame, [pts], blade_col)

        # Central motor hub
        cv2.circle(frame, (fan_cx, fan_cy), 8, (15, 20, 30), -1)
        cv2.circle(frame, (fan_cx, fan_cy), 8, fan_border_col, 2)
        cv2.circle(frame, (fan_cx, fan_cy), 3, (255, 255, 255) if discrete > 0 else (100, 100, 100), -1)

        # --- RIGHT SIDE: RPM & 0 1 2 3 4 5 LEVEL INDICATOR ---
        side_x = x + 88

        # RPM Speed display (Large, bold, high-contrast)
        rpm_color = (0, 245, 255) if discrete > 0 else (120, 120, 220)
        rpm_text = f"{rpm} RPM"
        # Shadow for readability
        cv2.putText(frame, rpm_text, (side_x + 1, y + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 0, 0), 3)
        cv2.putText(frame, rpm_text, (side_x, y + 24), cv2.FONT_HERSHEY_SIMPLEX, 0.65, rpm_color, 2)

        # Mode label
        mode_text = f"{mode}"
        cv2.putText(frame, mode_text, (side_x + 120, y + 23), cv2.FONT_HERSHEY_SIMPLEX, 0.44, (0, 0, 0), 2)
        cv2.putText(frame, mode_text, (side_x + 120, y + 23), cv2.FONT_HERSHEY_SIMPLEX, 0.44, (220, 235, 250), 1)

        # Speed Level 0 1 2 3 4 5 Blocks
        cv2.putText(frame, "SPEED:", (side_x, y + 50), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 0, 0), 2)
        cv2.putText(frame, "SPEED:", (side_x, y + 50), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (180, 200, 220), 1)

        # Draw 0 1 2 3 4 5 boxes (Comfortable size & readable text)
        box_start_x = side_x + 55
        box_w = 26
        box_h = 22
        box_gap = 5

        for lvl in range(6):
            bx = box_start_x + lvl * (box_w + box_gap)
            by = y + 33
            is_active = (lvl == discrete)
            is_past = (lvl <= discrete and discrete > 0)

            if is_active:
                box_bg = (0, 230, 120) if lvl == 5 else ((50, 50, 230) if lvl == 0 else (0, 190, 255))
                text_col = (10, 15, 25)
            elif is_past:
                box_bg = (40, 70, 90)
                text_col = (0, 230, 184)
            else:
                box_bg = (25, 32, 45)
                text_col = (120, 140, 160)

            cv2.rectangle(frame, (bx, by), (bx + box_w, by + box_h), box_bg, -1)
            cv2.rectangle(frame, (bx, by), (bx + box_w, by + box_h), (0, 230, 184) if is_active else (60, 75, 95), 1)

            cv2.putText(
                frame,
                str(lvl),
                (bx + 8, by + 16),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.48,
                text_col,
                2 if is_active else 1,
            )

        # Bottom row: Countdown & Smooth level indicator (High readability)
        scan_text = f"Scan: {countdown_sec:.1f}s" if countdown_sec > 0 else "Scanning..."
        sub_text = f"Level: {level:.1f}/5  |  {scan_text}"
        cv2.putText(frame, sub_text, (side_x, y + 80), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 0, 0), 2)
        cv2.putText(frame, sub_text, (side_x, y + 80), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 230, 184), 1)

    def draw_live_emotion_graph(self, frame, timeline, x=20, y=100, w=260, h=110):
        if not timeline or len(timeline) < 2:
            return

        sub_img = frame[y : y + h, x : x + w]
        if sub_img.shape[0] != h or sub_img.shape[1] != w:
            return

        overlay = sub_img.copy()
        cv2.rectangle(overlay, (0, 0), (w, h), (18, 22, 30), -1)
        cv2.addWeighted(overlay, 0.75, sub_img, 0.25, 0, sub_img)
        cv2.rectangle(frame, (x, y), (x + w, y + h), (60, 75, 95), 1)

        cv2.putText(
            frame,
            "EMOTION TIMELINE (LIVE)",
            (x + 10, y + 18),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.38,
            (0, 220, 255),
            1,
        )

        recent = timeline[-30:]
        num_points = len(recent)
        step_x = (w - 24) / max(num_points - 1, 1)

        pts = []
        for idx, entry in enumerate(recent):
            conf = entry.get("confidence", 50.0)
            emo = entry.get("emotion", "neutral")
            norm_y = 1.0 - (conf / 100.0)
            pt_x = int(x + 12 + (idx * step_x))
            pt_y = int(y + 32 + (norm_y * (h - 46)))
            pts.append((pt_x, pt_y, emo))

        for i in range(len(pts) - 1):
            p1 = (pts[i][0], pts[i][1])
            p2 = (pts[i + 1][0], pts[i + 1][1])
            col = self.get_emotion_color(pts[i + 1][2])
            cv2.line(frame, p1, p2, col, 2)
            cv2.circle(frame, p2, 2, col, -1)

    def draw_emotion_counters(self, frame, emotion_counts, x=None, y=100, w=220, h=175):
        img_h, img_w, _ = frame.shape
        if x is None:
            x = img_w - w - 20

        sub_img = frame[y : y + h, x : x + w]
        if sub_img.shape[0] != h or sub_img.shape[1] != w:
            return

        overlay = sub_img.copy()
        cv2.rectangle(overlay, (0, 0), (w, h), (18, 22, 30), -1)
        cv2.addWeighted(overlay, 0.75, sub_img, 0.25, 0, sub_img)
        cv2.rectangle(frame, (x, y), (x + w, y + h), (60, 75, 95), 1)

        cv2.putText(
            frame,
            "EMOTION COUNTER",
            (x + 10, y + 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.42,
            (0, 220, 255),
            1,
        )

        total = sum(emotion_counts.values())
        line_y = y + 42

        for emo, count in emotion_counts.items():
            col = self.get_emotion_color(emo)
            pct = (count / total * 100) if total > 0 else 0
            cv2.circle(frame, (x + 16, line_y - 4), 4, col, -1)
            text = f"{emo.capitalize():<8} : {count:>3} ({pct:4.1f}%)"
            cv2.putText(
                frame,
                text,
                (x + 28, line_y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.36,
                (230, 230, 230),
                1,
            )
            line_y += 18

    def draw_wellbeing_banner(self, frame, suggestion):
        img_h, img_w, _ = frame.shape
        banner_h = 60
        y1 = img_h - banner_h - 12
        x1 = 20
        x2 = img_w - 20

        sub = frame[y1 : y1 + banner_h, x1:x2]
        if sub.size == 0:
            return

        overlay = sub.copy()
        cv2.rectangle(overlay, (0, 0), (x2 - x1, banner_h), (15, 20, 30), -1)
        cv2.addWeighted(overlay, 0.85, sub, 0.15, 0, sub)
        cv2.rectangle(frame, (x1, y1), (x2, y1 + banner_h), (0, 200, 150), 1)

        title = f"WELLBEING: {suggestion.get('title', 'Mental Check-in')}"
        cv2.putText(
            frame,
            title,
            (x1 + 15, y1 + 22),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.48,
            (0, 220, 180),
            1,
        )

        advice = suggestion.get("advice", "")
        cv2.putText(
            frame,
            advice,
            (x1 + 15, y1 + 46),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.42,
            (240, 240, 240),
            1,
        )

    def draw_header_hud(self, frame, fps=0, flags=None):
        if flags is None:
            flags = {}

        img_h, img_w, _ = frame.shape

        cv2.rectangle(frame, (0, 0), (img_w, 48), (14, 18, 25), -1)
        cv2.line(frame, (0, 48), (img_w, 48), (40, 50, 70), 1)

        cv2.putText(
            frame,
            "FaceSense",
            (18, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.75,
            (0, 230, 255),
            2,
        )

        cv2.putText(
            frame,
            "Real-Time Emotion AI & Climate Control",
            (145, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (180, 190, 205),
            1,
        )

        hotkeys_text = "[C] Consent  [B] Blur  [G] Graph  [S] Stats  [F] Fan  [M] Music  [V] Voice  [W] Wellness  [Q] Quit"
        cv2.putText(
            frame,
            hotkeys_text,
            (20, img_h - 15) if not flags.get("show_wellbeing") else (img_w - 530, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.34,
            (160, 175, 195),
            1,
        )

"""
FaceSense AI - Real-Time Smart Climate & Facial Emotion Dashboard
Comfortable, Spacious, High-Contrast Dashboard with Large Camera Viewport.
Features:
- Large, immersive camera viewport (460px height) providing clear, commanding visibility.
- Comfortable, spacious layout ("comforty and not conjusted") with generous padding and breathing room.
- Large, bold, highly readable typography across all metrics, badges, and controls.
- Strict Single Human Face Detection & Tracing (EMA smoothed, rejects all background objects).
- Decoupled 30 FPS continuous face tracing with periodic 5.0s DeepFace emotion classification.
- Smart Climate Fan: Happy = Speed 5 (heavy rapid rotation), Angry = Speed 0 (stopped), Speed 2 = gentle breeze.
- Prominent Side-by-Side RPM Tachometer & Segmented 0 1 2 3 4 5 Speed Blocks with Sub-Labels.
- Clear 7-Emotion Horizontal Probability Meters & Anonymous Session Telemetry.
"""

import os
import io
import time
import random
import cv2
import numpy as np
import streamlit as st

from modules.detector import EmotionDetector
from modules.privacy import PrivacyBlurEngine, AnonymousStatsLogger
from modules.wellbeing import get_suggestion
from modules.sound_engine import MoodSoundEngine
from modules.visualizer import FrameVisualizer, EMOTION_COLORS_BGR
from modules.fan_controller import SmartFanController

# ==============================================================================
# STREAMLIT PAGE CONFIG & COMFORTABLE, HIGH-CONTRAST CSS
# ==============================================================================
st.set_page_config(
    page_title="FaceSense AI | Smart Climate & Emotion",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Comfortable, Spacious, High-Contrast CSS Design System
st.markdown(
    """
<style>
/* Modern Bold High-Legibility Typography */
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800;900&display=swap');

/* Clean Full-Viewport Background */
html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
    background: radial-gradient(circle at 15% 15%, #0d1527 0%, #060911 100%) !important;
    color: #ffffff !important;
    font-family: 'Outfit', -apple-system, BlinkMacSystemFont, sans-serif !important;
    overflow-x: hidden !important;
}

/* Hide default Streamlit decoration, header and footer */
header[data-testid="stHeader"], footer, #MainMenu {
    display: none !important;
}

/* Comfortable, spacious page padding */
.block-container, [data-testid="stAppViewBlockContainer"] {
    padding: 0.8rem 2.0rem 1.4rem 2.0rem !important;
    max-width: 100% !important;
    box-sizing: border-box !important;
}

/* Spacious, Professional Glassmorphic Cards (Comfortable & Not Congested) */
.pro-card {
    background: linear-gradient(135deg, rgba(16, 25, 42, 0.94) 0%, rgba(10, 16, 28, 0.98) 100%);
    border: 1.5px solid rgba(255, 255, 255, 0.16);
    border-radius: 14px;
    padding: 16px 20px;
    box-shadow: 0 8px 26px rgba(0, 0, 0, 0.55);
    margin-bottom: 14px;
    font-family: 'Outfit', sans-serif;
}

.pro-card-glow {
    border: 1.5px solid rgba(0, 255, 178, 0.55);
    box-shadow: 0 0 22px rgba(0, 255, 178, 0.2);
}

/* Large, Immersive Camera Viewport Styling */
[data-testid="stImage"] img {
    border-radius: 14px !important;
    border: 2px solid rgba(0, 255, 178, 0.5) !important;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.7) !important;
    height: 460px !important;
    max-height: 480px !important;
    width: 100% !important;
    object-fit: cover !important;
    background: #000000 !important;
}

/* Large, Comfortable, Readable Action Buttons */
div.stButton > button {
    border-radius: 10px !important;
    font-weight: 800 !important;
    font-size: 1.02rem !important;
    padding: 10px 18px !important;
    letter-spacing: 0.3px !important;
    transition: all 0.18s ease !important;
    border: 1.5px solid rgba(255, 255, 255, 0.22) !important;
    color: #ffffff !important;
}

div.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 24px rgba(0, 255, 178, 0.38) !important;
    border-color: #00ffb2 !important;
}

/* Checkbox Labels Readability */
div[data-testid="stCheckbox"] label span {
    font-size: 0.98rem !important;
    font-weight: 700 !important;
    color: #ffffff !important;
}

/* Slider Readability */
div[data-testid="stSlider"] label {
    font-size: 1.02rem !important;
    font-weight: 800 !important;
    color: #00ffb2 !important;
}

/* Column Spacing */
div[data-testid="stHorizontalBlock"] {
    gap: 1.4rem !important;
    align-items: stretch !important;
}

/* Clean Sleek Scrollbar */
::-webkit-scrollbar {
    width: 7px;
    height: 7px;
}
::-webkit-scrollbar-track {
    background: #060911;
}
::-webkit-scrollbar-thumb {
    background: #1e293b;
    border-radius: 4px;
}
::-webkit-scrollbar-thumb:hover {
    background: #00ffb2;
}
</style>
""",
    unsafe_allow_html=True,
)


@st.cache_resource
def load_core_engines():
    detector = EmotionDetector(backend="opencv")
    sound_engine = MoodSoundEngine()
    visualizer = FrameVisualizer()
    fan_controller = SmartFanController()
    return detector, sound_engine, visualizer, fan_controller


detector, sound_engine, visualizer, fan_controller = load_core_engines()

# Session State Initialization
if "user_consented" not in st.session_state:
    st.session_state.user_consented = True
if "anonymous_logs" not in st.session_state:
    st.session_state.anonymous_logs = []
if "emotion_counts" not in st.session_state:
    st.session_state.emotion_counts = {
        "happy": 0, "sad": 0, "angry": 0, "surprise": 0,
        "fear": 0, "disgust": 0, "neutral": 0
    }
if "latest_emotion" not in st.session_state:
    st.session_state.latest_emotion = "neutral"
if "latest_confidence" not in st.session_state:
    st.session_state.latest_confidence = 85.0
if "privacy_blur" not in st.session_state:
    st.session_state.privacy_blur = False
if "music_enabled" not in st.session_state:
    st.session_state.music_enabled = False
if "live_streaming" not in st.session_state:
    st.session_state.live_streaming = False
if "manual_override" not in st.session_state:
    st.session_state.manual_override = False
if "manual_speed" not in st.session_state:
    st.session_state.manual_speed = 3


def log_emotion(emotion, confidence):
    emotion = emotion.lower().strip()
    if emotion in st.session_state.emotion_counts:
        st.session_state.emotion_counts[emotion] += 1
    st.session_state.latest_emotion = emotion
    st.session_state.latest_confidence = float(confidence)
    st.session_state.anonymous_logs.append({
        "timestamp": time.strftime("%H:%M:%S"),
        "emotion": emotion,
        "confidence": round(float(confidence), 1),
    })
    if len(st.session_state.anonymous_logs) > 500:
        st.session_state.anonymous_logs.pop(0)


# ==============================================================================
# CARD 1: COMFORTABLE, READABLE ANIMATED FAN & TACHOMETER WIDGET
# ==============================================================================
def render_fan_widget_html(fan_state, countdown_sec=None):
    """Generates bold, clear, comfortable HTML/SVG for the calibrated animated fan with tachometer & levels."""
    speed_level = fan_state["speed_level"]
    discrete = fan_state["discrete_level"]
    target = fan_state["target_level"]
    rpm = fan_state["rpm"]
    mode = fan_state["mode"]
    desc = fan_state["description"]

    fan_id = f"fan_{int(time.time() * 1000) % 100000}_{random.randint(100, 999)}"

    if discrete == 0 or speed_level <= 0.05:
        # SPEED 0: NO ROTATE AT 0 (Stationary)
        spin_sec = 0.0
        anim_tag = ""
        rotor_css = "animation: none !important; transform: rotate(0deg);"
        fan_status_text = "🛑 FAN STOPPED (0 RPM)"
        fan_status_color = "#ff4d4d"
        blade_col1 = "#5c1b1b"
        blade_col2 = "#782222"
        housing_color = "#ff4d4d"
        glow_shadow = "0 0 12px rgba(255, 77, 77, 0.45)"
        vortex_elements = ""
        motor_label = "MOTOR IDLE • 0 RPM"
    elif discrete == 1:
        spin_sec = 3.60
        rotor_css = f"animation: spinFan_{fan_id} {spin_sec:.2f}s linear infinite;"
        anim_tag = f'<animateTransform attributeName="transform" type="rotate" from="0 60 60" to="360 60 60" dur="{spin_sec:.2f}s" repeatCount="indefinite" />'
        fan_status_text = "💤 WHISPER • SPEED 1 / 5"
        fan_status_color = "#a78bfa"
        blade_col1 = "#a78bfa"
        blade_col2 = "#7c3aed"
        housing_color = "#a78bfa"
        glow_shadow = "0 0 14px rgba(167, 139, 250, 0.5)"
        vortex_elements = ""
        motor_label = "WHISPER • 450 RPM"
    elif discrete == 2:
        # SPEED 2: SMALL SPEED ROTATE (Calm & Gentle)
        spin_sec = 2.20
        rotor_css = f"animation: spinFan_{fan_id} {spin_sec:.2f}s linear infinite;"
        anim_tag = f'<animateTransform attributeName="transform" type="rotate" from="0 60 60" to="360 60 60" dur="{spin_sec:.2f}s" repeatCount="indefinite" />'
        fan_status_text = "🍃 GENTLE BREEZE • SPEED 2 / 5"
        fan_status_color = "#38bdf8"
        blade_col1 = "#38bdf8"
        blade_col2 = "#0284c7"
        housing_color = "#38bdf8"
        glow_shadow = "0 0 18px rgba(56, 189, 248, 0.6)"
        vortex_elements = ""
        motor_label = "GENTLE • 850 RPM"
    elif discrete == 3:
        spin_sec = 1.00
        rotor_css = f"animation: spinFan_{fan_id} {spin_sec:.2f}s linear infinite;"
        anim_tag = f'<animateTransform attributeName="transform" type="rotate" from="0 60 60" to="360 60 60" dur="{spin_sec:.2f}s" repeatCount="indefinite" />'
        fan_status_text = "⚖️ BALANCED • SPEED 3 / 5"
        fan_status_color = "#2dd4bf"
        blade_col1 = "#2dd4bf"
        blade_col2 = "#0d9488"
        housing_color = "#2dd4bf"
        glow_shadow = "0 0 20px rgba(45, 212, 191, 0.6)"
        vortex_elements = ""
        motor_label = "BALANCED • 1,350 RPM"
    elif discrete == 4:
        spin_sec = 0.30
        rotor_css = f"animation: spinFan_{fan_id} {spin_sec:.2f}s linear infinite;"
        anim_tag = f'<animateTransform attributeName="transform" type="rotate" from="0 60 60" to="360 60 60" dur="{spin_sec:.2f}s" repeatCount="indefinite" />'
        fan_status_text = "💨 HIGH BREEZE • SPEED 4 / 5"
        fan_status_color = "#facc15"
        blade_col1 = "#facc15"
        blade_col2 = "#d97706"
        housing_color = "#facc15"
        glow_shadow = "0 0 22px rgba(250, 204, 21, 0.7)"
        vortex_elements = ""
        motor_label = "HIGH BREEZE • 1,850 RPM"
    else:
        # SPEED 5: ROTATES HEAVILY (Ultra Turbo Spin with Swirling Vortex)
        spin_sec = 0.06
        rotor_css = f"animation: spinFan_{fan_id} {spin_sec:.2f}s linear infinite;"
        anim_tag = f'<animateTransform attributeName="transform" type="rotate" from="0 60 60" to="360 60 60" dur="{spin_sec:.2f}s" repeatCount="indefinite" />'
        fan_status_text = "⚡ HEAVY TURBO • SPEED 5 / 5"
        fan_status_color = "#00ffb2"
        blade_col1 = "#00ffb2"
        blade_col2 = "#22c55e"
        housing_color = "#00ffb2"
        glow_shadow = "0 0 28px rgba(0, 255, 178, 0.95)"
        vortex_elements = """
        <circle cx="60" cy="60" r="53" fill="none" stroke="#00ffb2" stroke-width="2.4" stroke-dasharray="10 14" opacity="0.95">
            <animateTransform attributeName="transform" type="rotate" from="0 60 60" to="360 60 60" dur="0.08s" repeatCount="indefinite" />
        </circle>
        <circle cx="60" cy="60" r="46" fill="none" stroke="#22c55e" stroke-width="1.8" stroke-dasharray="12 18" opacity="0.85">
            <animateTransform attributeName="transform" type="rotate" from="360 60 60" to="0 60 60" dur="0.12s" repeatCount="indefinite" />
        </circle>
        """
        motor_label = "TURBO • 2,400 RPM (HEAVY)"

    scan_badge = ""
    if countdown_sec is not None:
        scan_badge = f'<span style="background: rgba(56, 189, 248, 0.22); color: #38bdf8; border: 1.5px solid #38bdf8; padding: 3px 11px; border-radius: 12px; font-size: 0.90rem; font-weight: 800; margin-left: 10px;">⏱️ Scan: {countdown_sec:.1f}s</span>'

    # Clear, Comfortable Segmented 0 1 2 3 4 5 Blocks with Sub-Labels
    level_names = {0: "OFF", 1: "WHISPER", 2: "GENTLE", 3: "NORMAL", 4: "BREEZE", 5: "TURBO"}
    level_theme_colors = {0: "#ff4d4d", 1: "#a78bfa", 2: "#38bdf8", 3: "#2dd4bf", 4: "#facc15", 5: "#00ffb2"}

    blocks_html = ""
    for lvl in range(6):
        is_active = (lvl == discrete)
        is_filled = (lvl <= discrete and discrete > 0)
        col_theme = level_theme_colors[lvl]

        if is_active:
            bg = col_theme
            text_num = "#060911"
            text_sub = "#060911"
            border = f"2.5px solid #ffffff"
            box_shadow = f"0 0 20px {col_theme}"
            scale = "transform: scale(1.06);"
        elif is_filled:
            bg = f"rgba(0, 255, 178, 0.22)"
            text_num = "#00ffb2"
            text_sub = "#ffffff"
            border = f"1.5px solid {col_theme}99"
            box_shadow = "none"
            scale = ""
        else:
            bg = "rgba(22, 32, 50, 0.85)"
            text_num = "#e2e8f0"
            text_sub = "#94a3b8"
            border = "1.5px solid rgba(255, 255, 255, 0.12)"
            box_shadow = "none"
            scale = ""

        blocks_html += f'''
        <div style="flex: 1; text-align: center; background: {bg}; border: {border}; border-radius: 10px; padding: 8px 3px; box-shadow: {box_shadow}; {scale} transition: all 0.2s ease;">
            <div style="font-size: 1.55rem; font-weight: 900; color: {text_num}; line-height: 1;">{lvl}</div>
            <div style="font-size: 0.78rem; font-weight: 800; color: {text_sub}; text-transform: uppercase; margin-top: 3px;">{level_names[lvl]}</div>
        </div>
        '''

    return f"""
<div class="pro-card pro-card-glow">
    <!-- Header -->
    <div style="display: flex; align-items: center; justify-content: space-between; border-bottom: 1.5px solid rgba(255,255,255,0.12); padding-bottom: 8px; margin-bottom: 12px;">
        <div style="display: flex; align-items: center;">
            <span style="font-size: 1.35rem; font-weight: 900; color: #00ffb2; letter-spacing: 0.4px;">💨 SMART CLIMATE FAN</span>
            {scan_badge}
        </div>
        <div style="font-size: 1.02rem; font-weight: 900; color: {fan_status_color}; background: rgba(0,0,0,0.55); padding: 5px 14px; border-radius: 12px; border: 1.5px solid {fan_status_color};">
            {fan_status_text}
        </div>
    </div>

    <!-- Fan SVG + Tachometer & Blocks Row -->
    <div style="display: flex; align-items: center; gap: 20px;">
        <!-- Left: Animated SVG Fan -->
        <div style="flex-shrink: 0; text-align: center; width: 120px;">
            <div style="position: relative; width: 120px; height: 120px; margin: 0 auto; filter: drop-shadow({glow_shadow});">
                <svg viewBox="0 0 120 120" width="120" height="120">
                    <defs>
                        <style>
                            @keyframes spinFan_{fan_id} {{
                                0% {{ transform: rotate(0deg); }}
                                100% {{ transform: rotate(360deg); }}
                            }}
                            .rotor-box-{fan_id} {{
                                transform-origin: 60px 60px;
                                transform-box: view-box;
                                {rotor_css}
                            }}
                        </style>
                        <linearGradient id="bladeGrad_{fan_id}" x1="0%" y1="0%" x2="100%" y2="100%">
                            <stop offset="0%" stop-color="{blade_col1}"/>
                            <stop offset="100%" stop-color="{blade_col2}"/>
                        </linearGradient>
                    </defs>
                    <circle cx="60" cy="60" r="56" fill="#080e1a" stroke="{housing_color}" stroke-width="2.8"/>
                    <circle cx="60" cy="60" r="51" fill="none" stroke="{housing_color}" stroke-width="1.2" stroke-dasharray="4 3" opacity="0.6"/>
                    <line x1="60" y1="8" x2="60" y2="112" stroke="{housing_color}" stroke-width="1.2" opacity="0.4"/>
                    <line x1="8" y1="60" x2="112" y2="60" stroke="{housing_color}" stroke-width="1.2" opacity="0.4"/>
                    {vortex_elements}
                    <g class="rotor-box-{fan_id}" transform-origin="60 60" style="transform-origin: 60px 60px; transform-box: view-box; {rotor_css}">
                        {anim_tag}
                        <path d="M 60 60 C 50 38, 38 18, 60 8 C 82 18, 70 38, 60 60 Z" fill="url(#bladeGrad_{fan_id})" stroke="{housing_color}" stroke-width="0.8"/>
                        <path d="M 60 60 C 82 50, 102 38, 112 60 C 102 82, 82 70, 60 60 Z" fill="url(#bladeGrad_{fan_id})" stroke="{housing_color}" stroke-width="0.8"/>
                        <path d="M 60 60 C 70 82, 82 102, 60 112 C 38 102, 50 82, 60 60 Z" fill="url(#bladeGrad_{fan_id})" stroke="{housing_color}" stroke-width="0.8"/>
                        <path d="M 60 60 C 38 70, 18 82, 8 60 C 18 38, 38 50, 60 60 Z" fill="url(#bladeGrad_{fan_id})" stroke="{housing_color}" stroke-width="0.8"/>
                        <circle cx="60" cy="60" r="14" fill="#131c2d" stroke="{housing_color}" stroke-width="2.6"/>
                        <circle cx="60" cy="60" r="5" fill="{housing_color}"/>
                    </g>
                </svg>
            </div>
            <div style="font-size: 0.88rem; color: #ffffff; margin-top: 5px; font-weight: 800;">
                {motor_label}
            </div>
        </div>

        <!-- Right: Digital Tachometer & 0-5 Level Indicators -->
        <div style="flex-grow: 1;">
            <div style="display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 8px;">
                <div>
                    <div style="font-size: 0.90rem; color: #e2e8f0; text-transform: uppercase; font-weight: 800; letter-spacing: 0.5px;">Motor Tachometer</div>
                    <div style="font-size: 2.7rem; font-weight: 900; color: #00ffb2; line-height: 1.0;">
                        ⚡ {rpm:,} <span style="font-size: 1.3rem; color: #ffffff; font-weight: 800;">RPM</span>
                    </div>
                </div>
                <div style="text-align: right;">
                    <div style="font-size: 0.90rem; color: #e2e8f0; text-transform: uppercase; font-weight: 800; letter-spacing: 0.5px;">Airflow Mode</div>
                    <div style="font-size: 1.25rem; font-weight: 900; color: #ffffff;">
                        {mode}
                    </div>
                </div>
            </div>

            <!-- Segmented Speed Level 0-5 Blocks -->
            <div style="margin-bottom: 6px; display: flex; justify-content: space-between; font-size: 0.98rem; color: #ffffff; font-weight: 800;">
                <span>SPEED LEVEL: <b style="color: #00ffb2; font-size: 1.15rem;">Level {speed_level:.1f} / 5</b></span>
                <span style="color: #38bdf8; font-size: 1.02rem;">Target: Speed {target}</span>
            </div>
            <div style="display: flex; gap: 8px;">
                {blocks_html}
            </div>
            <div style="font-size: 0.90rem; color: #cbd5e1; margin-top: 7px; font-weight: 600;">
                ℹ️ {desc} <b style="color: #00ffb2;">(Slow, gradual inertia transitions)</b>
            </div>
        </div>
    </div>
</div>
"""


# ==============================================================================
# CARD 2: COMFORTABLE BIOMETRIC EMOTION RECOGNITION CARD
# ==============================================================================
def render_emotion_card_html(dominant, confidence, is_smiling, suggestion):
    """Renders the large, comfortable, high-contrast Biometric Emotion & Mental Wellbeing Card."""
    colors = {
        "happy": "#00ffb2", "sad": "#38bdf8", "angry": "#ff4d4d",
        "surprise": "#facc15", "fear": "#a78bfa", "disgust": "#34d399", "neutral": "#e2e8f0"
    }
    col = colors.get(dominant.lower(), "#00ffb2")
    smile_badge = '<span style="background: rgba(0, 255, 178, 0.22); color: #00ffb2; border: 1.5px solid #00ffb2; padding: 4px 12px; border-radius: 10px; font-size: 0.98rem; font-weight: 900; margin-left: 12px;">😊 SMILE VERIFIED</span>' if is_smiling else ''

    fan_target_desc = "Speed 5 (Heavy Turbo)" if dominant.lower() == "happy" else ("Speed 0 (Fan Stopped)" if dominant.lower() == "angry" else "Speed 2 (Gentle Draft)")

    return f"""
<div class="pro-card">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
        <span style="font-size: 1.05rem; font-weight: 800; color: #e2e8f0; text-transform: uppercase; letter-spacing: 0.5px;">BIOMETRIC EMOTION RECOGNITION</span>
        <span style="font-size: 0.88rem; font-weight: 800; color: #38bdf8; background: rgba(56, 189, 248, 0.18); padding: 3px 12px; border-radius: 8px;">🎯 Target: Single Human Face</span>
    </div>
    <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; margin-bottom: 10px;">
        <div style="display: flex; align-items: center;">
            <span style="font-size: 2.8rem; font-weight: 900; color: {col}; letter-spacing: 0.5px; line-height: 1.0;">
                {dominant.upper()}
            </span>
            <span style="font-size: 1.6rem; font-weight: 900; color: #ffffff; margin-left: 12px;">
                {confidence:.1f}%
            </span>
            {smile_badge}
        </div>
        <div style="font-size: 1.02rem; font-weight: 800; color: #ffffff;">
            Climate Target: <b style="color: {col}; font-size: 1.15rem;">{fan_target_desc}</b>
        </div>
    </div>
    <!-- Wellbeing Suggestion Box -->
    <div style="padding: 10px 16px; background: rgba(255,255,255,0.06); border-radius: 10px; border-left: 4.5px solid {col}; font-size: 0.98rem; color: #ffffff; font-weight: 600; line-height: 1.4;">
        <b style="color: {col}; font-size: 1.05rem;">{suggestion.get('icon', '💡')} {suggestion.get('title', 'Wellness')}:</b> {suggestion.get('advice', '')}
    </div>
</div>
"""


# ==============================================================================
# CARD 3: COMFORTABLE 7-EMOTION SPECTRUM & TELEMETRY CARD
# ==============================================================================
def render_spectrum_card_html(emotions_dict, telemetry_counts):
    """Renders 7-Emotion Horizontal Progress Bars with generous spacing & clean layout."""
    all_emos = [
        ("Happy", "#00ffb2"), ("Neutral", "#e2e8f0"), ("Surprise", "#facc15"),
        ("Sad", "#38bdf8"), ("Fear", "#a78bfa"), ("Disgust", "#34d399"), ("Angry", "#ff4d4d")
    ]
    scores = emotions_dict or {"neutral": 85.0, "happy": 10.0, "surprise": 2.0, "sad": 1.0, "fear": 1.0, "disgust": 0.5, "angry": 0.5}

    bars_html = ""
    for name, col in all_emos:
        pct = float(scores.get(name.lower(), 0.0))
        bars_html += f"""
        <div style="display: flex; align-items: center; margin-bottom: 5px; font-size: 0.95rem;">
            <span style="width: 78px; color: #ffffff; font-weight: 800;">{name}</span>
            <div style="flex-grow: 1; height: 10px; background: rgba(255,255,255,0.14); border-radius: 5px; overflow: hidden; margin: 0 10px;">
                <div style="width: {min(100.0, max(0.0, pct))}%; height: 100%; background: {col}; border-radius: 5px;"></div>
            </div>
            <span style="width: 52px; text-align: right; color: {col}; font-weight: 900;">{pct:.1f}%</span>
        </div>
        """

    total_scans = sum(telemetry_counts.values())

    return f"""
<div class="pro-card">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
        <span style="font-size: 1.05rem; font-weight: 800; color: #e2e8f0; text-transform: uppercase; letter-spacing: 0.5px;">7-EMOTION SPECTRUM & TELEMETRY</span>
        <span style="font-size: 0.88rem; color: #00ffb2; font-weight: 900; background: rgba(0, 255, 178, 0.16); padding: 3px 12px; border-radius: 8px;">🔒 100% ANONYMOUS</span>
    </div>
    <div style="display: grid; grid-template-columns: 1.4fr 1fr; gap: 18px; align-items: center;">
        <div>
            {bars_html}
        </div>
        <div style="background: rgba(10, 16, 26, 0.88); border: 1.5px solid rgba(255,255,255,0.12); border-radius: 12px; padding: 14px; text-align: center;">
            <div style="font-size: 0.88rem; color: #cbd5e1; font-weight: 800; text-transform: uppercase;">Total Detections</div>
            <div style="font-size: 2.6rem; font-weight: 900; color: #00ffb2; line-height: 1.1;">{total_scans}</div>
            <div style="font-size: 0.90rem; color: #e2e8f0; font-weight: 700; margin-top: 6px;">
                Single Face Lock: <b style="color: #00ffb2;">ACTIVE</b>
            </div>
            <div style="font-size: 0.90rem; color: #e2e8f0; font-weight: 700; margin-top: 4px;">
                Scan Cycle: <b style="color: #38bdf8;">5.0 SECONDS</b>
            </div>
        </div>
    </div>
</div>
"""


# ==============================================================================
# TOP HEADER BAR (COMPACT, HIGH-CONTRAST, SPACIOUS)
# ==============================================================================
col_head1, col_head2, col_head3 = st.columns([1.6, 2.0, 1.4], gap="medium")

with col_head1:
    st.html(
        """
        <div style="display: flex; align-items: center; gap: 12px;">
            <span style="font-size: 2.1rem;">🧠</span>
            <div>
                <div style="font-size: 1.6rem; font-weight: 900; color: #00ffb2; line-height: 1.0; letter-spacing: -0.5px;">FACESENSE AI</div>
                <div style="font-size: 0.85rem; font-weight: 800; color: #e2e8f0; letter-spacing: 0.7px; margin-top: 2px;">REAL-TIME SMART CLIMATE & FACIAL BIOMETRICS</div>
            </div>
        </div>
        """
    )

with col_head2:
    st.html(
        """
        <div style="display: flex; align-items: center; justify-content: center; gap: 12px; margin-top: 6px; font-size: 0.92rem; font-weight: 800;">
            <span style="background: rgba(0, 255, 178, 0.2); color: #00ffb2; padding: 5px 14px; border-radius: 12px; border: 1.5px solid #00ffb2;">🟢 AI CORE ACTIVE</span>
            <span style="background: rgba(56, 189, 248, 0.2); color: #38bdf8; padding: 5px 14px; border-radius: 12px; border: 1.5px solid #38bdf8;">🎯 1 HUMAN FACE LOCK</span>
            <span style="background: rgba(167, 139, 250, 0.2); color: #a78bfa; padding: 5px 14px; border-radius: 12px; border: 1.5px solid #a78bfa;">⏱️ 5.0s SCAN CYCLE</span>
        </div>
        """
    )

with col_head3:
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        st.session_state.privacy_blur = st.checkbox("🛡️ Blur Face", value=st.session_state.privacy_blur, help="Applies privacy blur on face")
    with col_t2:
        st.session_state.manual_override = st.checkbox("💨 Fan Override", value=st.session_state.manual_override, help="Manual fan override")


# ==============================================================================
# MAIN 2-COLUMN BALANCED DASHBOARD (LARGE CAMERA + COMFORTABLE HUB)
# ==============================================================================
left_col, right_col = st.columns([1.30, 1.15], gap="large")

# ------------------------------------------------------------------------------
# LEFT COLUMN: LARGE IMMERSIVE CAMERA VIEWPORT & DOCKED TOOLBAR
# ------------------------------------------------------------------------------
with left_col:
    # Camera Display Frame Placeholder
    frame_placeholder = st.empty()

    # Docked Action Toolbar
    col_btn1, col_btn2, col_btn3, col_btn4 = st.columns([1.3, 1.1, 1.3, 1.3])

    with col_btn1:
        start_btn = st.button("▶️ Start Camera", type="primary", width="stretch")
    with col_btn2:
        stop_btn = st.button("⏹️ Stop Feed", width="stretch")
    with col_btn3:
        snapshot_btn = st.button("📸 Snapshot", width="stretch")
    with col_btn4:
        sample_btn = st.button("🖼️ Load Demo", width="stretch")

    # Sub-status badge underneath toolbar
    status_placeholder = st.empty()

    if start_btn:
        st.session_state.live_streaming = True
    if stop_btn:
        st.session_state.live_streaming = False
        frame_placeholder.empty()

# ------------------------------------------------------------------------------
# RIGHT COLUMN: DOCKED INTELLIGENCE & CLIMATE HUB
# ------------------------------------------------------------------------------
with right_col:
    # Manual Slider if Override Enabled
    if st.session_state.manual_override:
        fan_controller.manual_override = True
        st.session_state.manual_speed = st.slider("Manual Fan Speed Setting (0 to 5)", 0, 5, st.session_state.manual_speed)
        fan_controller.manual_level = st.session_state.manual_speed
    else:
        fan_controller.manual_override = False

    # Intelligence & Fan Placeholders
    fan_placeholder = st.empty()
    emotion_placeholder = st.empty()
    spectrum_placeholder = st.empty()

    # Render initial state on page load
    init_state = fan_controller.get_current_state()
    sugg = get_suggestion(st.session_state.latest_emotion)

    with fan_placeholder.container():
        st.html(render_fan_widget_html(init_state, countdown_sec=5.0))

    with emotion_placeholder.container():
        st.html(render_emotion_card_html(st.session_state.latest_emotion, st.session_state.latest_confidence, False, sugg))

    with spectrum_placeholder.container():
        st.html(render_spectrum_card_html(None, st.session_state.emotion_counts))


# Initial camera frame placeholder when not streaming
if not st.session_state.live_streaming:
    with status_placeholder.container():
        st.html(
            """
            <div style="display: flex; justify-content: space-between; font-size: 0.95rem; color: #ffffff; padding: 7px 14px; background: rgba(16, 25, 42, 0.9); border-radius: 10px; margin-top: 6px; border: 1.5px solid rgba(255,255,255,0.14);">
                <span>STATUS: <b style="color: #38bdf8;">STANDBY (Click 'Start Camera' or 'Load Demo')</b></span>
                <span>TARGET: <b style="color: #00ffb2;">Strict Single Human Face Lock</b></span>
            </div>
            """
        )

    # If user clicked Load Demo Sample
    if sample_btn:
        sample_path = os.path.join(os.path.dirname(__file__), "assets", "samples", "happy_portrait.jpg")
        if os.path.exists(sample_path):
            sample_img = cv2.imread(sample_path)
            res = detector.analyze_frame_sync(sample_img)
            if res:
                primary = res[0]
                dom = primary.get("dominant_emotion", "happy")
                conf = primary.get("confidence", 99.8)
                is_smile = primary.get("is_smiling", True)

                fan_controller.set_target_emotion(dom)
                fan_s = fan_controller.update_smooth(step_rate=1.0)
                log_emotion(dom, conf)

                annotated = sample_img.copy()
                visualizer.draw_face_result(annotated, primary)
                visualizer.draw_fan_speed_bar(annotated, fan_s, countdown_sec=0.0, x=15, y=15)

                rgb = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)
                frame_placeholder.image(rgb, channels="RGB", width="stretch")

                with fan_placeholder.container():
                    st.html(render_fan_widget_html(fan_s))
                with emotion_placeholder.container():
                    st.html(render_emotion_card_html(dom, conf, is_smile, get_suggestion(dom)))
                with spectrum_placeholder.container():
                    st.html(render_spectrum_card_html(primary.get("emotion"), st.session_state.emotion_counts))

    elif not sample_btn:
        # Large, Grand High-Tech Camera Viewport (460px height)
        frame_placeholder.html(
            """
            <div style="height: 460px; background: rgba(10, 16, 28, 0.95); border: 2.5px dashed rgba(0, 255, 178, 0.5); border-radius: 14px; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; color: #ffffff; padding: 24px;">
                <div style="font-size: 4.2rem; margin-bottom: 12px; filter: drop-shadow(0 0 16px rgba(0,255,178,0.4));">📹</div>
                <div style="font-size: 1.7rem; font-weight: 900; color: #00ffb2; letter-spacing: 0.5px;">CAMERA FEED READY</div>
                <div style="font-size: 1.05rem; color: #e2e8f0; max-width: 440px; margin-top: 10px; line-height: 1.45; font-weight: 600;">
                    Click <b style="color: #00ffb2; font-size: 1.15rem;">▶️ Start Camera</b> below to begin real-time single human face tracing & automated smart climate control.
                </div>
                <div style="margin-top: 20px; display: flex; gap: 10px; flex-wrap: wrap; justify-content: center;">
                    <span style="font-size: 0.90rem; font-weight: 800; color: #00ffb2; background: rgba(0, 255, 178, 0.18); padding: 6px 14px; border-radius: 10px; border: 1.5px solid #00ffb2;">
                        🎯 Single Human Face Lock
                    </span>
                    <span style="font-size: 0.90rem; font-weight: 800; color: #38bdf8; background: rgba(56, 189, 248, 0.18); padding: 6px 14px; border-radius: 10px; border: 1.5px solid #38bdf8;">
                        🚫 Non-Human Objects Filtered
                    </span>
                    <span style="font-size: 0.90rem; font-weight: 800; color: #a78bfa; background: rgba(167, 139, 250, 0.18); padding: 6px 14px; border-radius: 10px; border: 1.5px solid #a78bfa;">
                        ⚡ 30 FPS Smooth Tracing
                    </span>
                </div>
            </div>
            """
        )


# ==============================================================================
# LIVE STREAMING LOOP (STRICT SINGLE-FACE TRACING & DECOUPLED 5S EMOTION SCAN)
# ==============================================================================
if st.session_state.live_streaming:
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        st.error("❌ Could not access webcam index 0. Please verify camera permissions.")
        st.session_state.live_streaming = False
    else:
        SCAN_INTERVAL = 5.0
        last_scan_time = 0.0
        current_face_result = None
        dom_emo = "neutral"
        dom_conf = 85.0
        is_smiling = False

        try:
            while st.session_state.live_streaming:
                ret, frame = cap.read()
                if not ret:
                    st.warning("Frame capture ended.")
                    break

                frame = cv2.flip(frame, 1)
                now = time.time()
                time_since_scan = now - last_scan_time
                countdown_sec = max(0.0, SCAN_INTERVAL - time_since_scan)

                # 1. FAST CONTINUOUS HUMAN FACE TRACING (Runs at 30 FPS on every frame)
                # Strictly locates ONE primary human face; ignores all background objects
                tracked_face_box = detector.trace_single_face(frame)

                # 2. DECOUPLED 5-SECOND EMOTION CLASSIFICATION
                if time_since_scan >= SCAN_INTERVAL or current_face_result is None:
                    if tracked_face_box is not None:
                        res = detector.analyze_frame_sync(frame)
                        if res:
                            current_face_result = res[0]
                            dom_emo = current_face_result.get("dominant_emotion", "neutral")
                            dom_conf = current_face_result.get("confidence", 85.0)
                            is_smiling = current_face_result.get("is_smiling", False)

                            fan_controller.set_target_emotion(dom_emo)
                            log_emotion(dom_emo, dom_conf)
                    last_scan_time = now

                # 3. GRADUAL SMOOTH FAN SPEED STEP ("slowly slowly change")
                current_fan_state = fan_controller.update_smooth(step_rate=0.035)

                # 4. DRAW STREAM HUD
                annotated = frame.copy()
                if tracked_face_box is not None:
                    display_res = {
                        "region": tracked_face_box,
                        "dominant_emotion": dom_emo,
                        "confidence": dom_conf,
                        "is_smiling": is_smiling,
                    }
                    if st.session_state.privacy_blur:
                        annotated = PrivacyBlurEngine.blur_face(annotated, tracked_face_box)
                    else:
                        visualizer.draw_face_result(annotated, display_res)

                # Overlay animated fan HUD on corner of video frame
                visualizer.draw_fan_speed_bar(annotated, current_fan_state, countdown_sec=countdown_sec, x=15, y=15)

                rgb_frame = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)
                frame_placeholder.image(rgb_frame, channels="RGB", width="stretch")

                # Update Status Bar Underneath Video
                with status_placeholder.container():
                    lock_status = f'<b style="color: #00ffb2;">LOCKED (1 Human Face)</b>' if tracked_face_box else '<b style="color: #facc15;">SEARCHING (Human Face Only)...</b>'
                    st.html(
                        f"""
                        <div style="display: flex; justify-content: space-between; font-size: 0.95rem; color: #ffffff; padding: 7px 14px; background: rgba(16, 25, 42, 0.9); border-radius: 10px; margin-top: 6px; border: 1.5px solid rgba(255,255,255,0.14);">
                            <span>TARGET: {lock_status}</span>
                            <span>NEXT AI SCAN: <b style="color: #38bdf8;">{countdown_sec:.1f}s</b></span>
                        </div>
                        """
                    )

                # Update Right Command Panel
                with fan_placeholder.container():
                    st.html(render_fan_widget_html(current_fan_state, countdown_sec=countdown_sec))

                with emotion_placeholder.container():
                    sugg = get_suggestion(dom_emo)
                    st.html(render_emotion_card_html(dom_emo, dom_conf, is_smiling, sugg))

                with spectrum_placeholder.container():
                    emotions_scores = current_face_result.get("emotion") if current_face_result else None
                    st.html(render_spectrum_card_html(emotions_scores, st.session_state.emotion_counts))

                time.sleep(0.015)

        finally:
            cap.release()

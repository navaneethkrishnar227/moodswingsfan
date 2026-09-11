"""
Wellbeing & Mindfulness Suggestions for FaceSense.
Provides evidence-based wellness tips, grounding exercises, and mindfulness prompts
tailored to detected emotional states.
"""

WELLBEING_DATA = {
    "happy": {
        "title": "Positive Resonance",
        "icon": "✨",
        "advice": "You're radiating positive energy! This is a great moment to anchor your mood.",
        "exercise": "Gratitude Anchor: Think of three specific things or people that made this moment possible.",
        "action": "Share a kind word or compliment with someone around you.",
        "color": (46, 204, 113),  # Emerald Green
    },
    "sad": {
        "title": "Gentle Comfort & Compassion",
        "icon": "💙",
        "advice": "Honor your feelings—sadness is a natural emotional response. Be kind to yourself.",
        "exercise": "Self-Compassion Pause: Place a hand over your heart, take three slow breaths, and release tension.",
        "action": "Step away from screens for 5 minutes, drink a glass of water, or listen to soothing music.",
        "color": (52, 152, 219),  # Calming Blue
    },
    "angry": {
        "title": "De-escalation & Release",
        "icon": "🌿",
        "advice": "Notice any physical tightness in your jaw, fists, or shoulders. Allow them to loosen.",
        "exercise": "Box Breathing: Inhale slowly for 4s, hold for 4s, exhale for 4s, hold empty for 4s. Repeat 3 times.",
        "action": "Step back from the immediate trigger. A 2-minute walk can reset adrenaline levels.",
        "color": (231, 76, 60),  # Red
    },
    "fear": {
        "title": "Grounding & Safety",
        "icon": "🛡️",
        "advice": "You are safe right now in this present moment. Let's anchor your nervous system.",
        "exercise": "5-4-3-2-1 Grounding: Identify 5 things you see, 4 you can touch, 3 you hear, 2 you smell, 1 you taste.",
        "action": "Feel both feet flat on the floor and gently lengthen your spine.",
        "color": (155, 89, 182),  # Purple
    },
    "surprise": {
        "title": "Curiosity & Integration",
        "icon": "⚡",
        "advice": "Sudden inputs trigger alert states. Give your mind a moment to process the novelty.",
        "exercise": "Centering Breath: Take a deep inhalation through your nose, then a slow sigh out through your mouth.",
        "action": "Ask yourself: 'Is this information urgent, or can I reflect on it calmly?'",
        "color": (241, 196, 15),  # Amber Yellow
    },
    "disgust": {
        "title": "Reset & Refresh",
        "icon": "🍃",
        "advice": "Disgust is a protective boundary emotion. Give yourself space to reset.",
        "exercise": "Visual Reset: Look out a window at distant natural greenery or sky for 30 seconds.",
        "action": "Wash your hands with cool water or open a window for fresh circulating air.",
        "color": (39, 174, 96),  # Green
    },
    "neutral": {
        "title": "Centered & Balanced",
        "icon": "🎯",
        "advice": "A calm, neutral state is prime ground for focus, creativity, and steady progress.",
        "exercise": "Posture Check: Drop your shoulders down from your ears, align your head, and breathe naturally.",
        "action": "Set a clear micro-goal for the next 25 minutes of productive focus.",
        "color": (149, 165, 166),  # Silver Gray
    },
}


def get_suggestion(emotion):
    """Returns the wellbeing advice dictionary for a given emotion."""
    emotion = emotion.lower().strip()
    return WELLBEING_DATA.get(emotion, WELLBEING_DATA["neutral"])


def get_all_emotions():
    return list(WELLBEING_DATA.keys())

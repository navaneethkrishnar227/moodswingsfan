"""
Sound Engine for FaceSense.
Generates and plays mood-adaptive ambient music/harmonic soundscapes based on detected facial emotion.
Works 100% offline with zero external audio assets required.
"""

import os
import math
import struct
import wave
import threading
import base64

# Try importing pygame for desktop playback
try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False


class MoodSoundEngine:
    """Manages procedural generation and playback of mood-adaptive music/tones."""

    def __init__(self, audio_dir=None):
        if audio_dir is None:
            audio_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "audio")
        self.audio_dir = audio_dir
        os.makedirs(self.audio_dir, exist_ok=True)

        self.current_emotion = None
        self.is_enabled = True
        self.volume = 0.6
        self.lock = threading.Lock()
        self._pygame_initialized = False

        self._ensure_sound_tracks()
        self._init_mixer()

    def _init_mixer(self):
        if PYGAME_AVAILABLE and not self._pygame_initialized:
            try:
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)
                pygame.mixer.set_num_channels(8)
                self._pygame_initialized = True
            except Exception as e:
                print(f"[SoundEngine] Pygame mixer init warning: {e}")

    def _ensure_sound_tracks(self):
        """Generates pleasant harmonic ambient WAV tracks for each emotion if missing."""
        tracks = {
            "happy": self._create_happy_chime,
            "sad": self._create_sad_ambient,
            "neutral": self._create_neutral_drone,
            "angry": self._create_calming_chord,
            "fear": self._create_grounding_tone,
            "surprise": self._create_surprise_bell,
            "disgust": self._create_soothing_wave,
        }

        for emotion, gen_fn in tracks.items():
            file_path = os.path.join(self.audio_dir, f"{emotion}.wav")
            if not os.path.exists(file_path):
                try:
                    gen_fn(file_path)
                except Exception as e:
                    print(f"[SoundEngine] Error generating {emotion}.wav: {e}")

    def _write_wav(self, file_path, samples, sample_rate=44100):
        """Helper to write raw PCM samples to 16-bit stereo WAV."""
        with wave.open(file_path, "w") as wav_file:
            wav_file.setnchannels(2)  # Stereo
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)

            raw_bytes = bytearray()
            for left, right in samples:
                # Clamp to 16-bit signed integer range
                l_val = max(-32767, min(32767, int(left * 32767)))
                r_val = max(-32767, min(32767, int(right * 32767)))
                raw_bytes.extend(struct.pack("<hh", l_val, r_val))
            wav_file.writeframes(raw_bytes)

    def _create_happy_chime(self, file_path, duration_sec=3.5, sample_rate=44100):
        """Joyful, bright, uplifting major pentatonic arpeggio (C5, E5, G5, A5, C6)."""
        num_samples = int(duration_sec * sample_rate)
        notes = [523.25, 659.25, 783.99, 880.00, 1046.50]  # C5, E5, G5, A5, C6
        note_dur = duration_sec / len(notes)
        samples = []

        for i in range(num_samples):
            t = i / sample_rate
            note_idx = min(int(t / note_dur), len(notes) - 1)
            freq = notes[note_idx]
            local_t = t - (note_idx * note_dur)
            # Envelope: fast attack, gentle decay
            decay = math.exp(-local_t * 3.5)
            # Add harmonic overtones
            wave_val = (
                0.6 * math.sin(2 * math.pi * freq * t)
                + 0.3 * math.sin(2 * math.pi * freq * 2 * t)
                + 0.1 * math.sin(2 * math.pi * freq * 3 * t)
            ) * decay * 0.4
            # Gentle panning
            pan = math.sin(2 * math.pi * 0.5 * t) * 0.3
            samples.append((wave_val * (0.5 - pan), wave_val * (0.5 + pan)))

        self._write_wav(file_path, samples, sample_rate)

    def _create_sad_ambient(self, file_path, duration_sec=4.0, sample_rate=44100):
        """Warm, melancholic, comforting minor chord with slow swell (A3, C4, E4)."""
        num_samples = int(duration_sec * sample_rate)
        freqs = [220.00, 261.63, 329.63]
        samples = []

        for i in range(num_samples):
            t = i / sample_rate
            # Smooth attack and decay envelope
            env = math.sin(math.pi * (t / duration_sec)) ** 1.5
            wave_val = sum(math.sin(2 * math.pi * f * t) for f in freqs) / len(freqs)
            # Add warm sub-harmonic
            sub = 0.4 * math.sin(2 * math.pi * 110.0 * t)
            combined = (wave_val * 0.7 + sub * 0.3) * env * 0.35
            samples.append((combined, combined))

        self._write_wav(file_path, samples, sample_rate)

    def _create_neutral_drone(self, file_path, duration_sec=4.0, sample_rate=44100):
        """Gentle, focused, ambient meditation tone (D3 + A3)."""
        num_samples = int(duration_sec * sample_rate)
        freqs = [146.83, 220.00, 293.66]
        samples = []

        for i in range(num_samples):
            t = i / sample_rate
            env = math.sin(math.pi * (t / duration_sec))
            # Subtle binaural beating (1 Hz difference between channels)
            left_val = (0.5 * math.sin(2 * math.pi * 146.83 * t) + 0.3 * math.sin(2 * math.pi * 220.00 * t)) * env * 0.3
            right_val = (0.5 * math.sin(2 * math.pi * 147.83 * t) + 0.3 * math.sin(2 * math.pi * 220.50 * t)) * env * 0.3
            samples.append((left_val, right_val))

        self._write_wav(file_path, samples, sample_rate)

    def _create_calming_chord(self, file_path, duration_sec=4.0, sample_rate=44100):
        """Soft, restorative chord designed to de-escalate tension and anger (F4, A4, C5)."""
        num_samples = int(duration_sec * sample_rate)
        freqs = [349.23, 440.00, 523.25]
        samples = []

        for i in range(num_samples):
            t = i / sample_rate
            env = math.sin(math.pi * (t / duration_sec)) ** 2
            wave_val = sum(math.sin(2 * math.pi * f * t) for f in freqs) / len(freqs)
            val = wave_val * env * 0.3
            samples.append((val, val))

        self._write_wav(file_path, samples, sample_rate)

    def _create_grounding_tone(self, file_path, duration_sec=4.0, sample_rate=44100):
        """Grounding, reassuring low warm tone for fear/anxiety relief (G2 + D3)."""
        num_samples = int(duration_sec * sample_rate)
        samples = []

        for i in range(num_samples):
            t = i / sample_rate
            env = math.sin(math.pi * (t / duration_sec)) ** 1.8
            val = (0.6 * math.sin(2 * math.pi * 98.0 * t) + 0.4 * math.sin(2 * math.pi * 146.83 * t)) * env * 0.35
            samples.append((val, val))

        self._write_wav(file_path, samples, sample_rate)

    def _create_surprise_bell(self, file_path, duration_sec=3.0, sample_rate=44100):
        """Sparkling curious chime (E5, G#5, B5)."""
        num_samples = int(duration_sec * sample_rate)
        freqs = [659.25, 830.61, 987.77]
        samples = []

        for i in range(num_samples):
            t = i / sample_rate
            decay = math.exp(-t * 2.2)
            val = sum(math.sin(2 * math.pi * f * t) for f in freqs) / len(freqs) * decay * 0.35
            samples.append((val, val))

        self._write_wav(file_path, samples, sample_rate)

    def _create_soothing_wave(self, file_path, duration_sec=3.5, sample_rate=44100):
        """Gentle harmonic ocean wave for soothing negative feelings."""
        num_samples = int(duration_sec * sample_rate)
        samples = []

        for i in range(num_samples):
            t = i / sample_rate
            env = math.sin(math.pi * (t / duration_sec)) ** 2
            val = (0.5 * math.sin(2 * math.pi * 174.61 * t) + 0.3 * math.sin(2 * math.pi * 261.63 * t)) * env * 0.3
            samples.append((val, val))

        self._write_wav(file_path, samples, sample_rate)

    def play_for_emotion(self, emotion):
        """Plays the corresponding ambient mood audio in desktop mode."""
        if not self.is_enabled or not self._pygame_initialized:
            return

        emotion = emotion.lower().strip()
        if emotion == self.current_emotion:
            # Already playing / aligned with current emotion
            return

        file_path = os.path.join(self.audio_dir, f"{emotion}.wav")
        if not os.path.exists(file_path):
            file_path = os.path.join(self.audio_dir, "neutral.wav")

        if os.path.exists(file_path):
            def _play():
                with self.lock:
                    try:
                        self.current_emotion = emotion
                        sound = pygame.mixer.Sound(file_path)
                        sound.set_volume(self.volume)
                        sound.play()
                    except Exception as e:
                        print(f"[SoundEngine] Playback error: {e}")

            threading.Thread(target=_play, daemon=True).start()

    def get_audio_base64(self, emotion):
        """Returns base64 encoded audio for embedding in HTML5 audio in Streamlit."""
        emotion = emotion.lower().strip()
        file_path = os.path.join(self.audio_dir, f"{emotion}.wav")
        if not os.path.exists(file_path):
            file_path = os.path.join(self.audio_dir, "neutral.wav")

        if os.path.exists(file_path):
            with open(file_path, "rb") as f:
                return base64.b64encode(f.read()).decode("utf-8")
        return ""

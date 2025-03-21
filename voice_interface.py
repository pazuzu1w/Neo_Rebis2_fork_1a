import threading
import queue
import tempfile
import pyaudio
import wave
import numpy as np
import speech_recognition as sr
from gtts import gTTS
from PyQt6.QtCore import QObject, pyqtSignal, QThread, Qt
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QPushButton,
                             QSlider, QLabel, QHBoxLayout, QComboBox, QCheckBox)
import pygame
import random
import os


class VoiceController(QObject):
    """Handles speech recognition and text-to-speech functionality."""

    # Signals
    speech_recognized_signal = pyqtSignal(str)
    tts_done_signal = pyqtSignal()
    status_signal = pyqtSignal(str)
    # Update signals
    speech_recognized_signal = pyqtSignal(str)
    tts_done_signal = pyqtSignal()
    status_signal = pyqtSignal(str)
    speech_started_signal = pyqtSignal(float)  # Intensity parameter
    speech_ended_signal = pyqtSignal()

    def __init__(self):
        super().__init__()

        # Initialize speech recognizer
        self.recognizer = sr.Recognizer()

        # Initialize pygame for audio playback
        pygame.mixer.init()

        # Settings
        self.voice_effects = "normal"  # normal, reverb, pitch_shift, glitch
        self.voice_language = "en"
        self.is_listening = False
        self.is_speaking = False
        self.recording_thread = None
        self.speaking_thread = None

        # Audio settings
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 44100
        self.CHUNK = 1024
        self.audio = pyaudio.PyAudio()

        # Create temp directory for audio files
        self.temp_dir = tempfile.mkdtemp()

    def start_listening(self):
        """Start continuous listening in background thread."""
        if self.is_listening:
            return

        self.is_listening = True
        self.recording_thread = threading.Thread(target=self._listen_continuously)
        self.recording_thread.daemon = True
        self.recording_thread.start()
        self.status_signal.emit("Listening...")

    def stop_listening(self):
        """Stop the continuous listening."""
        self.is_listening = False
        if self.recording_thread:
            self.recording_thread.join(timeout=1.0)
            self.recording_thread = None
        self.status_signal.emit("Listening stopped")

    def _listen_continuously(self):
        """Background thread that continuously listens for speech."""
        while self.is_listening:
            try:
                # Use the microphone as source
                with sr.Microphone() as source:
                    self.status_signal.emit("Adjusting for ambient noise...")
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    self.status_signal.emit("Listening...")

                    # Record audio
                    audio = self.recognizer.listen(source, timeout=10.0, phrase_time_limit=15.0)

                    try:
                        # Recognize speech
                        self.status_signal.emit("Processing speech...")
                        text = self.recognizer.recognize_google(audio)

                        if text:
                            self.speech_recognized_signal.emit(text)
                    except sr.UnknownValueError:
                        self.status_signal.emit("Could not understand audio")
                    except sr.RequestError as e:
                        self.status_signal.emit(f"Recognition error: {e}")

            except Exception as e:
                self.status_signal.emit(f"Error in listening: {e}")
                # Brief pause before retrying
                import time
                time.sleep(1)

    def speak(self, text):
        """Convert text to speech with optional effects."""
        if not text:
            return

        self.is_speaking = True

        # Analyze text for intensity
        intensity = self._analyze_text_intensity(text)
        # Emit signal that speaking has started, with intensity
        self.speech_started_signal.emit(intensity)

        self.speaking_thread = threading.Thread(target=self._speak_text, args=(text,))
        self.speaking_thread.daemon = True
        self.speaking_thread.start()

    def _speak_text(self, text):
        """Background thread for text-to-speech conversion."""
        try:
            # Generate speech file
            tts = gTTS(text=text, lang=self.voice_language, slow=False)
            temp_file = os.path.join(self.temp_dir, f"speech_{random.randint(1000, 9999)}.mp3")
            tts.save(temp_file)

            # Apply effects if needed
            if self.voice_effects != "normal":
                temp_file = self._apply_voice_effects(temp_file)

            # Play the audio
            pygame.mixer.music.load(temp_file)
            pygame.mixer.music.play()

            # Wait for playback to finish
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)

            # Clean up
            try:
                os.remove(temp_file)
            except:
                pass

            self.is_speaking = False
            self.tts_done_signal.emit()

            # Signal that speech has ended
            self.speech_ended_signal.emit()

        except Exception as e:
            self.status_signal.emit(f"Error in speech synthesis: {e}")
            self.is_speaking = False
            self.speech_ended_signal.emit()

    def _analyze_text_intensity(self, text):
        """
        Analyze text to determine overall speech intensity.
        Returns a float from 0.3 (calm) to 0.9 (intense).
        """
        # Default medium intensity
        intensity = 0.6

        # Look for intensity markers
        if '!' in text:
            # More exclamation marks = more intensity
            intensity += 0.05 * text.count('!')

        # Question marks slightly increase intensity
        if '?' in text:
            intensity += 0.02 * text.count('?')

        # ALL CAPS sections increase intensity
        caps_words = sum(1 for word in text.split() if word.isupper() and len(word) > 2)
        if caps_words > 0:
            intensity += 0.1 * min(caps_words / 10, 1.0)

        # Magical keywords increase intensity
        magical_terms = ['sigil', 'chaos', 'ritual', 'magic', 'invoke', 'evoke', 'banish', 'summon']
        for term in magical_terms:
            if term in text.lower():
                intensity += 0.03

        # Cap at 0.9 maximum
        intensity = min(0.9, intensity)

        return intensity

    def _apply_voice_effects(self, audio_file):
        """Apply various effects to the voice."""
        import librosa
        import soundfile as sf

        # Load the audio file
        try:
            y, sr = librosa.load(audio_file)
            output_file = os.path.join(self.temp_dir, f"effect_{random.randint(1000, 9999)}.wav")

            if self.voice_effects == "reverb":
                # Simple reverb-like effect with convolution
                reverb = np.exp(-np.linspace(0, 5, sr // 2))
                y_reverb = np.convolve(y, reverb, mode='full')[:len(y)]
                y = y + 0.5 * y_reverb

            elif self.voice_effects == "pitch_shift":
                # Pitch shift
                steps = random.uniform(-4, 4)
                y = librosa.effects.pitch_shift(y, sr=sr, n_steps=steps)

            elif self.voice_effects == "glitch":
                # Create glitch effect with random segments
                segments = []
                segment_length = sr // 8

                for i in range(0, len(y), segment_length):
                    segment = y[i:i + segment_length]
                    if random.random() < 0.2:  # 20% chance to glitch a segment
                        if random.random() < 0.5:
                            segment = np.flip(segment)  # Reverse segment
                        else:
                            segment = np.roll(segment, random.randint(0, len(segment) // 2))  # Shift segment
                    segments.append(segment)

                y = np.concatenate([s for s in segments if len(s) > 0])

            # Save the processed audio
            sf.write(output_file, y, sr)
            return output_file

        except Exception as e:
            self.status_signal.emit(f"Effect error: {e}")
            return audio_file  # Return original if processing fails

    def set_voice_effect(self, effect):
        """Set the voice effect to use."""
        self.voice_effects = effect

    def set_language(self, language_code):
        """Set the TTS language."""
        self.voice_language = language_code

    def cleanup(self):
        """Clean up resources."""
        self.stop_listening()

        if self.is_speaking:
            pygame.mixer.music.stop()
            if self.speaking_thread:
                self.speaking_thread.join(timeout=1.0)

        # Clean temp directory
        for file in os.listdir(self.temp_dir):
            try:
                os.remove(os.path.join(self.temp_dir, file))
            except:
                pass

        try:
            os.rmdir(self.temp_dir)
        except:
            pass

        self.audio.terminate()


class VoiceControlPanel(QWidget):
    """UI panel for controlling voice interface settings."""

    # Add this signal to the panel class
    auto_speak_changed = pyqtSignal(bool)

    def __init__(self, voice_controller):
        super().__init__()
        self.voice_controller = voice_controller
        self.setup_ui()

        # Connect signals
        self.voice_controller.status_signal.connect(self.update_status)

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Status label
        self.status_label = QLabel("Voice Ready")
        layout.addWidget(self.status_label)

        # Voice toggle button
        self.toggle_button = QPushButton("Start Listening")
        self.toggle_button.clicked.connect(self.toggle_listening)
        layout.addWidget(self.toggle_button)

        # Voice effect selection
        effect_layout = QHBoxLayout()
        effect_layout.addWidget(QLabel("Voice Effect:"))
        self.effect_combo = QComboBox()
        self.effect_combo.addItems(["normal", "reverb", "pitch_shift", "glitch"])
        self.effect_combo.currentTextChanged.connect(self.change_effect)
        effect_layout.addWidget(self.effect_combo)
        layout.addLayout(effect_layout)

        # Language selection
        lang_layout = QHBoxLayout()
        lang_layout.addWidget(QLabel("Language:"))
        self.lang_combo = QComboBox()

        # Add common languages
        languages = [
            ("English", "en"),
            ("French", "fr"),
            ("German", "de"),
            ("Spanish", "es"),
            ("Italian", "it"),
            ("Japanese", "ja"),
            ("Russian", "ru"),
            ("Chinese", "zh")
        ]

        for lang_name, lang_code in languages:
            self.lang_combo.addItem(lang_name, lang_code)

        self.lang_combo.currentIndexChanged.connect(self.change_language)
        lang_layout.addWidget(self.lang_combo)
        layout.addLayout(lang_layout)

        # Volume control
        vol_layout = QHBoxLayout()
        vol_layout.addWidget(QLabel("Volume:"))
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setMinimum(0)
        self.volume_slider.setMaximum(100)
        self.volume_slider.setValue(70)
        self.volume_slider.valueChanged.connect(self.change_volume)
        vol_layout.addWidget(self.volume_slider)
        layout.addLayout(vol_layout)

        # Test voice button
        self.test_button = QPushButton("Test Voice")
        self.test_button.clicked.connect(self.test_voice)
        layout.addWidget(self.test_button)

        # Add auto-speak checkbox
        self.auto_speak_checkbox = QCheckBox("Auto-speak AI responses")
        self.auto_speak_checkbox.setChecked(False)
        self.auto_speak_checkbox.toggled.connect(self.on_auto_speak_toggled)
        layout.addWidget(self.auto_speak_checkbox)

    def toggle_listening(self):
        """Toggle between listening and not listening."""
        if self.voice_controller.is_listening:
            self.voice_controller.stop_listening()
            self.toggle_button.setText("Start Listening")
        else:
            self.voice_controller.start_listening()
            self.toggle_button.setText("Stop Listening")

    def change_effect(self, effect):
        """Change the voice effect."""
        self.voice_controller.set_voice_effect(effect)

    def change_language(self, index):
        """Change the TTS language."""
        lang_code = self.lang_combo.itemData(index)
        self.voice_controller.set_language(lang_code)

    def change_volume(self, value):
        """Change the voice volume."""
        pygame.mixer.music.set_volume(value / 100.0)

    def test_voice(self):
        """Test the current voice settings."""
        test_phrases = [
            "Neo Rebis voice system active and ready.",
            "Your magical assistant is listening.",
            "The sigils speak through me now.",
            "Chaos becomes order, order becomes chaos, and words become reality.",
            "The boundaries between technology and magic are dissolving."
        ]
        self.voice_controller.speak(random.choice(test_phrases))

    def update_status(self, status):
        """Update the status label."""
        self.status_label.setText(status)

    def on_auto_speak_toggled(self, checked):
        """Emit signal when auto-speak is toggled."""
        self.auto_speak_changed.emit(checked)
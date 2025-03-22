import threading
import sys
import random
import os
from enum import Enum
import numpy as np
import speech_recognition as sr
from PyQt6.QtCore import QObject, pyqtSignal, QThread, Qt
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QPushButton,
                             QSlider, QLabel, QHBoxLayout, QComboBox, QCheckBox,
                             QGroupBox, QGridLayout, QSpacerItem, QSizePolicy)
from PyQt6.QtGui import QIcon, QFont
from PyQt6.QtTextToSpeech import QTextToSpeech, QVoice


class RitualMode(Enum):
    NORMAL = "normal"
    INVOCATION = "invocation"
    EVOCATION = "evocation"
    BANISHING = "banishing"
    CHARGING = "charging"


class VoiceController(QObject):
    """Handles speech recognition and text-to-speech functionality."""

    # Signals
    speech_recognized_signal = pyqtSignal(str)
    tts_done_signal = pyqtSignal()
    status_signal = pyqtSignal(str)
    speech_started_signal = pyqtSignal(float)
    speech_ended_signal = pyqtSignal()

    def __init__(self):
        super().__init__()

        # Initialize speech recognizer
        self.recognizer = sr.Recognizer()

        # Initialize Qt text-to-speech
        self.tts = QTextToSpeech()

        # Connect TTS state change signal
        self.tts.stateChanged.connect(self.handle_tts_state_change)

        # Settings
        self.voice_effects = "normal"  # normal, reverb, pitch_shift, glitch
        self.is_listening = False
        self.is_speaking = False
        self.recording_thread = None
        self.ritual_mode = RitualMode.NORMAL

        # Set up available voices
        self.available_voices = self.tts.availableVoices()
        if self.available_voices:
            # Try to find a female voice first (common for AI assistants)
            female_voice = None
            for voice in self.available_voices:
                if voice.gender() == QVoice.Gender.Female:
                    female_voice = voice
                    break

            # Set voice to female if found, otherwise use the first available
            self.tts.setVoice(female_voice if female_voice else self.available_voices[0])

        # Setup voice parameters
        self.tts.setRate(0.0)  # Normal rate
        self.tts.setPitch(0.0)  # Normal pitch
        self.tts.setVolume(1.0)  # Full volume

        # Save default voice
        self.default_voice = self.tts.voice()
        self.default_rate = 0.0
        self.default_pitch = 0.0
        self.default_volume = 1.0

        # Store available locales
        self.available_locales = self.tts.availableLocales()

    def speak(self, text):
        """Convert text to speech with optional effects."""
        if not text or self.is_speaking:
            return

        self.is_speaking = True

        # Analyze text for intensity
        intensity = self._analyze_text_intensity(text)
        # Emit signal that speaking has started, with intensity
        self.speech_started_signal.emit(intensity)

        # Apply voice effects based on current settings
        self._apply_voice_effect_settings()

        # Speak the text
        self.tts.say(text)

    def handle_tts_state_change(self, state):
        """Handle TTS state changes."""
        if state == QTextToSpeech.State.Ready and self.is_speaking:
            # Speech finished
            self.is_speaking = False
            self.tts_done_signal.emit()
            self.speech_ended_signal.emit()

            # Reset voice to normal if we're not in a ritual mode
            if self.ritual_mode == RitualMode.NORMAL:
                self._reset_voice_settings()

    def _apply_voice_effect_settings(self):
        """Apply voice effect settings to TTS."""
        # Apply effects based on ritual mode first
        if self.ritual_mode != RitualMode.NORMAL:
            self._apply_ritual_mode_effects()
            return

        # Otherwise apply regular voice effects
        if self.voice_effects == "normal":
            self.tts.setPitch(self.default_pitch)
            self.tts.setRate(self.default_rate)
        elif self.voice_effects == "reverb":
            # We can't do true reverb, but we can slow it down a bit
            self.tts.setPitch(self.default_pitch)
            self.tts.setRate(self.default_rate - 0.2)
        elif self.voice_effects == "pitch_shift":
            # Lower pitch
            self.tts.setPitch(self.default_pitch - 0.3)
            self.tts.setRate(self.default_rate)
        elif self.voice_effects == "glitch":
            # Raise pitch and speed up slightly
            self.tts.setPitch(self.default_pitch + 0.3)
            self.tts.setRate(self.default_rate + 0.2)

    def _apply_ritual_mode_effects(self):
        """Apply voice effects based on ritual mode."""
        if self.ritual_mode == RitualMode.INVOCATION:
            # Ethereal, reverberant voice
            self.tts.setPitch(self.default_pitch + 0.2)
            self.tts.setRate(self.default_rate - 0.3)
        elif self.ritual_mode == RitualMode.EVOCATION:
            # Deep, powerful voice
            self.tts.setPitch(self.default_pitch - 0.4)
            self.tts.setRate(self.default_rate - 0.1)
        elif self.ritual_mode == RitualMode.BANISHING:
            # Sharp, commanding voice
            self.tts.setPitch(self.default_pitch)
            self.tts.setRate(self.default_rate + 0.2)
        elif self.ritual_mode == RitualMode.CHARGING:
            # Intense, energetic voice
            self.tts.setPitch(self.default_pitch + 0.1)
            self.tts.setRate(self.default_rate + 0.1)

    def _reset_voice_settings(self):
        """Reset voice settings to default values."""
        self.tts.setPitch(self.default_pitch)
        self.tts.setRate(self.default_rate)
        self.tts.setVolume(self.default_volume)

    def stop_speaking(self):
        """Stop current speech."""
        if self.is_speaking:
            self.tts.stop()
            self.is_speaking = False

    def set_voice_effect(self, effect):
        """Set the voice effect to use."""
        self.voice_effects = effect

    def set_ritual_mode(self, mode):
        """Set the ritual voice mode."""
        if isinstance(mode, str):
            try:
                self.ritual_mode = RitualMode(mode)
            except ValueError:
                self.ritual_mode = RitualMode.NORMAL
        else:
            self.ritual_mode = mode

        # Apply effects immediately if not speaking
        if not self.is_speaking:
            self._apply_voice_effect_settings()

        # Return to normal effects when not in ritual mode
        if self.ritual_mode == RitualMode.NORMAL:
            self._reset_voice_settings()

    def set_voice(self, voice):
        """Set the TTS voice."""
        self.tts.setVoice(voice)

    def set_locale(self, locale):
        """Set the TTS locale."""
        self.tts.setLocale(locale)

    def set_rate(self, rate):
        """Set the speech rate."""
        self.default_rate = rate
        if not self.is_speaking:
            self.tts.setRate(rate)

    def set_pitch(self, pitch):
        """Set the speech pitch."""
        self.default_pitch = pitch
        if not self.is_speaking:
            self.tts.setPitch(pitch)

    def set_volume(self, volume):
        """Set the speech volume."""
        self.default_volume = volume
        self.tts.setVolume(volume)

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
        magical_terms = ['sigil', 'chaos', 'ritual', 'magic', 'invoke', 'evoke',
                         'banish', 'summon', 'conjure', 'manifest', 'egregore']
        for term in magical_terms:
            if term in text.lower():
                intensity += 0.03

        # Cap at 0.9 maximum
        intensity = min(0.9, intensity)

        return intensity

    # Speech recognition methods
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

    def cleanup(self):
        """Clean up resources."""
        self.stop_listening()
        self.stop_speaking()


class VoiceControlPanel(QWidget):
    """UI panel for controlling voice interface settings."""

    auto_speak_changed = pyqtSignal(bool)

    def __init__(self, voice_controller):
        super().__init__()
        self.voice_controller = voice_controller
        self.setWindowTitle("Voice Control Panel")
        self.resize(500, 600)
        self.setup_ui()

        # Connect signals
        self.voice_controller.status_signal.connect(self.update_status)
        self.voice_controller.tts_done_signal.connect(self.update_speaking_status)

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)

        # Status section
        status_group = QGroupBox("Status")
        status_layout = QVBoxLayout(status_group)

        self.status_label = QLabel("Voice Ready")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        status_layout.addWidget(self.status_label)

        # Speaking status
        self.speaking_status = QLabel("Not Speaking")
        self.speaking_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_layout.addWidget(self.speaking_status)

        main_layout.addWidget(status_group)

        # Voice control section
        voice_group = QGroupBox("Voice Controls")
        voice_layout = QGridLayout(voice_group)

        # Voice selection
        voice_layout.addWidget(QLabel("Voice:"), 0, 0)
        self.voice_combo = QComboBox()

        # Add available voices
        if hasattr(self.voice_controller, 'tts'):
            voices = self.voice_controller.available_voices
            for voice in voices:
                gender = "Female" if voice.gender() == QVoice.Gender.Female else "Male"
                age = {
                    QVoice.Age.Child: "Child",
                    QVoice.Age.Teenager: "Teen",
                    QVoice.Age.Adult: "Adult",
                    QVoice.Age.Senior: "Senior"
                }.get(voice.age(), "Adult")

                display_name = f"{voice.name()} ({gender}, {age})"
                self.voice_combo.addItem(display_name, voice)

            self.voice_combo.currentIndexChanged.connect(self.change_voice)

        voice_layout.addWidget(self.voice_combo, 0, 1, 1, 3)

        # Language/locale selection
        voice_layout.addWidget(QLabel("Language:"), 1, 0)
        self.locale_combo = QComboBox()

        # Add available locales
        if hasattr(self.voice_controller, 'available_locales'):
            for locale in self.voice_controller.available_locales:
                self.locale_combo.addItem(locale.nativeLanguageName(), locale)

            self.locale_combo.currentIndexChanged.connect(self.change_locale)

        voice_layout.addWidget(self.locale_combo, 1, 1, 1, 3)

        # Rate slider
        voice_layout.addWidget(QLabel("Speed:"), 2, 0)
        self.rate_slider = QSlider(Qt.Orientation.Horizontal)
        self.rate_slider.setMinimum(-10)
        self.rate_slider.setMaximum(10)
        self.rate_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.rate_slider.setTickInterval(5)
        self.rate_slider.setValue(0)
        self.rate_slider.valueChanged.connect(self.change_rate)
        voice_layout.addWidget(self.rate_slider, 2, 1, 1, 3)

        # Rate labels
        voice_layout.addWidget(QLabel("Slow"), 3, 1)
        voice_layout.addWidget(QLabel("Normal"), 3, 2, Qt.AlignmentFlag.AlignCenter)
        voice_layout.addWidget(QLabel("Fast"), 3, 3, Qt.AlignmentFlag.AlignRight)

        # Pitch slider
        voice_layout.addWidget(QLabel("Pitch:"), 4, 0)
        self.pitch_slider = QSlider(Qt.Orientation.Horizontal)
        self.pitch_slider.setMinimum(-10)
        self.pitch_slider.setMaximum(10)
        self.pitch_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.pitch_slider.setTickInterval(5)
        self.pitch_slider.setValue(0)
        self.pitch_slider.valueChanged.connect(self.change_pitch)
        voice_layout.addWidget(self.pitch_slider, 4, 1, 1, 3)

        # Pitch labels
        voice_layout.addWidget(QLabel("Low"), 5, 1)
        voice_layout.addWidget(QLabel("Normal"), 5, 2, Qt.AlignmentFlag.AlignCenter)
        voice_layout.addWidget(QLabel("High"), 5, 3, Qt.AlignmentFlag.AlignRight)

        # Volume slider
        voice_layout.addWidget(QLabel("Volume:"), 6, 0)
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setMinimum(0)
        self.volume_slider.setMaximum(100)
        self.volume_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.volume_slider.setTickInterval(20)
        self.volume_slider.setValue(100)
        self.volume_slider.valueChanged.connect(self.change_volume)
        voice_layout.addWidget(self.volume_slider, 6, 1, 1, 3)

        # Volume labels
        voice_layout.addWidget(QLabel("Off"), 7, 1)
        voice_layout.addWidget(QLabel("Med"), 7, 2, Qt.AlignmentFlag.AlignCenter)
        voice_layout.addWidget(QLabel("Max"), 7, 3, Qt.AlignmentFlag.AlignRight)

        main_layout.addWidget(voice_group)

        # Effects section
        effects_group = QGroupBox("Voice Effects")
        effects_layout = QVBoxLayout(effects_group)

        # Standard effects
        effect_layout = QHBoxLayout()
        effect_layout.addWidget(QLabel("Effect:"))
        self.effect_combo = QComboBox()
        self.effect_combo.addItems(["normal", "reverb", "pitch_shift", "glitch"])
        self.effect_combo.currentTextChanged.connect(self.change_effect)
        effect_layout.addWidget(self.effect_combo)
        effects_layout.addLayout(effect_layout)

        # Ritual mode
        ritual_layout = QHBoxLayout()
        ritual_layout.addWidget(QLabel("Ritual Mode:"))
        self.ritual_combo = QComboBox()
        for mode in RitualMode:
            self.ritual_combo.addItem(mode.value.title(), mode.value)
        self.ritual_combo.currentIndexChanged.connect(self.change_ritual_mode)
        ritual_layout.addWidget(self.ritual_combo)
        effects_layout.addLayout(ritual_layout)

        main_layout.addWidget(effects_group)

        # Speech recognition section
        sr_group = QGroupBox("Speech Recognition")
        sr_layout = QVBoxLayout(sr_group)

        # Listening toggle
        self.listen_button = QPushButton("Start Listening")
        self.listen_button.setCheckable(True)
        self.listen_button.toggled.connect(self.toggle_listening)
        sr_layout.addWidget(self.listen_button)

        # Auto-speak checkbox
        self.auto_speak_checkbox = QCheckBox("Auto-speak AI responses")
        self.auto_speak_checkbox.setChecked(False)
        self.auto_speak_checkbox.toggled.connect(self.on_auto_speak_toggled)
        sr_layout.addWidget(self.auto_speak_checkbox)

        main_layout.addWidget(sr_group)

        # Test section
        test_group = QGroupBox("Test")
        test_layout = QVBoxLayout(test_group)

        # Test voice button
        self.test_button = QPushButton("Test Voice")
        self.test_button.clicked.connect(self.test_voice)
        test_layout.addWidget(self.test_button)

        # Stop button
        self.stop_button = QPushButton("Stop Speaking")
        self.stop_button.clicked.connect(self.stop_speaking)
        test_layout.addWidget(self.stop_button)

        main_layout.addWidget(test_group)

        # Add spacer at the bottom
        spacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        main_layout.addItem(spacer)

    def toggle_listening(self, checked):
        """Toggle between listening and not listening."""
        if checked:
            self.voice_controller.start_listening()
            self.listen_button.setText("Stop Listening")
        else:
            self.voice_controller.stop_listening()
            self.listen_button.setText("Start Listening")

    def change_effect(self, effect):
        """Change the voice effect."""
        self.voice_controller.set_voice_effect(effect)

    def change_ritual_mode(self, index):
        """Change the ritual mode."""
        if index >= 0:
            mode = self.ritual_combo.itemData(index)
            self.voice_controller.set_ritual_mode(mode)

            # Update effect combo to match
            if mode != RitualMode.NORMAL.value:
                self.effect_combo.setEnabled(False)
            else:
                self.effect_combo.setEnabled(True)

    def change_voice(self, index):
        """Change the TTS voice."""
        if hasattr(self.voice_controller, 'tts') and index >= 0:
            voice = self.voice_combo.itemData(index)
            self.voice_controller.set_voice(voice)

    def change_locale(self, index):
        """Change the TTS locale."""
        if hasattr(self.voice_controller, 'tts') and index >= 0:
            locale = self.locale_combo.itemData(index)
            self.voice_controller.set_locale(locale)

    def change_rate(self, value):
        """Change the speech rate."""
        rate = value / 10.0
        self.voice_controller.set_rate(rate)

    def change_pitch(self, value):
        """Change the speech pitch."""
        pitch = value / 10.0
        self.voice_controller.set_pitch(pitch)

    def change_volume(self, value):
        """Change the voice volume."""
        volume = value / 100.0
        self.voice_controller.set_volume(volume)

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
        self.speaking_status.setText("Speaking...")

    def stop_speaking(self):
        """Stop current speech."""
        self.voice_controller.stop_speaking()
        self.speaking_status.setText("Not Speaking")

    def update_status(self, status):
        """Update the status label."""
        self.status_label.setText(status)

    def update_speaking_status(self):
        """Update the speaking status when speech is done."""
        self.speaking_status.setText("Not Speaking")

    def on_auto_speak_toggled(self, checked):
        """Emit signal when auto-speak is toggled."""
        self.auto_speak_changed.emit(checked)
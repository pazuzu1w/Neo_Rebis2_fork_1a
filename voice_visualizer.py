from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush
import numpy as np
import random
import pyaudio
import struct


class VoiceVisualizer(QWidget):
    """Visualizes AI speech output with magical/sigil-like patterns."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Voice Visualization")
        self.resize(400, 400)

        # Remove microphone input code
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 44100
        self.CHUNK = 1024

        # AI speech visualization variables
        self.points = []
        self.lines = []
        self.circles = []
        self.audio_level = 0
        self.smooth_level = 0
        self.base_color = QColor(0, 128, 255)
        self.accent_color = QColor(255, 64, 128)

        # Speech status
        self.ai_speaking = False
        self.ai_speech_intensity = 0.5
        self.ai_speech_timer = 0

        # Mode settings
        self.viz_mode = "sigil"  # sigil, wave, fractal

        # Animation timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_visualization)
        self.timer.start(30)  # ~30fps

    def set_ai_speaking(self, is_speaking, intensity=0.5):
        """
        Signal that the AI is speaking to drive visualization.

        Args:
            is_speaking: Boolean indicating if AI is speaking
            intensity: Float between 0 and 1 indicating speech intensity
        """
        self.ai_speaking = is_speaking
        self.ai_speech_intensity = intensity
        self.ai_speech_timer = 0

        # If starting speech, reset visualization elements
        if is_speaking:
            self.points = []
            self.lines = []
            self.circles = []

    def update_visualization(self):
        """Update the visualization based on AI speech signals."""
        # Generate a speech level
        if self.ai_speaking:
            # Generate a dynamic audio level for AI speech
            # Oscillate intensity for a more natural effect
            self.ai_speech_timer += 1
            base_intensity = self.ai_speech_intensity
            # Add some variation to the intensity
            oscillation = 0.3 * np.sin(self.ai_speech_timer * 0.2)
            self.audio_level = max(0.1, min(1.0, base_intensity + oscillation))
        else:
            # Gradually reduce audio level when not speaking
            self.audio_level = max(0, self.audio_level - 0.05)

        # Smooth the level for more stable visualizations
        self.smooth_level = 0.9 * self.smooth_level + 0.1 * self.audio_level

        # Update visualization elements based on mode
        if self.viz_mode == "sigil":
            self._update_sigil_viz()
        elif self.viz_mode == "wave":
            self._update_wave_viz()
        elif self.viz_mode == "fractal":
            self._update_fractal_viz()

        # Trigger repaint
        self.update()

    def _update_sigil_viz(self):
        """Update the sigil visualization."""
        # Clear existing points if we're at a low level
        if self.smooth_level < 0.01 and random.random() < 0.1:
            self.points = []
            self.lines = []
            self.circles = []

        # Add new points based on audio level
        center_x, center_y = self.width() / 2, self.height() / 2
        radius = min(self.width(), self.height()) * 0.4

        # Add points if audio is active
        if self.smooth_level > 0.02:
            # Calculate position based on angle
            angle = random.uniform(0, 2 * np.pi)
            r = radius * (0.2 + 0.8 * self.smooth_level)
            x = center_x + r * np.cos(angle)
            y = center_y + r * np.sin(angle)

            # Add point
            self.points.append((x, y, self.smooth_level))

            # Possibly add connections
            if len(self.points) > 1 and random.random() < 0.3:
                idx1 = len(self.points) - 1
                idx2 = random.randint(0, len(self.points) - 2)
                self.lines.append((idx1, idx2, self.smooth_level))

            # Possibly add circles
            if random.random() < 0.05:
                self.circles.append((x, y, r * 0.2 * self.smooth_level, self.smooth_level))

        # Remove oldest elements if we have too many
        max_points = 30
        if len(self.points) > max_points:
            self.points = self.points[-max_points:]
            self.lines = [l for l in self.lines if l[0] < max_points and l[1] < max_points]
            self.circles = self.circles[-10:]

    def _update_wave_viz(self):
        """Update the wave visualization."""
        # Simply store the current level for painting
        pass

    def _update_fractal_viz(self):
        """Update the fractal visualization."""
        # Store level for painting
        pass

    def set_viz_mode(self, mode):
        """Set the visualization mode."""
        self.viz_mode = mode

        # Clear existing elements
        self.points = []
        self.lines = []
        self.circles = []

    def paintEvent(self, event):
        """Paint the visualization."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Fill background
        painter.fillRect(self.rect(), QColor(0, 0, 0))

        if self.viz_mode == "sigil":
            self._paint_sigil(painter)
        elif self.viz_mode == "wave":
            self._paint_wave(painter)
        elif self.viz_mode == "fractal":
            self._paint_fractal(painter)

    def _paint_sigil(self, painter):
        """Paint the sigil visualization."""
        # Draw lines between points
        for idx1, idx2, level in self.lines:
            if idx1 < len(self.points) and idx2 < len(self.points):
                x1, y1, _ = self.points[idx1]
                x2, y2, _ = self.points[idx2]

                # Set line color based on level
                color = QColor(
                    self.base_color.red() + int((self.accent_color.red() - self.base_color.red()) * level),
                    self.base_color.green() + int((self.accent_color.green() - self.base_color.green()) * level),
                    self.base_color.blue() + int((self.accent_color.blue() - self.base_color.blue()) * level),
                )

                pen = QPen(color)
                pen.setWidth(1 + int(level * 3))
                painter.setPen(pen)
                painter.drawLine(int(x1), int(y1), int(x2), int(y2))

        # Draw circles
        for x, y, r, level in self.circles:
            # Set circle color
            color = QColor(
                self.accent_color.red(),
                self.accent_color.green(),
                self.accent_color.blue(),
                int(128 * level)
            )

            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(color))
            painter.drawEllipse(int(x - r), int(y - r), int(r * 2), int(r * 2))

        # Draw points
        for x, y, level in self.points:
            # Set point color
            color = QColor(
                self.base_color.red(),
                self.base_color.green(),
                self.base_color.blue(),
                int(255 * level)
            )

            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(color))

            # Size based on level
            size = 2 + int(level * 8)
            painter.drawEllipse(int(x - size / 2), int(y - size / 2), size, size)

    def _paint_wave(self, painter):
        """Paint the wave visualization."""
        width, height = self.width(), self.height()
        center_y = height / 2

        # Draw wave patterns
        pen = QPen(self.base_color)
        pen.setWidth(2)
        painter.setPen(pen)

        # Generate sine wave based on audio level
        points = []
        amplitude = height * 0.3 * self.smooth_level

        for x in range(0, width, 2):
            # Multiple frequencies for complexity
            y = center_y
            y += amplitude * np.sin(x * 0.02 + self.timer.interval() * 0.01)
            y += amplitude * 0.5 * np.sin(x * 0.04 + self.timer.interval() * 0.02)
            points.append((x, y))

        # Draw the wave
        for i in range(1, len(points)):
            x1, y1 = points[i - 1]
            x2, y2 = points[i]
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))

    def _paint_fractal(self, painter):
        """Paint the fractal visualization."""
        width, height = self.width(), self.height()
        center_x, center_y = width / 2, height / 2

        # Draw a recursive tree fractal
        pen = QPen(self.accent_color)
        pen.setWidth(2)
        painter.setPen(pen)

        # Start with a trunk
        angle = -np.pi / 2  # Start pointing up
        length = height * 0.3 * (0.5 + self.smooth_level)

        # Recursive function to draw branches
        def draw_branch(x, y, angle, length, depth):
            if depth <= 0 or length < 3:
                return

            # Calculate end point
            end_x = x + length * np.cos(angle)
            end_y = y + length * np.sin(angle)

            # Draw this branch
            painter.drawLine(int(x), int(y), int(end_x), int(end_y))

            # Draw sub-branches
            branch_angle = 0.4 + 0.3 * self.smooth_level  # Wider angle with more sound
            new_length = length * (0.6 + 0.1 * self.smooth_level)

            draw_branch(end_x, end_y, angle - branch_angle, new_length, depth - 1)
            draw_branch(end_x, end_y, angle + branch_angle, new_length, depth - 1)

        # Start recursive drawing
        depth = 6 + int(self.smooth_level * 4)  # More complex with more sound
        draw_branch(center_x, height * 0.7, angle, length, depth)

    def closeEvent(self, event):
        """Clean up resources."""
        # Stop the timer
        self.timer.stop()
        event.accept()
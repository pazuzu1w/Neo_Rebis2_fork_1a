import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLineEdit,
                             QPushButton, QLabel, QSlider, QComboBox, QGridLayout)
from PyQt6.QtCore import Qt
import random
import string


class SigilGenerator(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sigil Generator")
        self.resize(800, 600)
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)

        # Input area
        input_layout = QGridLayout()

        self.intention_label = QLabel("Enter your intention:")
        self.intention_input = QLineEdit()
        self.intention_input.setPlaceholderText("I want to manifest...")

        self.complexity_label = QLabel("Complexity:")
        self.complexity_slider = QSlider(Qt.Orientation.Horizontal)
        self.complexity_slider.setMinimum(1)
        self.complexity_slider.setMaximum(10)
        self.complexity_slider.setValue(5)

        self.style_label = QLabel("Style:")
        self.style_combo = QComboBox()
        self.style_combo.addItems(["Chaotic", "Geometric", "Organic", "Runic", "Alchemical"])

        self.generate_button = QPushButton("Generate Sigil")
        self.generate_button.clicked.connect(self.generate_sigil)

        self.save_button = QPushButton("Save Sigil")
        self.save_button.clicked.connect(self.save_sigil)

        # Add widgets to input layout
        input_layout.addWidget(self.intention_label, 0, 0)
        input_layout.addWidget(self.intention_input, 0, 1, 1, 3)
        input_layout.addWidget(self.complexity_label, 1, 0)
        input_layout.addWidget(self.complexity_slider, 1, 1, 1, 3)
        input_layout.addWidget(self.style_label, 2, 0)
        input_layout.addWidget(self.style_combo, 2, 1)
        input_layout.addWidget(self.generate_button, 3, 0, 1, 2)
        input_layout.addWidget(self.save_button, 3, 2, 1, 2)

        # Sigil display area
        self.figure = plt.figure(figsize=(8, 8), facecolor='black')
        self.canvas = FigureCanvasQTAgg(self.figure)

        # Add all to main layout
        main_layout.addLayout(input_layout)
        main_layout.addWidget(self.canvas, 1)

    def generate_sigil(self):
        intention = self.intention_input.text().strip()
        if not intention:
            return

        complexity = self.complexity_slider.value()
        style = self.style_combo.currentText()

        # Process the intention text
        processed_text = self.process_intention(intention)

        # Clear the figure
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.set_facecolor('black')

        # Draw based on style
        if style == "Chaotic":
            self.draw_chaotic_sigil(ax, processed_text, complexity)
        elif style == "Geometric":
            self.draw_geometric_sigil(ax, processed_text, complexity)
        elif style == "Organic":
            self.draw_organic_sigil(ax, processed_text, complexity)
        elif style == "Runic":
            self.draw_runic_sigil(ax, processed_text, complexity)
        elif style == "Alchemical":
            self.draw_alchemical_sigil(ax, processed_text, complexity)

        # Remove axis
        ax.set_axis_off()
        ax.set_xlim(-1.2, 1.2)
        ax.set_ylim(-1.2, 1.2)

        # Update canvas
        self.canvas.draw()

    def process_intention(self, text):
        # Remove vowels and duplicates (traditional sigil method)
        vowels = "aeiou"
        text = text.lower()
        text = ''.join([c for c in text if c not in vowels])
        text = ''.join([c for c in text if c.isalpha()])

        # Remove duplicate letters
        result = ""
        for char in text:
            if char not in result:
                result += char

        return result

    def draw_chaotic_sigil(self, ax, text, complexity):
        points = []
        # Generate points based on characters
        for i, char in enumerate(text):
            # Convert char to position on unit circle
            angle = (ord(char) - ord('a')) * (360 / 26) * (np.pi / 180)
            r = 0.8  # Fixed radius
            x = r * np.cos(angle)
            y = r * np.sin(angle)
            points.append((x, y))

        # Draw connections
        for i in range(len(points)):
            for j in range(i + 1, min(i + complexity + 1, len(points))):
                ax.plot([points[i][0], points[j][0]],
                        [points[i][1], points[j][1]],
                        'w-', alpha=0.7, linewidth=2)

        # Draw points
        ax.scatter([p[0] for p in points], [p[1] for p in points],
                   color='red', s=50, zorder=10)

    def draw_geometric_sigil(self, ax, text, complexity):
        # Generate a base shape based on text length
        sides = min(len(text), 12)
        angles = np.linspace(0, 2 * np.pi, sides + 1)[:-1]
        base_points = [(np.cos(angle), np.sin(angle)) for angle in angles]

        # Draw base shape
        ax.plot([p[0] for p in base_points] + [base_points[0][0]],
                [p[1] for p in base_points] + [base_points[0][1]],
                'w-', alpha=0.7, linewidth=2)

        # Add internal lines based on characters
        for i, char in enumerate(text):
            idx1 = i % sides
            idx2 = (i + ord(char) % sides) % sides
            ax.plot([base_points[idx1][0], base_points[idx2][0]],
                    [base_points[idx1][1], base_points[idx2][1]],
                    'r-', alpha=0.5, linewidth=1)

    def draw_organic_sigil(self, ax, text, complexity):
        # Create a flowing, organic sigil using bezier curves
        seed = sum(ord(c) for c in text)
        random.seed(seed)

        # Generate control points
        n_points = len(text) + 2
        angles = np.linspace(0, 2 * np.pi, n_points) + np.array([random.uniform(-0.5, 0.5) for _ in range(n_points)])
        radii = np.array([random.uniform(0.5, 0.9) for _ in range(n_points)])
        points = [(r * np.cos(a), r * np.sin(a)) for r, a in zip(radii, angles)]

        # Draw smooth curve through points
        from scipy.interpolate import splprep, splev
        points = np.array(points)
        tck, u = splprep([points[:, 0], points[:, 1]], s=0, per=1)
        unew = np.linspace(0, 1, 100)
        curve = splev(unew, tck)

        ax.plot(curve[0], curve[1], 'w-', alpha=0.8, linewidth=2.5)

        # Add details based on complexity
        for _ in range(complexity):
            idx = random.randint(0, len(points) - 1)
            ax.plot([0, points[idx][0]], [0, points[idx][1]],
                    'r-', alpha=0.4, linewidth=1)

    def draw_runic_sigil(self, ax, text, complexity):
        # Create a sigil with straight lines resembling runes
        # Convert text to a series of strokes
        strokes = []
        for char in text:
            # Get ASCII value and normalize
            val = ord(char) - ord('a')

            # Define some basic rune-like strokes
            if val % 4 == 0:  # Vertical line
                strokes.append(('v', (val % 10) / 10))
            elif val % 4 == 1:  # Horizontal line
                strokes.append(('h', (val % 10) / 10))
            elif val % 4 == 2:  # Diagonal up
                strokes.append(('du', (val % 10) / 10))
            else:  # Diagonal down
                strokes.append(('dd', (val % 10) / 10))

        # Draw the combined strokes
        x, y = 0, 0
        points = [(x, y)]

        for stroke_type, pos in strokes:
            if stroke_type == 'v':
                y += 0.2
                points.append((x, y))
            elif stroke_type == 'h':
                x += 0.2
                points.append((x, y))
            elif stroke_type == 'du':
                x += 0.15
                y += 0.15
                points.append((x, y))
            elif stroke_type == 'dd':
                x += 0.15
                y -= 0.15
                points.append((x, y))

        # Center the sigil
        points = np.array(points)
        center = np.mean(points, axis=0)
        points = points - center

        # Scale to unit circle
        max_dist = np.max(np.abs(points))
        points = points / max_dist * 0.8

        # Draw the sigil
        ax.plot(points[:, 0], points[:, 1], 'w-', linewidth=2)

        # Add embellishments based on complexity
        for i in range(min(complexity, len(points) - 1)):
            idx = i % len(points)
            ax.scatter(points[idx, 0], points[idx, 1], color='red', s=40, zorder=10)

    def draw_alchemical_sigil(self, ax, text, complexity):
        # Create a sigil with circular and triangular elements
        seed = sum(ord(c) for c in text)
        random.seed(seed)

        # Draw base circle
        circle = plt.Circle((0, 0), 0.8, fill=False, color='white', linewidth=2)
        ax.add_artist(circle)

        # Add symbols based on characters
        for i, char in enumerate(text):
            val = ord(char) - ord('a')
            angle = val * (360 / 26) * (np.pi / 180)

            # Position on circle
            x = 0.8 * np.cos(angle)
            y = 0.8 * np.sin(angle)

            # Add a symbol based on character
            if val % 5 == 0:  # Small circle
                ax.add_artist(plt.Circle((x, y), 0.1, fill=False, color='red'))
            elif val % 5 == 1:  # Triangle
                triangle_points = [(x, y),
                                   (x + 0.1, y - 0.1),
                                   (x - 0.1, y - 0.1)]
                ax.fill(
                    [p[0] for p in triangle_points],
                    [p[1] for p in triangle_points],
                    'none', edgecolor='red', linewidth=1)
            elif val % 5 == 2:  # Cross
                ax.plot([x - 0.1, x + 0.1], [y, y], 'r-', linewidth=1)
                ax.plot([x, x], [y - 0.1, y + 0.1], 'r-', linewidth=1)
            elif val % 5 == 3:  # Square
                ax.add_artist(plt.Rectangle((x - 0.07, y - 0.07), 0.14, 0.14,
                                            fill=False, color='red'))
            else:  # Line to center
                ax.plot([0, x], [0, y], 'r-', alpha=0.7, linewidth=1)

        # Draw connecting lines between elements
        points = []
        for i in range(len(text)):
            val = ord(text[i]) - ord('a')
            angle = val * (360 / 26) * (np.pi / 180)
            x = 0.8 * np.cos(angle)
            y = 0.8 * np.sin(angle)
            points.append((x, y))

        # Connect based on complexity
        for i in range(min(complexity, len(points))):
            start = i % len(points)
            end = (i + 2) % len(points)
            ax.plot([points[start][0], points[end][0]],
                    [points[start][1], points[end][1]],
                    'w--', alpha=0.5, linewidth=1)

    def save_sigil(self):
        from PyQt6.QtWidgets import QFileDialog
        options = QFileDialog.Option.DontUseNativeDialog
        fileName, _ = QFileDialog.getSaveFileName(
            self, "Save Sigil", "", "PNG Files (*.png);;All Files (*)", options=options)
        if fileName:
            if not fileName.endswith(".png"):
                fileName += ".png"
            self.figure.savefig(fileName, facecolor='black', dpi=300, bbox_inches='tight')
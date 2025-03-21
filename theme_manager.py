import random
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtCore import QTimer


class ThemeManager:
    def __init__(self, main_window):
        self.main_window = main_window
        self.current_theme = "default"
        self.chaos_timer = QTimer()
        self.chaos_timer.timeout.connect(self.apply_chaos_shift)

        # Define base themes
        self.themes = {
            "default": {
                "bg_color": "#2D2D2D",
                "text_color": "white",
                "accent_color": "#2196F3",
                "user_font": QFont("Comic Sans MS", 14),
                "bot_font": QFont("Consolas", 14),
            },
            "twilight": {
                "bg_color": "#1A1A2E",
                "text_color": "#E94560",
                "accent_color": "#16213E",
                "user_font": QFont("Courier New", 14),
                "bot_font": QFont("Georgia", 14),
            },
            "solar": {
                "bg_color": "#F9F7F7",
                "text_color": "#112D4E",
                "accent_color": "#3F72AF",
                "user_font": QFont("Verdana", 14),
                "bot_font": QFont("Tahoma", 14),
            }
        }

        # Fonts for chaos mode
        self.chaos_fonts = [
            "Papyrus", "Impact", "Copperplate", "Luminari",
            "Bradley Hand", "Trattatello", "Brush Script MT",
            "Chalkduster", "Comic Sans MS", "Andale Mono"
        ]

    def set_theme(self, theme_name):
        if theme_name == "chaos":
            self.start_chaos_mode()
            return

        self.stop_chaos_mode()
        self.current_theme = theme_name
        theme = self.themes.get(theme_name, self.themes["default"])

        # Apply theme to main window
        self.main_window.setStyleSheet(f"""
            QWidget {{ background-color: {theme['bg_color']}; }}
            QTextEdit, QPlainTextEdit {{ 
                background-color: {self.lighten_color(theme['bg_color'])}; 
                color: {theme['text_color']}; 
                border-radius: 8px;
                padding: 8px;
            }}
            QPushButton {{ 
                background-color: {theme['accent_color']}; 
                color: white;
                border-radius: 4px;
                padding: 8px 16px;
            }}
            QPushButton:hover {{ 
                background-color: {self.lighten_color(theme['accent_color'])}; 
            }}
        """)

        # Update fonts
        self.main_window.current_font = theme["user_font"]
        self.main_window.bot_font = theme["bot_font"]
        self.main_window.current_color = theme["text_color"]
        self.main_window.bot_color = theme["accent_color"]

    def start_chaos_mode(self):
        self.current_theme = "chaos"
        self.chaos_timer.start(10000)  # Shift every 10 seconds
        self.apply_chaos_shift()

    def stop_chaos_mode(self):
        self.chaos_timer.stop()

    def apply_chaos_shift(self):
        # Generate random colors
        bg_color = self.random_color(max_bright=60)
        text_color = self.complementary_color(bg_color)
        accent_color = self.random_color()

        # Random fonts
        user_font = QFont(random.choice(self.chaos_fonts), random.randint(12, 16))
        bot_font = QFont(random.choice(self.chaos_fonts), random.randint(12, 16))

        # Apply random styles
        self.main_window.setStyleSheet(f"""
            QWidget {{ background-color: {bg_color}; }}
            QTextEdit, QPlainTextEdit {{ 
                background-color: {self.lighten_color(bg_color)}; 
                color: {text_color}; 
                border-radius: {random.randint(2, 10)}px;
                padding: {random.randint(5, 12)}px;
            }}
            QPushButton {{ 
                background-color: {accent_color}; 
                color: {text_color};
                border-radius: {random.randint(2, 8)}px;
                padding: {random.randint(6, 10)}px {random.randint(10, 20)}px;
            }}
        """)

        # Update fonts
        self.main_window.current_font = user_font
        self.main_window.bot_font = bot_font
        self.main_window.current_color = text_color
        self.main_window.bot_color = accent_color

    def random_color(self, max_bright=100):
        r = random.randint(0, max_bright)
        g = random.randint(0, max_bright)
        b = random.randint(0, max_bright)
        return f"#{r:02x}{g:02x}{b:02x}"

    def complementary_color(self, hex_color):
        # Strip the # if present
        hex_color = hex_color.lstrip('#')

        # Convert to RGB
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)

        # Calculate complementary (simple method - invert)
        r, g, b = 255 - r, 255 - g, 255 - b

        return f"#{r:02x}{g:02x}{b:02x}"

    def lighten_color(self, hex_color, factor=0.2):
        # Strip the # if present
        hex_color = hex_color.lstrip('#')

        # Convert to RGB
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)

        # Lighten
        r = min(255, int(r + (255 - r) * factor))
        g = min(255, int(g + (255 - g) * factor))
        b = min(255, int(b + (255 - b) * factor))

        return f"#{r:02x}{g:02x}{b:02x}"
from PyQt6.QtCore import Qt, QThread
from PyQt6.QtWidgets import (QMainWindow, QPlainTextEdit, QPushButton,
                             QVBoxLayout, QWidget, QHBoxLayout, QMenuBar, QMenu,
                             QFileDialog, QTextEdit, QMessageBox)
from model import init_model, list_available_models, DEFAULT_MODEL, SYSTEM_PROMPT, memory_manager

from PyQt6.QtGui import QFont, QAction, QShortcut, QKeySequence, QTextCharFormat, QColor
from qWorker import ChatWorker
from theme_manager import ThemeManager
from visualizer import MemoryVisualizer
from sigil_generator import SigilGenerator
from voice_interface import VoiceController, VoiceControlPanel
from voice_visualizer import VoiceVisualizer

class ChatWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Neo Rebis")
        self.resize(600, 400)

        self.current_font = QFont("Comic Sans MS", 14)
        self.current_color = "white"  # Initial color as a string
        self.model_instance = None
        self.chat = None
        self.bot_font = QFont("Consolas", 14)  # Default bot font
        self.bot_color = "#2196F3"  # Initial color as a string
        # Model parameters
        self.temperature = 1.0
        self.top_p = 1.0
        self.top_k = 1
        self.max_output_tokens = 4000
        self.block_harassment = False
        self.block_hate_speech = False
        self.block_sexually_explicit = False
        self.block_dangerous_content = False

        self.selected_model_name = DEFAULT_MODEL
        self.system_prompt = SYSTEM_PROMPT

        # Initialize the model
        self.init_or_reinit_model()

        self.setup_ui()
        self.setup_shortcuts()
        self.setup_status_bar()
        self.ChatWorker = None

        self.theme_manager = ThemeManager(self)
        self.theme_manager.set_theme("default")

        # Create visualizer
        self.memory_visualizer = MemoryVisualizer(memory_manager)

        self.sigil_generator = SigilGenerator()

        # Initialize voice controller
        self.voice_controller = VoiceController()
        self.voice_controller.speech_recognized_signal.connect(self.handle_speech_input)
        self.voice_controller.speech_started_signal.connect(self.on_speech_started)
        self.voice_controller.speech_ended_signal.connect(self.on_speech_ended)

        # Initialize voice visualizer
        self.voice_visualizer = VoiceVisualizer()

    def init_or_reinit_model(self, model_name=None, system_prompt=None, temperature=None, top_p=None, top_k=None, max_output_tokens=None,
                             block_harassment=None, block_hate_speech=None, block_sexually_explicit=None, block_dangerous_content=None):
        """Initializes or reinitializes the AI model."""
        model_name = model_name if model_name is not None else self.selected_model_name
        system_prompt = system_prompt if system_prompt is not None else self.system_prompt
        temperature = temperature if temperature is not None else self.temperature
        top_p = top_p if top_p is not None else self.top_p
        top_k = top_k if top_k is not None else self.top_k
        max_output_tokens = max_output_tokens if max_output_tokens is not None else self.max_output_tokens
        block_harassment = block_harassment if block_harassment is not None else self.block_harassment
        block_hate_speech = block_hate_speech if block_hate_speech is not None else self.block_hate_speech
        block_sexually_explicit = block_sexually_explicit if block_sexually_explicit is not None else self.block_sexually_explicit
        block_dangerous_content = block_dangerous_content if block_dangerous_content is not None else self.block_dangerous_content

        try:
            self.model_instance, self.chat = init_model(model_name=model_name, system_prompt=system_prompt,
                                                        temperature=temperature, top_p=top_p, top_k=top_k,
                                                        max_output_tokens=max_output_tokens,
                                                        block_harassment=block_harassment, block_hate_speech=block_hate_speech,
                                                        block_sexually_explicit=block_sexually_explicit, block_dangerous_content=block_dangerous_content)

            self.statusBar().showMessage("Model initialized!", 3000)
            self.selected_model_name = model_name
            self.system_prompt = system_prompt
            self.temperature = temperature
            self.top_p = top_p
            self.top_k = top_k
            self.max_output_tokens = max_output_tokens
            self.block_harassment = block_harassment
            self.block_hate_speech = block_hate_speech
            self.block_sexually_explicit = block_sexually_explicit
            self.block_dangerous_content = block_dangerous_content

        except Exception as e:
            self.show_error_message(f"Model initialization failed: {e}")
            self.model_instance, self.chat = None, None

    def show_error_message(self, message):
        """Displays an error message."""
        self.chatLog.append(f'<p style="color: red;">Error: {message}</p>')

    def setup_ui(self):
        """Sets up the UI."""
        self.create_menu_bar()
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        self.chatLog = QTextEdit()
        self.chatLog.setReadOnly(True)

        self.inputTextBox = QPlainTextEdit()
        self.inputTextBox.setPlaceholderText("Enter your message here...")
        self.inputTextBox.installEventFilter(self)

        self.sendButton = QPushButton("Send")
        self.sendButton.clicked.connect(self.handle_send)


        button_layout = QHBoxLayout()
        button_layout.addWidget(self.sendButton)
        self.sendButton.setToolTip("Ctrl+Enter")

        main_layout = QVBoxLayout(central_widget)
        main_layout.addWidget(self.chatLog, 3)
        main_layout.addWidget(self.inputTextBox, 1)
        main_layout.addLayout(button_layout)
        self.inputTextBox.setFocus()

        # Add voice button to button layout
        self.voiceButton = QPushButton("🎤")
        self.voiceButton.setToolTip("Toggle Voice Input")
        self.voiceButton.clicked.connect(self.toggle_voice)
        button_layout.addWidget(self.voiceButton)

        self.auto_speak = False  # Default to off

    def create_menu_bar(self):
        """Creates the menu bar."""
        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu("&File")
        self.add_action(file_menu, "&Exit", self.close, "Ctrl+Q")

        themes_menu = menu_bar.addMenu("&Themes")
        self.add_action(themes_menu, "&Default", lambda: self.theme_manager.set_theme("default"))
        self.add_action(themes_menu, "&Twilight", lambda: self.theme_manager.set_theme("twilight"))
        self.add_action(themes_menu, "&Solar", lambda: self.theme_manager.set_theme("solar"))
        self.add_action(themes_menu, "&Chaos Mode", lambda: self.theme_manager.set_theme("chaos"))

        # Add Visualization menu
        viz_menu = menu_bar.addMenu("&Visualize")
        self.add_action(viz_menu, "&Memory Network", self.show_memory_network)
        self.add_action(viz_menu, "&Topic Heatmap", self.show_topic_heatmap)

        tools_menu = menu_bar.addMenu("&Tools")
        self.add_action(tools_menu, "&Sigil Generator", self.show_sigil_generator)

        # In create_menu_bar method:
        debug_menu = menu_bar.addMenu("&Debug")
        self.add_action(debug_menu, "&Generate Test Data", self.generate_test_data)

        # Add Voice menu
        voice_menu = menu_bar.addMenu("&Voice")
        self.add_action(voice_menu, "&Voice Settings", self.toggle_voice_panel)
        self.add_action(voice_menu, "&Start Listening", lambda: self.voice_controller.start_listening())
        self.add_action(voice_menu, "&Stop Listening", lambda: self.voice_controller.stop_listening())
        self.add_action(voice_menu, "&Read Last Response", lambda: self.speak_response(self.last_response))

        voice_menu.addSeparator()
        self.add_action(voice_menu, "Show Visualizer", self.toggle_voice_visualizer)
        submenu = voice_menu.addMenu("Visualizer Mode")
        self.add_action(submenu, "Sigil Mode", lambda: self.set_visualizer_mode("sigil"))
        self.add_action(submenu, "Wave Mode", lambda: self.set_visualizer_mode("wave"))
        self.add_action(submenu, "Fractal Mode", lambda: self.set_visualizer_mode("fractal"))

    def add_action(self, menu, text, slot, shortcut=None):
        """Adds an action to a menu."""
        action = QAction(text, self)
        action.triggered.connect(slot)
        if shortcut:
            action.setShortcut(shortcut)
        menu.addAction(action)

    def setup_shortcuts(self):
        """Sets up shortcuts."""
        QShortcut(QKeySequence("Ctrl+Enter"), self, self.handle_send)

    def setup_status_bar(self):
        """Sets up the status bar."""
        self.statusBar().showMessage("Ready")

    def handle_send(self):
        """Handles sending messages."""
        user_text = self.inputTextBox.toPlainText().strip()
        if not user_text:
            return
        if not self.chat:
            self.show_error_message("Chat model not initialized.")
            return

        self.append_user_message(user_text)
        self.inputTextBox.clear()
        self.start_ai_response(user_text)

    def append_user_message(self, user_text):
        """Appends user messages."""
        set_style = f'style="color: {self.current_color}; font-family: {self.current_font.family()}; font-size: {self.current_font.pointSize()}px;"'
        self.chatLog.append(f'<p {set_style}>User: {user_text}</p>')

    def start_ai_response(self, user_text):
        """Starts the AI response."""
        self.statusBar().showMessage("Generating response...")
        self.worker = ChatWorker(self.chat, user_text)
        self.worker.stream_signal.connect(self.append_ai_message)
        self.worker.error_signal.connect(self.handle_error)
        self.worker.done_signal.connect(self.handle_response_complete)
        self.worker.start()

    def append_ai_message(self, chunk_text):
        """Appends AI messages."""
        set_style = f'style="color: {self.bot_color}; font-family: {self.bot_font.family()}; font-size: {self.bot_font.pointSize()}px;"'
        self.chatLog.append(f'<p {set_style}>AI: {chunk_text}</p>')

    def handle_response_complete(self):
        """Handles AI response completion"""
        self.statusBar().showMessage("Response generated", 3000)

        # Store last response for possible voice playback
        self.last_response = self.chatLog.toPlainText().split("AI:")[-1].strip()

        # Auto-speak if enabled
        if hasattr(self, 'auto_speak') and self.auto_speak:
            self.speak_response(self.last_response)


    def scroll_chat_to_bottom(self):
        """Scrolls to the bottom."""
        self.chatLog.verticalScrollBar().setValue(self.chatLog.verticalScrollBar().maximum())

    def handle_error(self, err):
        """Handles worker errors."""
        self.show_error_message(f"Error: {err}")
        self.statusBar().showMessage("Error occurred", 3000)

    def eventFilter(self, source, event):
        """Filters events."""
        if (source is self.inputTextBox and event.type() == event.Type.KeyPress
                and event.key() == Qt.Key.Key_Return and event.modifiers() == Qt.KeyboardModifier.ControlModifier):
            self.handle_send()
            return True
        return super().eventFilter(source, event)

    def show_memory_network(self):
        """Shows the memory network visualization."""
        self.memory_visualizer.generate_network_graph()
        self.memory_visualizer.show()

    def show_topic_heatmap(self):
        """Shows the topic heatmap visualization."""
        self.memory_visualizer.generate_topic_heatmap()
        self.memory_visualizer.show()

    def show_sigil_generator(self):
        """Shows the sigil generator."""
        self.sigil_generator.show()

    def generate_test_data(self):
        """Generates test data for visualization."""
        from memory import memory_manager

        # Sample conversations
        test_conversations = [
            "I've been thinking about chaos magic and sigil creation techniques.",
            "Poetry seems to function like a magical ritual sometimes.",
            "How do symbols and archetypes influence our subconscious?",
            "I'm exploring the connection between programming and magical thinking.",
            "Dreams have a symbolic language that feels like a personal mythology.",
            "Technology is just modern magic with different symbols.",
            "The universe seems to have synchronistic patterns if you pay attention.",
            "Creative writing helps me access different states of consciousness.",
            "Python programming can be a form of modern sigil magic.",
            "I've been experimenting with visualization techniques for memory enhancement."
        ]

        # Add sample data to memory
        print("Adding test data to memory...")
        for i, text in enumerate(test_conversations):
            # Create dummy conversation
            ai_response = f"Response #{i}: {text}"
            memory_manager.add_conversation(text, ai_response)

        print(f"Added {len(test_conversations)} test conversations to memory")
        self.statusBar().showMessage("Test data generated", 3000)

    def handle_speech_input(self, text):
        """Handle recognized speech input."""
        # Set the input text and send
        self.inputTextBox.setPlainText(text)
        self.handle_send()

    def toggle_voice_panel(self):
        """Show/hide the voice control panel."""
        if hasattr(self, 'voice_panel') and self.voice_panel.isVisible():
            self.voice_panel.hide()
        else:
            if not hasattr(self, 'voice_panel'):
                self.voice_panel = VoiceControlPanel(self.voice_controller)
                # Connect a signal from the panel to update auto_speak
                if hasattr(self.voice_panel, 'auto_speak_changed'):
                    self.voice_panel.auto_speak_changed.connect(self.set_auto_speak)
            self.voice_panel.show()

    def set_auto_speak(self, enabled):
        """Set whether responses should be automatically spoken."""
        self.auto_speak = enabled

    def speak_response(self, response_text):
        """Speak the AI response."""
        self.voice_controller.speak(response_text)

    def closeEvent(self, event):
        """Clean up resources when closing the app."""
        # Clean up voice controller
        if hasattr(self, 'voice_controller'):
            self.voice_controller.cleanup()
        event.accept()

    def toggle_voice_visualizer(self):
        """Show/hide the voice visualizer."""
        if self.voice_visualizer.isVisible():
            self.voice_visualizer.hide()
        else:
            self.voice_visualizer.show()

    def set_visualizer_mode(self, mode):
        """Set the visualizer mode."""
        self.voice_visualizer.set_viz_mode(mode)

    def toggle_voice(self):
        """Toggle voice input on/off."""
        if self.voice_controller.is_listening:
            self.voice_controller.stop_listening()
            self.voiceButton.setStyleSheet("")
        else:
            self.voice_controller.start_listening()
            self.voiceButton.setStyleSheet("background-color: #E94560;")

    def on_speech_started(self, intensity):
        """Handler for when AI speech starts."""
        if hasattr(self, 'voice_visualizer') and self.voice_visualizer.isVisible():
            self.voice_visualizer.set_ai_speaking(True, intensity)

    def on_speech_ended(self):
        """Handler for when AI speech ends."""
        if hasattr(self, 'voice_visualizer') and self.voice_visualizer.isVisible():
            self.voice_visualizer.set_ai_speaking(False)
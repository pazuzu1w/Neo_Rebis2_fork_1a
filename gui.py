# gui.py - updated
from PyQt6.QtCore import Qt, QThread
from PyQt6.QtWidgets import (QMainWindow, QPlainTextEdit, QPushButton,
                             QVBoxLayout, QWidget, QHBoxLayout, QMenuBar, QMenu,
                             QFileDialog, QTextEdit, QMessageBox, QSplitter,
                             QTabWidget, QLabel, QComboBox, QSlider, QCheckBox,
                             QGroupBox, QFormLayout)
from PyQt6.QtGui import QFont, QAction, QShortcut, QKeySequence, QTextCharFormat, QColor
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from qWorker import ChatWorker


class MemoryBrowser(QWidget):
    def __init__(self, memory_component):
        super().__init__()
        self.memory_component = memory_component
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Memory type filter
        self.memory_type_combo = QComboBox()
        self.memory_type_combo.addItems(["All Types", "Episodic", "Semantic", "Procedural"])
        self.memory_type_combo.currentTextChanged.connect(self.filter_memories)

        # Search box
        self.search_box = QPlainTextEdit()
        self.search_box.setPlaceholderText("Search memories...")
        self.search_box.setMaximumHeight(80)

        # Search button
        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self.search_memories)

        # Results display
        self.results_display = QTextEdit()
        self.results_display.setReadOnly(True)

        # Memory details
        self.memory_details = QTextEdit()
        self.memory_details.setReadOnly(True)

        # Layout
        top_layout = QHBoxLayout()
        top_layout.addWidget(QLabel("Memory Type:"))
        top_layout.addWidget(self.memory_type_combo)

        search_layout = QHBoxLayout()
        search_layout.addWidget(self.search_box, 3)
        search_layout.addWidget(self.search_button, 1)

        # Add widgets to layout
        layout.addLayout(top_layout)
        layout.addLayout(search_layout)

        # Split view for results and details
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.addWidget(self.results_display)
        splitter.addWidget(self.memory_details)
        layout.addWidget(splitter, 1)

    def search_memories(self):
        query = self.search_box.toPlainText().strip()
        if not query:
            return

        memory_type = self.memory_type_combo.currentText().lower()
        if memory_type == "all types":
            memory_type = None

        results = self.memory_component.search_memories(query, memory_type)

        self.results_display.clear()
        if not results:
            self.results_display.append("No results found.")
            return

        for i, memory in enumerate(results):
            self.results_display.append(f"<h3>Result {i + 1}</h3>")
            self.results_display.append(
                f"<p><strong>Type:</strong> {memory['metadata'].get('memory_type', 'unknown')}</p>")
            self.results_display.append(
                f"<p><strong>Timestamp:</strong> {memory['metadata'].get('timestamp', 'unknown')}</p>")

            # Show snippet of text
            text = memory["text"]
            if len(text) > 100:
                text = text[:100] + "..."
            self.results_display.append(f"<p>{text}</p>")

            # Add button to view full memory
            self.results_display.append(f'<button onclick="viewMemory(\'{memory["id"]}\')">View Full Memory</button>')
            self.results_display.append("<hr>")

    def filter_memories(self):
        # Re-run search with new filter
        self.search_memories()

    def view_memory(self, memory_id):
        memory = self.memory_component.get_memory_by_id(memory_id)
        if not memory:
            self.memory_details.setText("Memory not found")
            return

        # Display memory details
        self.memory_details.clear()
        self.memory_details.append(f"<h2>Memory Details</h2>")
        self.memory_details.append(f"<p><strong>ID:</strong> {memory['id']}</p>")
        self.memory_details.append(f"<p><strong>Type:</strong> {memory['metadata'].get('memory_type', 'unknown')}</p>")

        # Format timestamp
        timestamp = memory['metadata'].get('timestamp', 'unknown')
        self.memory_details.append(f"<p><strong>Timestamp:</strong> {timestamp}</p>")

        # Add other metadata
        for key, value in memory['metadata'].items():
            if key not in ['memory_type', 'timestamp']:
                self.memory_details.append(f"<p><strong>{key}:</strong> {value}</p>")

        # Display full text
        self.memory_details.append("<h3>Content:</h3>")
        self.memory_details.append(f"<p>{memory['text']}</p>")


class MemoryVisualization(QWidget):
    def __init__(self, memory_component):
        super().__init__()
        self.memory_component = memory_component
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Query input
        query_layout = QHBoxLayout()
        self.query_input = QPlainTextEdit()
        self.query_input.setPlaceholderText("Enter topic to visualize...")
        self.query_input.setMaximumHeight(80)
        self.visualize_button = QPushButton("Visualize")
        self.visualize_button.clicked.connect(self.generate_visualization)

        query_layout.addWidget(self.query_input, 3)
        query_layout.addWidget(self.visualize_button, 1)

        # Settings
        settings_layout = QHBoxLayout()
        settings_layout.addWidget(QLabel("Depth:"))
        self.depth_slider = QSlider(Qt.Orientation.Horizontal)
        self.depth_slider.setMinimum(1)
        self.depth_slider.setMaximum(3)
        self.depth_slider.setValue(2)
        self.depth_label = QLabel("2")
        self.depth_slider.valueChanged.connect(lambda v: self.depth_label.setText(str(v)))

        settings_layout.addWidget(self.depth_slider)
        settings_layout.addWidget(self.depth_label)
        settings_layout.addWidget(QLabel("Max Connections:"))

        self.connections_slider = QSlider(Qt.Orientation.Horizontal)
        self.connections_slider.setMinimum(5)
        self.connections_slider.setMaximum(50)
        self.connections_slider.setValue(20)
        self.connections_label = QLabel("20")
        self.connections_slider.valueChanged.connect(lambda v: self.connections_label.setText(str(v)))

        settings_layout.addWidget(self.connections_slider)
        settings_layout.addWidget(self.connections_label)

        # Matplotlib figure
        self.figure = plt.figure(figsize=(8, 6))
        self.canvas = FigureCanvas(self.figure)

        # Legend
        legend_layout = QHBoxLayout()
        legend_layout.addWidget(QLabel("Legend:"))
        legend_layout.addWidget(self._create_color_label("Episodic", "blue"))
        legend_layout.addWidget(self._create_color_label("Semantic", "green"))
        legend_layout.addWidget(self._create_color_label("Procedural", "red"))
        legend_layout.addWidget(self._create_color_label("Consolidated", "purple"))
        legend_layout.addStretch()

        # Add to main layout
        layout.addLayout(query_layout)
        layout.addLayout(settings_layout)
        layout.addWidget(self.canvas, 1)
        layout.addLayout(legend_layout)

    def _create_color_label(self, text, color):
        label = QLabel(f"■ {text}")
        label.setStyleSheet(f"color: {color}")
        return label

    def generate_visualization(self):
        query = self.query_input.toPlainText().strip()
        if not query:
            return

        depth = self.depth_slider.value()
        max_connections = self.connections_slider.value()

        # Generate graph
        graph = self.memory_component.generate_memory_graph(query, depth, max_connections)
        if not graph:
            # Clear figure and show message
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            ax.text(0.5, 0.5, "No memories found", ha='center', va='center')
            ax.axis('off')
            self.canvas.draw()
            return

        # Clear figure
        self.figure.clear()

        # Get the visualization
        import networkx as nx

        # Create position layout
        pos = nx.spring_layout(graph)

        # Node colors based on type
        color_map = {
            "episodic": "blue",
            "semantic": "green",
            "procedural": "red",
            "consolidated_episodic": "purple",
            "unknown": "gray"
        }

        node_colors = [color_map.get(graph.nodes[node]["type"], "gray") for node in graph.nodes]

        # Draw the graph
        nx.draw_networkx_nodes(graph, pos, node_color=node_colors, alpha=0.8, node_size=300, ax=self.figure.gca())

        # Edge weights for thickness
        edge_weights = [graph[u][v]["weight"] * 5 for u, v in graph.edges]
        nx.draw_networkx_edges(graph, pos, width=edge_weights, alpha=0.5, ax=self.figure.gca())

        # Add labels
        labels = {node: graph.nodes[node]["text"] for node in graph.nodes}
        nx.draw_networkx_labels(graph, pos, labels, font_size=8, ax=self.figure.gca())

        self.figure.gca().set_title("Memory Connections Visualization")
        self.figure.gca().axis("off")

        # Draw
        self.canvas.draw()


class SettingsTab(QWidget):
    def __init__(self, engine):
        super().__init__()
        self.engine = engine
        self.model_component = engine.get_component("model")
        self.memory_component = engine.get_component("memory")
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Model settings
        model_group = QGroupBox("Model Settings")
        model_layout = QFormLayout(model_group)

        # Model dropdown
        self.model_dropdown = QComboBox()
        self.model_dropdown.addItems(["gemini-2.0-flash-001", "gemini-2.0-pro-exp-02-05"])
        current_model = getattr(self.model_component, "model_name", "gemini-2.0-flash-001")
        self.model_dropdown.setCurrentText(current_model)
        model_layout.addRow("Model:", self.model_dropdown)

        # Temperature
        self.temperature_slider = QSlider(Qt.Orientation.Horizontal)
        self.temperature_slider.setMinimum(0)
        self.temperature_slider.setMaximum(100)
        temp = getattr(self.model_component, "temperature", 1.0)
        self.temperature_slider.setValue(int(temp * 100))
        self.temperature_label = QLabel(f"{temp:.2f}")
        self.temperature_slider.valueChanged.connect(
            lambda v: self.temperature_label.setText(f"{v / 100:.2f}")
        )

        temp_layout = QHBoxLayout()
        temp_layout.addWidget(self.temperature_slider)
        temp_layout.addWidget(self.temperature_label)
        model_layout.addRow("Temperature:", temp_layout)

        # System prompt
        self.system_prompt = QPlainTextEdit()
        self.system_prompt.setPlainText(
            getattr(self.model_component, "system_prompt", "You are c0d3, the machine half of Neo Rebis...")
        )
        self.system_prompt.setMinimumHeight(100)
        model_layout.addRow("System Prompt:", self.system_prompt)

        # Safety settings
        safety_group = QGroupBox("Safety Settings")
        safety_layout = QVBoxLayout(safety_group)

        self.block_harassment = QCheckBox("Block Harassment")
        self.block_harassment.setChecked(getattr(self.model_component, "block_harassment", False))
        safety_layout.addWidget(self.block_harassment)

        self.block_hate_speech = QCheckBox("Block Hate Speech")
        self.block_hate_speech.setChecked(getattr(self.model_component, "block_hate_speech", False))
        safety_layout.addWidget(self.block_hate_speech)

        self.block_sexually_explicit = QCheckBox("Block Sexually Explicit")
        self.block_sexually_explicit.setChecked(getattr(self.model_component, "block_sexually_explicit", False))
        safety_layout.addWidget(self.block_sexually_explicit)

        # Continuing SettingsTab class
        self.block_dangerous_content = QCheckBox("Block Dangerous Content")
        self.block_dangerous_content.setChecked(getattr(self.model_component, "block_dangerous_content", False))
        safety_layout.addWidget(self.block_dangerous_content)

        # Memory settings
        memory_group = QGroupBox("Memory Settings")
        memory_layout = QFormLayout(memory_group)

        self.auto_consolidation = QCheckBox("Auto Consolidation")
        self.auto_consolidation.setChecked(getattr(self.memory_component, "auto_consolidation", True))
        memory_layout.addRow("Enable Automatic Memory Consolidation:", self.auto_consolidation)

        self.consolidation_days = QSlider(Qt.Orientation.Horizontal)
        self.consolidation_days.setMinimum(1)
        self.consolidation_days.setMaximum(90)
        cons_days = getattr(self.memory_component, "consolidation_days", 30)
        self.consolidation_days.setValue(cons_days)
        self.cons_days_label = QLabel(f"{cons_days} days")
        self.consolidation_days.valueChanged.connect(
            lambda v: self.cons_days_label.setText(f"{v} days")
        )

        cons_days_layout = QHBoxLayout()
        cons_days_layout.addWidget(self.consolidation_days)
        cons_days_layout.addWidget(self.cons_days_label)
        memory_layout.addRow("Consolidate After:", cons_days_layout)

        self.auto_pruning = QCheckBox("Auto Pruning")
        self.auto_pruning.setChecked(getattr(self.memory_component, "auto_pruning", True))
        memory_layout.addRow("Enable Automatic Memory Pruning:", self.auto_pruning)

        # Save button
        self.save_button = QPushButton("Save Settings")
        self.save_button.clicked.connect(self.save_settings)

        # Add to layout
        layout.addWidget(model_group)
        layout.addWidget(safety_group)
        layout.addWidget(memory_group)
        layout.addWidget(self.save_button)
        layout.addStretch()

    def save_settings(self):
        """Save all settings and reinitialize components"""
        # Update model settings
        model_settings = {
            "model_name": self.model_dropdown.currentText(),
            "temperature": self.temperature_slider.value() / 100.0,
            "system_prompt": self.system_prompt.toPlainText(),
            "block_harassment": self.block_harassment.isChecked(),
            "block_hate_speech": self.block_hate_speech.isChecked(),
            "block_sexually_explicit": self.block_sexually_explicit.isChecked(),
            "block_dangerous_content": self.block_dangerous_content.isChecked()
        }

        self.model_component.update_settings(model_settings)

        # Update memory settings
        self.memory_component.auto_consolidation = self.auto_consolidation.isChecked()
        self.memory_component.auto_pruning = self.auto_pruning.isChecked()
        self.memory_component.consolidation_days = self.consolidation_days.value()

        # Save to config if available
        config = self.engine.get_component("config")
        if config:
            config.set_section("model", model_settings)
            config.set_section("memory", {
                "auto_consolidation": self.memory_component.auto_consolidation,
                "auto_pruning": self.memory_component.auto_pruning,
                "consolidation_days": self.memory_component.consolidation_days
            })

        # Show confirmation
        QMessageBox.information(self, "Settings Saved", "Settings have been saved and applied.")


class ChatWindow(QMainWindow):
    def __init__(self, engine):
        super().__init__()
        self.engine = engine
        self.setWindowTitle("Neo Rebis")
        self.resize(1000, 800)

        # Get components from engine
        self.model_component = engine.get_component("model")
        self.memory_component = engine.get_component("memory")
        self.logger = engine.get_component("logger")

        # Appearance settings
        self.current_font = QFont("Comic Sans MS", 14)
        self.current_color = "white"  # Initial color as a string
        self.bot_font = QFont("Consolas", 14)  # Default bot font
        self.bot_color = "#2196F3"  # Initial color as a string

        # Initialize UI
        self.setup_ui()
        self.setup_shortcuts()
        self.setup_status_bar()

        # Initialize thread management
        self.worker = None

        # Create active conversation thread
        if self.memory_component:
            self.conversation_thread = self.memory_component.create_conversation_thread("New Conversation")
        else:
            self.conversation_thread = None

        # Log startup
        if self.logger:
            self.logger.info("ChatWindow initialized")

    def setup_ui(self):
        """Sets up the UI."""
        # Create central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # Main layout
        main_layout = QHBoxLayout(self.central_widget)

        # Create main chat area
        chat_widget = QWidget()
        chat_layout = QVBoxLayout(chat_widget)

        # Chat log
        self.chatLog = QTextEdit()
        self.chatLog.setReadOnly(True)

        # Input area
        self.inputTextBox = QPlainTextEdit()
        self.inputTextBox.setPlaceholderText("Enter your message here...")
        self.inputTextBox.installEventFilter(self)

        # Send button
        self.sendButton = QPushButton("Send")
        self.sendButton.clicked.connect(self.handle_send)
        self.sendButton.setToolTip("Ctrl+Enter")

        # Layout for input and button
        input_layout = QHBoxLayout()
        input_layout.addWidget(self.inputTextBox, 1)
        input_layout.addWidget(self.sendButton)

        # Add to chat layout
        chat_layout.addWidget(self.chatLog, 3)
        chat_layout.addLayout(input_layout)

        # Create sidebar with tabs
        self.sidebar = QTabWidget()
        self.sidebar.setMinimumWidth(300)

        # Memory browser tab
        if self.memory_component:
            self.memory_browser = MemoryBrowser(self.memory_component)
            self.sidebar.addTab(self.memory_browser, "Memory Browser")

            self.memory_viz = MemoryVisualization(self.memory_component)
            self.sidebar.addTab(self.memory_viz, "Memory Visualization")

        # Settings tab
        self.settings_tab = SettingsTab(self.engine)
        self.sidebar.addTab(self.settings_tab, "Settings")

        # Add main components to main layout
        main_layout.addWidget(chat_widget, 3)
        main_layout.addWidget(self.sidebar, 1)

        # Create menu bar
        self.create_menu_bar()

        # Focus on input
        self.inputTextBox.setFocus()

    def create_menu_bar(self):
        """Creates the menu bar."""
        menu_bar = self.menuBar()

        # File menu
        file_menu = menu_bar.addMenu("&File")
        self.add_action(file_menu, "&New Conversation", self.new_conversation)
        self.add_action(file_menu, "&Save Conversation", self.save_conversation)
        self.add_action(file_menu, "&Export Chat Log", self.export_chat)
        file_menu.addSeparator()
        self.add_action(file_menu, "&Exit", self.close, "Ctrl+Q")

        # Edit menu
        edit_menu = menu_bar.addMenu("&Edit")
        self.add_action(edit_menu, "&Clear Chat", self.clear_chat)
        self.add_action(edit_menu, "&Copy Selected Text", self.copy_selected, "Ctrl+C")

        # View menu
        view_menu = menu_bar.addMenu("&View")
        self.add_action(view_menu, "&Toggle Sidebar", self.toggle_sidebar)

        # Memory menu
        if self.memory_component:
            memory_menu = menu_bar.addMenu("&Memory")
            self.add_action(memory_menu, "&Run Consolidation", self.run_consolidation)
            self.add_action(memory_menu, "&Run Pruning", self.run_pruning)
            self.add_action(memory_menu, "&Visualize Current Context", self.visualize_context)

        # Help menu
        help_menu = menu_bar.addMenu("&Help")
        self.add_action(help_menu, "&About", self.show_about)

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

    def new_conversation(self):
        """Start a new conversation."""
        reply = QMessageBox.question(self, 'New Conversation',
                                     'Start a new conversation? This will clear the current chat.',
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.clear_chat()
            if self.memory_component:
                self.conversation_thread = self.memory_component.create_conversation_thread("New Conversation")

    def save_conversation(self):
        """Save the current conversation thread."""
        if not self.memory_component or not self.conversation_thread:
            QMessageBox.warning(self, "Save Failed", "No active conversation to save.")
            return

        # Save thread metadata
        self.conversation_thread.save_thread_metadata()
        QMessageBox.information(self, "Conversation Saved",
                                "Conversation saved to memory system.")

    def export_chat(self):
        """Export chat log to a file."""
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Chat Log", "",
                                                   "Text Files (*.txt);;HTML Files (*.html);;All Files (*)")
        if not file_path:
            return

        try:
            if file_path.endswith(".html"):
                with open(file_path, "w") as f:
                    f.write(self.chatLog.toHtml())
            else:
                with open(file_path, "w") as f:
                    f.write(self.chatLog.toPlainText())

            self.statusBar().showMessage(f"Chat log saved to {file_path}", 3000)
        except Exception as e:
            QMessageBox.warning(self, "Export Failed", f"Error exporting chat log: {e}")

    def clear_chat(self):
        """Clear the chat log."""
        self.chatLog.clear()
        self.statusBar().showMessage("Chat cleared", 3000)

    def copy_selected(self):
        """Copy selected text to clipboard."""
        self.chatLog.copy()

    def toggle_sidebar(self):
        """Toggle sidebar visibility."""
        self.sidebar.setVisible(not self.sidebar.isVisible())

    def run_consolidation(self):
        """Run memory consolidation."""
        if not self.memory_component:
            return

        result = self.memory_component.run_consolidation()
        QMessageBox.information(self, "Memory Consolidation",
                                f"Consolidation complete: {result}")

    def run_pruning(self):
        """Run memory pruning."""
        if not self.memory_component:
            return

        result = self.memory_component.run_pruning()
        QMessageBox.information(self, "Memory Pruning",
                                f"Pruning complete: {result}")

    def visualize_context(self):
        """Visualize the current conversation context."""
        if not self.memory_component or not self.conversation_thread:
            QMessageBox.warning(self, "Visualization Failed", "No active conversation context.")
            return

        # Get the last few messages for context
        messages = self.conversation_thread.get_full_thread()
        if not messages:
            return

        # Use the last message as query
        last_msg = messages[-1]["text"]

        # Switch to visualization tab and set query
        self.sidebar.setCurrentWidget(self.memory_viz)
        self.memory_viz.query_input.setPlainText(last_msg)
        self.memory_viz.generate_visualization()

    def show_about(self):
        """Show about dialog."""
        QMessageBox.about(self, "About Neo Rebis",
                          "Neo Rebis - Advanced AI Communication Interface\n\n"
                          "Version 0.2.0\n"
                          "Created by Tony\n\n"
                          "An AI agent system with memory, planning and reasoning.")

    def handle_send(self):
        """Handles sending messages."""
        user_text = self.inputTextBox.toPlainText().strip()
        if not user_text:
            return

        if not self.model_component:
            self.show_error_message("AI model not initialized.")
            return

        # Append user message to chat
        self.append_user_message(user_text)

        # Save to conversation thread if available
        if self.memory_component and self.conversation_thread:
            self.conversation_thread.add_message(user_text, "user")

        # Clear input
        self.inputTextBox.clear()

        # Send to model
        self.start_ai_response(user_text)

    def append_user_message(self, user_text):
        """Appends user messages."""
        set_style = f'style="color: {self.current_color}; font-family: {self.current_font.family()}; font-size: {self.current_font.pointSize()}px;"'
        self.chatLog.append(f'<p {set_style}>User: {user_text}</p>')

    def start_ai_response(self, user_text):
        """Starts the AI response."""
        self.statusBar().showMessage("Generating response...")

        # Create worker thread
        self.worker = ChatWorker(self.model_component, user_text)
        self.worker.stream_signal.connect(self.append_ai_message)
        self.worker.error_signal.connect(self.handle_error)
        self.worker.done_signal.connect(self.handle_response_complete)
        self.worker.start()

    def append_ai_message(self, chunk_text):
        """Appends AI messages."""
        set_style = f'style="color: {self.bot_color}; font-family: {self.bot_font.family()}; font-size: {self.bot_font.pointSize()}px;"'
        self.chatLog.append(f'<p {set_style}>AI: {chunk_text}</p>')

        # Save to conversation thread if available
        if self.memory_component and self.conversation_thread:
            self.conversation_thread.add_message(chunk_text, "ai")
            self.conversation_thread.save_thread_metadata()

    def handle_response_complete(self):
        """Handles AI response completion"""
        self.statusBar().showMessage("Response generated", 3000)

    def handle_error(self, err):
        """Handles worker errors."""
        self.show_error_message(f"Error: {err}")
        self.statusBar().showMessage("Error occurred", 3000)

    def show_error_message(self, message):
        """Displays an error message."""
        self.chatLog.append(f'<p style="color: red;">Error: {message}</p>')

    def eventFilter(self, source, event):
        """Filters events."""
        if (source is self.inputTextBox and event.type() == event.Type.KeyPress
                and event.key() == Qt.Key.Key_Return and event.modifiers() == Qt.KeyboardModifier.ControlModifier):
            self.handle_send()
            return True
        return super().eventFilter(source, event)
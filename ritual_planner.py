from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QComboBox, QPushButton,
                             QTextEdit, QLabel, QLineEdit, QFormLayout, QDialogButtonBox,
                             QDialog, QDateTimeEdit, QListWidget)
from PyQt6.QtCore import Qt, QDateTime
from agent import MagicalAgent, RitualType


class RitualPlannerDialog(QDialog):
    def __init__(self, agent, parent=None):
        super().__init__(parent)
        self.agent = agent
        self.setWindowTitle("Ritual Planner")
        self.resize(500, 400)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        form_layout = QFormLayout()

        # Intention
        self.intention_input = QTextEdit()
        self.intention_input.setPlaceholderText("Enter your magical intention...")
        form_layout.addRow("Intention:", self.intention_input)

        # Ritual type
        self.ritual_type = QComboBox()
        for ritual in RitualType:
            self.ritual_type.addItem(ritual.value.title(), ritual.value)
        form_layout.addRow("Ritual Type:", self.ritual_type)

        # Timing
        self.timing = QDateTimeEdit(QDateTime.currentDateTime())
        form_layout.addRow("Timing:", self.timing)

        # Tools
        self.tools_input = QLineEdit()
        self.tools_input.setPlaceholderText("Enter tools separated by commas...")
        form_layout.addRow("Tools:", self.tools_input)

        # Notes
        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Additional notes...")
        form_layout.addRow("Notes:", self.notes_input)

        layout.addLayout(form_layout)

        # Correspondences preview
        self.correspondences_label = QLabel("Correspondences will appear here...")
        layout.addWidget(self.correspondences_label)

        # Update correspondences button
        self.update_button = QPushButton("Update Correspondences")
        self.update_button.clicked.connect(self.update_correspondences)
        layout.addWidget(self.update_button)

        # Dialog buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def update_correspondences(self):
        """Update the suggested correspondences based on current input."""
        intention = self.intention_input.toPlainText()
        ritual_type = self.ritual_type.currentData()

        if intention:
            correspondences = self.agent.suggest_correspondences(intention, ritual_type)

            # Format the correspondences for display
            text = "<b>Suggested Correspondences:</b><br>"
            for category, items in correspondences.items():
                if items:
                    text += f"<b>{category.title()}:</b> {', '.join(items)}<br>"

            self.correspondences_label.setText(text)

    def accept(self):
        """Create the ritual plan when accepted."""
        intention = self.intention_input.toPlainText()
        ritual_type = self.ritual_type.currentData()
        timing = self.timing.dateTime().toString(Qt.DateFormat.ISODate)
        tools = [t.strip() for t in self.tools_input.text().split(",") if t.strip()]
        notes = self.notes_input.toPlainText()

        if intention:
            # Create the ritual plan
            self.ritual_plan = self.agent.plan_ritual(
                intention=intention,
                ritual_type=ritual_type,
                timing=timing,
                tools=tools,
                notes=notes
            )
            super().accept()

    def get_ritual_plan(self):
        """Return the created ritual plan."""
        if hasattr(self, 'ritual_plan'):
            return self.ritual_plan
        return None
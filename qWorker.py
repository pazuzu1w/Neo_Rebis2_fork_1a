# qWorker.py - Corrected
from PyQt6.QtCore import QThread, pyqtSignal


class ChatWorker(QThread):
    stream_signal = pyqtSignal(str)  # Signal for streaming responses
    error_signal = pyqtSignal(str)  # Signal for errors
    done_signal = pyqtSignal()  # Signal for completion

    def __init__(self, model_component, message):
        super().__init__()
        self.model_component = model_component
        self.message = message

    def run(self):
        try:
            # Send the message to the model
            response_text = self.model_component.send_message(self.message)
            print(f"ChatWorker received response: {response_text}")

            # Emit the response text (even if it's an error message)
            self.stream_signal.emit(response_text)
            self.done_signal.emit()  # Always emit done when finished

        except Exception as e:
            print(f"ChatWorker error: {e}")
            self.error_signal.emit(str(e))
            self.done_signal.emit()
# qWorker.py - updated
from PyQt6.QtCore import QThread, pyqtSignal


class ChatWorker(QThread):
    stream_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)
    done_signal = pyqtSignal()

    def __init__(self, model_component, message):
        super().__init__()
        self.model_component = model_component
        self.message = message

    def run(self):
        try:
            # Send the message to the model
            response = self.model_component.send_message(self.message)

            if response and hasattr(response, 'text') and response.text:
                self.stream_signal.emit(response.text)
            else:
                # Handle case where response is not a proper model response
                text = str(response) if response else "[No response received]"
                self.stream_signal.emit(text)

            self.done_signal.emit()

        except Exception as e:
            self.error_signal.emit(str(e))
            self.done_signal.emit()
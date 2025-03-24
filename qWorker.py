# qWorker.py
from PyQt6.QtCore import QThread, pyqtSignal


class ChatWorker(QThread):
    """Worker thread for handling AI chat responses without freezing the UI."""

    stream_signal = pyqtSignal(str)  # Signal for streaming partial responses
    error_signal = pyqtSignal(str)  # Signal for reporting errors
    done_signal = pyqtSignal()  # Signal for completion notification

    def __init__(self, model_component, query_text):
        super().__init__()
        self.model_component = model_component
        self.query_text = query_text
        self.response_buffer = ""

    def run(self):
        """Run the worker thread to get AI response."""
        if not self.model_component:
            self.error_signal.emit("Model component not available")
            return

        try:
            # Check if streaming is supported
            if hasattr(self.model_component, 'generate_response_stream'):
                # Use streaming API
                for chunk in self.model_component.generate_response_stream(self.query_text):
                    if chunk:
                        self.stream_signal.emit(chunk)

                # Signal completion
                self.done_signal.emit()
            else:
                # Fallback to non-streaming API
                response = self.model_component.send_message(self.query_text)
                if response:
                    self.stream_signal.emit(response)
                    self.done_signal.emit()
                else:
                    self.error_signal.emit("Empty response received")

        except Exception as e:
            self.error_signal.emit(str(e))
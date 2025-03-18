from PyQt6.QtCore import QThread, pyqtSignal

class ChatWorker(QThread):
    stream_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)
    done_signal = pyqtSignal()

    def __init__(self, chat, message):
        super().__init__()
        self.chat = chat
        self.message = message


    def run(self):
        try:
            response = self.chat.send_message(self.message)
            if response and response.text:
                self.stream_signal.emit(response.text)
            else:
                self.stream_signal.emit("[No response received]")
            self.done_signal.emit() #Emit done signal

        except Exception as e:
            self.error_signal.emit(str(e))
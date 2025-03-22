# main.py - updated
import sys
from PyQt6.QtWidgets import QApplication
from gui import ChatWindow
from engine_core import EngineCore
from memory_component import MemoryComponent
from model import ModelComponent
from _logging import Logger
from config_manager import ConfigManager
from tools_component import ToolsComponent
from error_handler import ErrorHandler


def main():
    # Create the application
    app = QApplication(sys.argv)

    # Create and initialize the engine
    engine = EngineCore()

    # Create and register components
    logger = Logger()
    engine.register_component("logger", logger)

    config = ConfigManager()
    engine.register_component("config", config)

    error_handler = ErrorHandler()
    error_handler.install_global_handler()
    engine.register_component("error_handler", error_handler)

    memory = MemoryComponent()
    engine.register_component("memory", memory)

    tools = ToolsComponent()
    engine.register_component("tools", tools)

    model = ModelComponent()
    engine.register_component("model", model)

    # Initialize all components
    engine.initialize()

    # Create and show the UI
    window = ChatWindow(engine)
    window.show()

    # Start the application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
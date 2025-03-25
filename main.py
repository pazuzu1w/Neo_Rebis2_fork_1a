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

    # Create and initialize the engine
    engine = EngineCore()
    print("Engine initialized")

    # Create and register components

    engine.register_component("logger", engine.logger)
    engine.logger.info("Logger initialized")

    #use default config file
    engine.register_component("config", engine.config_manager)
    engine.logger.info("ConfigManager initialized")

    error_handler = ErrorHandler(engine.logger)
    error_handler.install_global_handler()
    engine.register_component("error_handler", error_handler)
    engine.logger.info("ErrorHandler initialized")

    memory = MemoryComponent()
    engine.register_component("memory", memory)
    engine.logger.info("MemoryComponent initialized")

    tools = ToolsComponent()
    engine.register_component("tools", tools)
    engine.logger.info("ToolsComponent initialized")

    model = ModelComponent()
    engine.register_component("model", model)
    engine.logger.info("ModelComponent initialized")

    # Initialize all components
    engine.initialize()
    engine.logger.info("All components initialized")

    # Create the application
    app = QApplication(sys.argv)
    engine.logger.info("QApplication created")

    # Create and show the UI
    window = ChatWindow(engine)
    window.show()
    engine.logger.info("ChatWindow created and shown")

    # Start the application
    sys.exit(app.exec())
    engine.logger.info("Application exited")

if __name__ == "__main__":
    main()

# engine_core.py
import os
from _logging import Logger
from config_manager import ConfigManager


class EngineCore:
    def __init__(self):
        self.components = {}

        # Create a proper config path
        base_dir = os.path.dirname(os.path.abspath(__file__))
        config_dir = os.path.join(base_dir, "config")
        os.makedirs(config_dir, exist_ok=True)
        config_path = os.path.join(config_dir, "config.json")

        # Create the file if it doesn't exist
        if not os.path.exists(config_path):
            with open(config_path, 'w') as f:
                f.write('{}')  # Initialize with empty JSON object

        self.config_manager = ConfigManager(config_path)
        self.logger = Logger()

    def register_component(self, name, component):
        """Register a component with the engine"""
        self.components[name] = component
        if hasattr(component, 'set_engine'):
            component.set_engine(self)
        self.logger.info(f"Registered component: {name}")

    def get_component(self, name):
        """Get a component by name"""
        if name in self.components:
            return self.components[name]
        self.logger.warning(f"Component not found: {name}")
        return None

    def initialize(self):
        """Initialize all components"""
        for name, component in self.components.items():
            if hasattr(component, 'initialize'):
                self.logger.info(f"Initializing component: {name}")
                component.initialize()

    def shutdown(self):
        """Shutdown all components"""
        for name, component in self.components.items():
            if hasattr(component, 'shutdown'):
                self.logger.info(f"Shutting down component: {name}")
                component.shutdown()
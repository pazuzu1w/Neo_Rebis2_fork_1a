# engine_core.py
from _logging import Logger

from pywin.scintilla.config import ConfigManager


class EngineCore:
    def __init__(self):
        self.components = {}
        # Use the positional parameter 'f' instead of 'config_file'
        config_path = "path/to/your/config.json"  # or whatever path is appropriate
        self.config_manager = ConfigManager(f=config_path)
        # or simply: self.config_manager = ConfigManager(config_path)
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
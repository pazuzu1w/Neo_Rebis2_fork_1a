# component.py
class Component:
    def __init__(self, name):
        self.name = name
        self.engine = None

    def set_engine(self, engine):
        """Set the reference to the engine"""
        self.engine = engine

    def initialize(self):
        """Initialize the component"""
        pass

    def shutdown(self):
        """Shutdown the component"""
        pass
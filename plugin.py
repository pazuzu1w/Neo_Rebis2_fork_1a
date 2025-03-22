# plugin.py
class Plugin:
    def __init__(self, name, version="0.1"):
        self.name = name
        self.version = version

    def initialize(self, engine):
        """Initialize the plugin"""
        pass

    def shutdown(self):
        """Shutdown the plugin"""
        pass


# plugin_manager.py
import os
import importlib


class PluginManager:
    def __init__(self, plugin_dir="plugins"):
        self.plugin_dir = plugin_dir
        self.plugins = {}

    def discover_plugins(self):
        """Discover plugins in the plugin directory"""
        if not os.path.exists(self.plugin_dir):
            os.makedirs(self.plugin_dir)

        for filename in os.listdir(self.plugin_dir):
            if filename.endswith(".py") and not filename.startswith("_"):
                module_name = filename[:-3]
                try:
                    module = importlib.import_module(f"{self.plugin_dir}.{module_name}")
                    if hasattr(module, "plugin_main"):
                        plugin = module.plugin_main()
                        self.plugins[plugin.name] = plugin
                except Exception as e:
                    print(f"Error loading plugin {module_name}: {e}")

    def initialize_plugins(self, engine):
        """Initialize all plugins"""
        for name, plugin in self.plugins.items():
            try:
                plugin.initialize(engine)
                print(f"Initialized plugin: {name} v{plugin.version}")
            except Exception as e:
                print(f"Error initializing plugin {name}: {e}")

    def shutdown_plugins(self):
        """Shutdown all plugins"""
        for name, plugin in self.plugins.items():
            try:
                plugin.shutdown()
                print(f"Shutdown plugin: {name}")
            except Exception as e:
                print(f"Error shutting down plugin {name}: {e}")
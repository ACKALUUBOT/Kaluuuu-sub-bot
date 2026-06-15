
import os
import glob
import importlib

# Yeh function plugins folder ki saari .py files ko automatic load karega
def load_plugins():
    # Current directory (plugins folder) ki path nikalna
    plugin_path = os.path.dirname(__file__)
    
    # Saari .py files ko dhundna (__init__.py ko chhod kar)
    files = glob.glob(os.path.join(plugin_path, "*.py"))
    
    for file in files:
        if not file.endswith("__init__.py"):
            # File name nikalna (e.g., 'start' ya 'story')
            module_name = os.path.basename(file)[:-3]
            
            # Module ko dynamic import karna
            try:
                importlib.import_module(f"plugins.{module_name}")
                print(f"✅ Plugin Loaded: {module_name}")
            except Exception as e:
                print(f"❌ Failed to load plugin {module_name}: {e}")

# Bot start hote hi load karne ke liye
load_plugins()

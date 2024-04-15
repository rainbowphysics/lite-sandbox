# lite-sandbox

An experimental Python package for sandboxing plugin scripts inside of Python by controlling imports and access to risky modules.

## Installation
Simply `pip install lite-sandbox`

PyPI page: https://pypi.org/project/lite-sandbox/

## Usage
```python
import os
from sandbox import exec_sandboxed

PLUGINS_PATH = 'plugins'

plugin_paths = []
for root, dirs, files in os.walk(PLUGINS_PATH, topdown=True):
    for filename in files:
        if filename.endswith('.py') and filename != '__init__.py' and filename != '__main__.py':
            plugin_paths.append(os.path.join(root, filename))

loaded_plugins = []
for plugin_path in plugin_paths:
    try:
        module = exec_sandboxed(plugin_path)
        if module:
            loaded_plugins.append(module)
    except:
        continue
```

## Current Status
Currently in the initial planning and testing phase. This is nothing more than a proof of concept and shouldn't be used in production
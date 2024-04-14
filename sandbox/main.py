import pkgutil
import importlib
import logging
import os
from types import ModuleType
from typing import Callable

ALLOWED_PACKAGES = ['math']

ROOT_PATH = os.path.dirname(os.path.dirname(__file__))
PLUGINS_PATH = os.path.join(ROOT_PATH, 'test')


class PluginMetadata:
    def __init__(self, name: str, author: str):
        self.name = name
        self.author = author

    def get_info(self) -> str:
        return f'{self.name} by {self.author}'

    def __str__(self):
        return self.get_info()


PluginMainType = Callable[[None], None]
PluginListType = list[tuple[ModuleType, PluginMetadata]]


def strattr_or_default(module, attr, default):
    if hasattr(module, attr):
        return str(getattr(module, attr)).strip()

    return default


def load_plugin(script_path, verbose=True) -> tuple[ModuleType, PluginMetadata] | None:
    script = os.path.basename(script_path)
    module_name = os.path.splitext(script)[0]
    if verbose:
        print(f"Loading plugin: {module_name}")
    try:
        # TODO convert from importlib.util to pkgutil
        spec = importlib.util.spec_from_file_location(module_name, script_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Get script directives/metadata variables
        plugin_name = strattr_or_default(module, 'NAME', module_name)
        author = strattr_or_default(module, 'AUTHOR', '')

        if verbose:
            success_message = f'Successfully loaded {plugin_name}'
            if author is not None:
                success_message += f' by {author}'

        return module, PluginMetadata(plugin_name, author)

    except Exception as e:
        logging.error(f"Error loading plugin '{script}': {e}")


# Get plugin scripts from folder, mostly used for testing
def get_plugins() -> list[str]:
    files = os.listdir(PLUGINS_PATH)

    python_files = [f for f in files if f.endswith('.py') and f != '__init__.py']
    if not python_files:
        logging.warning(f'No Python scripts found in {os.path.relpath(PLUGINS_PATH, ROOT_PATH)} folder.')
        return []

    python_files = sorted(python_files)

    # Convert to absolute paths and return
    return [os.path.normcase(os.path.join(PLUGINS_PATH, filename)) for filename in python_files]


def load_plugins(verbose=True) -> PluginListType:
    # Get all plugins
    if not os.path.exists(PLUGINS_PATH):
        os.mkdir(PLUGINS_PATH)

    plugin_paths = get_plugins()

    # Append each successfully loaded plugin to the output
    plugins = []
    for path in plugin_paths:
        load_result = load_plugin(path, verbose=verbose)
        if load_result is None:
            continue
        plugins.append(load_result)

    return plugins


if __name__ == '__main__':
    print(load_plugins())

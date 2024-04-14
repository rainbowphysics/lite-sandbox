import builtins
import inspect
import pkgutil
import importlib
import sys
from importlib import abc as iabc
import logging
import os
from types import ModuleType
from typing import Callable

ALLOWED_PACKAGES = ['math']

ROOT_PATH = os.path.dirname(os.path.dirname(__file__))
PLUGINS_PATH = os.path.join(ROOT_PATH, 'test')
BASE_MODULE = sys.modules[__name__]


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

    # Define a custom loader to control imports


def restricted(name):
    def restricted_func(*args, **kwargs):
        raise ImportError("Using {} is not allowed".format(name))

    return restricted_func


def restricted_import(real_import):
    def import_func(name, globals=None, locals=None, fromlist=(), level=0):
        # Silently fail to automatically import _io
        if name == '_io':
            return

        if name in ALLOWED_PACKAGES:
            del builtins.__import__
            import_result = real_import(name, globals, locals, fromlist, level)
            builtins.__import__ = restricted_import
            return import_result
        else:
            raise ImportError("Importing {} is not allowed".format(name))

    return import_func


num_execs = 0


def restricted_exec(real_exec):
    def exec_func(code, globals=None, locals=None):
        caller_file = inspect.stack()[1].filename
        if os.path.isfile(caller_file):
            if not os.path.samefile(caller_file, __file__):
                raise PermissionError("exec() is not allowed from this context")

        return real_exec(code, globals, locals)

    return exec_func


class RestrictedLoader(iabc.Loader):
    def __init__(self, spec, real_loader):
        self.spec = spec
        self.real_loader = real_loader

    def exec_module(self, module):
        real_import = builtins.__import__
        real_open = builtins.open
        real_exec = builtins.exec

        # Use builtins module to access the built-in namespace
        builtins.__import__ = restricted_import(real_import)
        builtins.open = restricted('open')
        builtins.exec = restricted_exec(real_exec)

        global num_execs
        num_execs = 10

        self.real_loader.exec_module(module)

        # Reset the import hook to default after execution
        builtins.__import__ = real_import
        builtins.open = real_open
        builtins.exec = real_exec


def load_plugin(script_path, verbose=True) -> tuple[ModuleType, PluginMetadata] | None:
    script = os.path.basename(script_path)
    module_name = os.path.splitext(script)[0]
    if verbose:
        print(f"Loading plugin: {module_name}")
    try:
        # TODO convert from importlib.util to pkgutil
        spec = importlib.util.spec_from_file_location(module_name, script_path)
        module = importlib.util.module_from_spec(spec)

        # Set the custom loader
        spec.loader = RestrictedLoader(spec, spec.loader)

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

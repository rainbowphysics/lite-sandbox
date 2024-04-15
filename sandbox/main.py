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

ALLOWED_PACKAGES = ['math', 'collections', 'faulthandler', '_pytest.fixtures']

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


def restricted(name):
    def restricted_func(*args, **kwargs):
        raise PermissionError("Using {} is not allowed".format(name))

    return restricted_func


def restricted_import(real_import):
    def import_func(name, globals=None, locals=None, fromlist=(), level=0):
        caller_file = inspect.stack()[1].filename
        relpath = os.path.relpath(caller_file, ROOT_PATH)
        if relpath.startswith('.venv') or relpath.startswith('..'):
            builtins.__import__ = real_import
            import_result = real_import(name, globals, locals, fromlist, level)
            builtins.__import__ = import_func
            return import_result

        # Silently fail to automatically import _io
        if name == '_io':
            return

        if name in ALLOWED_PACKAGES:
            builtins.__import__ = real_import
            import_result = real_import(name, globals, locals, fromlist, level)
            builtins.__import__ = import_func
            return import_result
        else:
            raise ImportError('Importing {} is not allowed'.format(name))

    return import_func


def restricted_exec(real_exec):
    def exec_func(code, globals=None, locals=None):
        caller_file = inspect.stack()[1].filename
        if os.path.isfile(caller_file):
            if not os.path.samefile(caller_file, __file__):
                raise PermissionError('Using exec is not allowed')

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

        self.real_loader.exec_module(module)

        # Reset the import hook to default after execution
        builtins.__import__ = real_import
        builtins.open = real_open
        builtins.exec = real_exec


def exec_sandboxed(arg, globals=None, locals=None):
    if isinstance(arg, str):
        if os.path.exists(arg):  # Treat as path
            script = os.path.basename(arg)
            module_name = os.path.splitext(script)[0]

            spec = importlib.util.spec_from_file_location(module_name, arg)

            # Set the custom loader
            module = importlib.util.module_from_spec(spec)
        else:  # Treat as source code TODO
            pass
    elif isinstance(arg, ModuleType):
        module = arg
        spec = module.__spec__
    else:
        raise ValueError('Invalid input to exec_sandboxed')
        return

    spec.loader = RestrictedLoader(spec, spec.loader)
    spec.loader.exec_module(module)
    return module


def __load_plugin(script_path, verbose=True) -> tuple[ModuleType, PluginMetadata] | None:
    script = os.path.basename(script_path)
    module_name = os.path.splitext(script)[0]
    try:
        # TODO convert from importlib.util to pkgutil
        spec = importlib.util.spec_from_file_location(module_name, script_path)
        module = importlib.util.module_from_spec(spec)

        exec_sandboxed(module)

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
def __get_plugins() -> list[str]:
    plugin_paths = []
    for root, dirs, files in os.walk(PLUGINS_PATH, topdown=True):
        for filename in files:
            if filename == 'plugin.py':
                plugin_paths.append(os.path.join(root, filename))

    if not plugin_paths:
        logging.warning(f'No Python scripts found in {os.path.relpath(PLUGINS_PATH, ROOT_PATH)} folder.')
        return []

    plugin_paths = sorted(plugin_paths, key=os.path.basename)

    return plugin_paths


def __load_plugins(verbose=True) -> PluginListType:
    # Get all plugins
    if not os.path.exists(PLUGINS_PATH):
        os.mkdir(PLUGINS_PATH)

    plugin_paths = __get_plugins()

    # Append each successfully loaded plugin to the output
    plugins = []
    for path in plugin_paths:
        load_result = __load_plugin(path, verbose=verbose)
        if load_result is None:
            continue
        plugins.append(load_result)

    return plugins


if __name__ == '__main__':
    print(__load_plugins())

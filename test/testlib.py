import inspect
import os
import sys
from io import StringIO

from sandbox import load_plugin

import logging
import sys

root = logging.getLogger()
root.setLevel(logging.DEBUG)

def try_plugin(script_name='plugin.py'):
    real_stdout = sys.stdout
    real_stderr = sys.stderr

    mock_stdout = StringIO()
    mock_stderr = StringIO()
    sys.stdout = mock_stdout
    sys.stderr = mock_stderr
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(logging.WARNING)
    root.addHandler(stdout_handler)
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setLevel(logging.ERROR)
    root.addHandler(stderr_handler)
    plugin_path = os.path.join(os.path.dirname(inspect.stack()[1].filename), script_name)
    load_plugin(plugin_path)

    sys.stdout = real_stdout
    sys.stderr = real_stderr

    return mock_stdout.getvalue(), mock_stderr.getvalue()

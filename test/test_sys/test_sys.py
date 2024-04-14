from ..testlib import try_plugin


def test():
    stdout, stderr = try_plugin()
    assert stderr.replace('\n', '').endswith('Importing sys is not allowed')

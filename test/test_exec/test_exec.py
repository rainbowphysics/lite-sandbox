from ..testlib import try_plugin


def test():
    stdout, stderr = try_plugin()
    assert stderr.replace('\n', '').endswith('Using exec is not allowed')

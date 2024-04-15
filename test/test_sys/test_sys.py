from ..testlib import try_plugin


def test():
    try:
        try_plugin()
        assert False
    except ImportError:
        assert True
    except Exception as e:
        assert e is None

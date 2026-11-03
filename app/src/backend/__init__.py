import config


def make_backend():
    """Give main.py the fake or real backend, based on config.USE_FAKE_BACKEND."""
    if config.USE_FAKE_BACKEND:
        from backend.fake_backend import FakeBackend
        return FakeBackend()
    from backend.serial_backend import SerialBackend
    return SerialBackend(config.SERIAL_PORT, config.SERIAL_BAUD)
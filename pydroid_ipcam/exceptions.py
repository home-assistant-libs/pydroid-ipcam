"""PyDroidIPCam excpetions."""


class PyDroidIPCamException(Exception):
    """Base exception for PyDroidIPCam."""


class Unauthorized(PyDroidIPCamException):
    """Username or password is incorrect."""


class CannotConnect(PyDroidIPCamException):
    """Exception raised when failed to connect the client."""

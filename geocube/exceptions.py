"""
This contains exceptions for GeoCube.
"""


class GeoCubeError(RuntimeError):
    """Base GeoCube exception class."""


class VectorDataError(GeoCubeError):
    """This is for errors in the vector data passed into GeoCube."""

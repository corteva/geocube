"""Top-level package for geocube."""

__author__ = """Geocube Contributors"""
__email__ = "alansnow21@gmail.com"

import importlib.metadata

from geocube._show_versions import show_versions  # noqa

__version__ = importlib.metadata.version(__package__)

"""Import uppd functions."""

from __future__ import absolute_import

from importlib.metadata import PackageNotFoundError, version
from uppd.uppd import candidate

try:
    __version__ = version("uppd")
except PackageNotFoundError:
    pass

__all__ = ('candidate',
)

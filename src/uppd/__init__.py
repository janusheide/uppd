"""Import uppd functions."""

from __future__ import absolute_import

from importlib.metadata import PackageNotFoundError, version

from uppd.uppd import (
    find_latest_version, get_package_info, set_version, set_versions,
    upgrade_requirements,
)

try:
    __version__ = version("uppd")
except PackageNotFoundError:
    pass

__all__ = (
    "set_version",
    "set_versions",
    "get_package_info",
    "find_latest_version",
    "upgrade_requirements",
)

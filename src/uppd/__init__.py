
# Copyright (c) 2020, Janus Heide.
# All rights reserved.
#
# Distributed under the "BSD 3-Clause License", see LICENSE.txt.

"""Import uppd functions."""

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

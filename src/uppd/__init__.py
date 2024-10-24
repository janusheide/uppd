# Copyright (c) 2024, Janus Heide.
# All rights reserved.
#
# Distributed under the "BSD 3-Clause License", see LICENSE.txt.

"""Import uppd functions."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("uppd")
except PackageNotFoundError:
    pass

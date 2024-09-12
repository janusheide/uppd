..  Copyright (c) 2020, Janus Heide.
..  All rights reserved.
..
.. Distributed under the "BSD 3-Clause License", see LICENSE.rst.


Update Python Project Dependencies (UPPD)
========

.. image:: https://github.com/janusheide/uppd/actions/workflows/unittests.yml/badge.svg
    :target: https://github.com/janusheide/uppd/actions/workflows/unittests.yml
    :alt: Unit tests

Update dependencies and optional dependencies in pyproject.toml.


Getting Started
---------------

::
    pip install uppd
    uppd --help

Logging
-------

Supports standard log levels; DEBUG, INFO, WARING, ERROR, CRITICAL, and writing
log to a file.

Set the log level to ``debug``::

    python boil --log-level=DEBUG test

Set the log level to ``debug`` and redirect output from executed commands to
``bar.log``::

    python boil --log-level=DEBUG test >> bar.log

Set the log level to ``debug`` and redirect output from executed commands to
``bar.log`` and log information to ``foo.log``::

    python boil --log-level=DEBUG --log-file=foo.log test >> bar.log

Set the log level to ``debug`` and redirect output from executed commands and
log information to ``foo.log``::

    python boil --log-level=DEBUG --log-file=foo.log test >> foo.log

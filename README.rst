..  Copyright (c) 2020, Janus Heide.
..  All rights reserved.
..
.. Distributed under the "BSD 3-Clause License", see LICENSE.rst.


Update Python Project Dependencies (UPPD)
=========================================

.. image:: https://github.com/janusheide/uppd/actions/workflows/unittests.yml/badge.svg
    :target: https://github.com/janusheide/uppd/actions/workflows/unittests.yml
    :alt: Unit tests

Update dependencies and optional dependencies in pyproject.toml.


Getting Started
---------------

Install and run::

    pip install uppd
    uppd --help


Basic Usage
-----------

Set inputs and output files::

    uppd -i pyproject.toml dev/pyproject.toml
    uppd -i pyproject.toml dev/pyproject.toml -o pyproject.toml.updated

Skip dependencies::

    uppd --skip foo bar

Allow pre releases to upgrade::

    uppd --pre foo bar


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


Development
-----------

Install run tests and release::

    python boil.py setup
    python boil.py lint
    python boil.py test
    python boil.py release

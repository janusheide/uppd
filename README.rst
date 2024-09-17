..  Copyright (c) 2020, Janus Heide.
..  All rights reserved.
..
.. Distributed under the "BSD 3-Clause License", see LICENSE.rst.

Update Python Project Dependencies (UPPD)
=========================================

.. image:: https://github.com/janusheide/uppd/actions/workflows/unittests.yml/badge.svg
    :target: https://github.com/janusheide/uppd/actions/workflows/unittests.yml
    :alt: Unit tests

.. image:: https://img.shields.io/pypi/pyversions/uppd
   :alt: PyPI - Python Version

.. image:: https://img.shields.io/librariesio/github/janusheide/bouillon
   :alt: Libraries.io dependency status for GitHub repo


Update dependencies and optional dependencies in pyproject.toml files.

Getting Started
---------------

Install and run::

    pip install uppd
    uppd --help

Usage
-----

Set inputs and output files::

    uppd -i pyproject.toml dev/pyproject.toml
    uppd -i pyproject.toml dev/pyproject.toml -o pyproject.toml.updated

Skip dependencies::

    uppd --skip foo bar

Allow upgrade to pre releases::

    uppd --pre foo bar

Development
-----------

Setup, run tests and release::

    python boil.py setup
    python boil.py lint
    python boil.py test
    python boil.py release

Credits
-------

This project aims to enable a similar workflow as pur_ for requirements.txt files

.. _pur: https://github.com/alanhamlett/pip-update-requirements

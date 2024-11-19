..  Copyright (c) 2024, Janus Heide.
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

.. image:: https://img.shields.io/librariesio/github/janusheide/uppd
   :alt: Libraries.io dependency status for GitHub repo

Update dependencies and optional dependencies in ``pyproject.toml`` files based on
defined match operators.

This project aims to enable a similar workflow as pur_ does for ``requirements.txt`` files.


Getting Started
---------------

Install and run::

    pip install uppd
    uppd
    INFO: dlister==1.1.0 -> dlister==1.2.0
    INFO: pytest-aiohttp==1.0.0 -> pytest-aiohttp==1.0.5
    INFO: pytest==8.0.0 -> pytest==8.3.3

Set inputs and output files::

    uppd -i dev/pyproject.toml
    uppd -i pyproject.toml -o pyproject.toml.updated

Skip dependencies::

    uppd --skip foo bar

Allow upgrade to pre releases::

    uppd --pre foo bar

Print help::

    uppd --help

    usage: uppd [-h]
                [-i INFILE]
                [-o OUTFILE]
                [-m [{<,<=,==,>=,>,~=} ...]]
                [--skip [SKIP ...]]
                [--dev [DEV ...]]
                [--pre [PRE ...]]
                [--post [POST ...]]
                [--index-url INDEX_URL]
                [--log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}]
                [--log-file LOG_FILE]
                [--dry-run]
                [-v]

    Update Python Project Dependencies.

    options:
    -h, --help            show this help message and exit
    -i INFILE, --infile INFILE
                          path(s) to input file(s) (default: pyproject.toml)
    -o OUTFILE, --outfile OUTFILE
                            path(s) to output file(s). (default: [])
    -m [{<,<=,==,>=,>,~=} ...], --match-operators [{<,<=,==,>=,>,~=} ...]
                          operators to upgrade. (default: ['==', '<=', '~='])
    --skip [SKIP ...]     dependencies to skip upgrade. (default: [])
    --dev [DEV ...]       dependencies to upgrade to dev release. (default: [])
    --pre [PRE ...]       dependencies to upgrade to pre release. (default: [])
    --post [POST ...]     dependencies to upgrade to post release. (default: ['*'])
    --index-url INDEX_URL
                          base URL of the Python Package Index. (default: https://pypi.org)
    --log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                          logging level. (default: INFO)
    --log-file LOG_FILE   pipe loggining to file instead of stdout. (default: None)
    --dry-run             do not save changes to output file(s). (default: False)
    -v, --version         show program's version number and exit


The following settings (with defaults) can be set/overwritten in the ``infile``::

    [tool.uppd]
    match_operators = ["==", "<=", "~="]
    skip = []
    dev = []
    pre = []
    post = ["*"]
    index_url = "https://pypi.org"


Development
-----------

Setup, run tests and release::

    pip install -e .[dev]
    brundle
    pytest
    bouillon release

Credits
-------

This project aims to enable a similar workflow as pur_ for requirements.txt files, and essentially exists because pur_ (at the time of writing) does not support upgrading dependencies in ``pyproject.toml`` files.

.. _pur: https://github.com/alanhamlett/pip-update-requirements

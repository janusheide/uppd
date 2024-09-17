# Copyright (c) 2020, Janus Heide.
# All rights reserved.
#
# Distributed under the "BSD 3-Clause License", see LICENSE.txt.

"""Command Line Interface (CLI) for project interaction.

Run various commands, such as; test, build, release on your project. You should
modify the steps that are relevant for your project, and the cli such that it
reflects those steps.
"""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser, Namespace
from importlib import util
from typing import Callable

# Modules that are not part of 'standard' Python is only installed if they can
# be found, this allows us to run the setup step where they are installed
# without importing the modules we are about to install.
if util.find_spec("bouillon") is not None:
    import bouillon


logger = logging.getLogger(__name__)


def setup(*, dry_run: bool, **kwargs) -> None:
    """Install dependencies."""
    logger.info("Installing dependencies")

    if dry_run:
        exit(0)

    # NOTE For your project instead add bouillon to requirements.txt.
    subprocess.run(["pip", "install", "-e", ".[dev]"], **kwargs)


def lint(
    isort: bool = True,
    liccheck: bool = False,
    mypy: bool = True,
    ruff: bool = True,
    **kwargs,
) -> None:
    """Run linters."""
    if isort:
        bouillon.run(["isort", "."], **kwargs)

    if liccheck:
        bouillon.run(["liccheck"], **kwargs)

    if mypy:
        bouillon.run(["mypy", "src"], **kwargs)

    if ruff:
        bouillon.run(["ruff", "check"], **kwargs)


def test(
    *,
    test_files: bool = True,
    unit_tests: bool = True,
    **kwargs,
) -> None:
    """Run tests."""
    # if test_files:
    #     if not bouillon.check_for_test_files(
    #         os.path.join('src', bouillon.git.repository_name()),
    #             os.path.join('test', bouillon.git.repository_name())):
    #         exit(1)

    # https://docs.pytest.org/en/latest/
    # https://pytest-cov.readthedocs.io/en/latest/
    if unit_tests:
        bouillon.run([
            "pytest",
            f'{os.path.join("test", "uppd")}',
            "--cov=uppd",
            "--cov-report",
            "term-missing",
            "--cov-fail-under=50",
            "--durations=5",
            "-vv",
            ],
            **kwargs)

def upgrade(**kwargs) -> None:
    """Upgrade the versions of the used modules."""
    bouillon.run(["uppd"], **kwargs)


def build(**kwargs) -> None:
    """Build distributeables."""
    logger.info("Building source and binary distributions")
    bouillon.run(["python", "-m", "build"], **kwargs)


def train(**kwargs) -> None:
    """Train a model."""
    logger.critical("train step not implemented.")


def clean(**kwargs) -> None:
    """Remove files and dirs created during build."""
    logger.info('Deleting "build" and "dist" directories.')
    shutil.rmtree("build", ignore_errors=True)
    shutil.rmtree("dist", ignore_errors=True)


def release(*, version: str, **kwargs) -> None:
    """Release the project."""
    if bouillon.run(["pysemver", "check", version]).returncode:
        logger.error("Provided version is not valid semver")
        exit(1)

    if not kwargs["dry_run"]:
        if bouillon.git.current_branch() != "main":
            logger.error("Only release from the main branch")
            exit(1)

        if not bouillon.git.working_directory_clean():
            logger.error("Unstaged changes in the working directory.")
            exit(1)

        if version in bouillon.git.tags():
            logger.error("Tag already exists.")
            exit(1)
    else:
        logger.debug("Skipped git status checks.")

    clean(**kwargs)
    lint(**kwargs)
    test(**kwargs)

    logger.debug("Edit the news file using default editor or nano.")
    EDITOR = os.environ.get("EDITOR", "nano")
    bouillon.run([EDITOR, "NEWS.rst"], **kwargs)
    bouillon.run(["git", "add", "NEWS.rst"], **kwargs)
    bouillon.run(["git", "commit", "-m", '"preparing release"'], **kwargs)

    logger.debug("Create an annotated tag, used by setuptools_scm.")
    bouillon.run(["git", "tag", "-a", f"{version}", "-m",
                  f"creating tag {version} for new release"], **kwargs)

    build(**kwargs)

    logger.debug("upload builds to pypi and push commit and tag to repo.")
    bouillon.run(["twine", "upload", "dist/*"], **kwargs)
    bouillon.run(["git", "push"], **kwargs)
    bouillon.run(["git", "push", "origin", f"{version}"], **kwargs)


def cli() -> Namespace:
    """Build the cli."""
    parser = ArgumentParser(
        description="Bouillon",
        formatter_class=ArgumentDefaultsHelpFormatter,
    )

    def _print_help(**kwargs):
        parser.print_help()

    parser.set_defaults(check=True, function=_print_help)

    parser.add_argument(
        "--dry-run", action="store_true", help="Perform a dry run.")
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICIAL"],
        default="WARNING", help="Set log level.")
    parser.add_argument(
        "--log-file", type=str, help="Set log file.")

    subparsers = parser.add_subparsers(help="Available sub commands")

    parser_setup = subparsers.add_parser(
        "setup",
        help="Setup installing dependencies, this will execute pip commands.")
    parser_setup.set_defaults(function=setup)

    parser_build = subparsers.add_parser("build", help="Build.")
    parser_build.set_defaults(function=build)

    parser_lint = subparsers.add_parser("lint", help="Run linters")
    parser_lint.set_defaults(function=lint)
    parser_lint.add_argument(
        "--no-isort", dest="isort", action="store_false",
        help="Do not run isort.")
    parser_lint.add_argument(
        "--no-liccheck", dest="liccheck", action="store_false",
        default=False,
        help="Do not check that licenses of all used modules. (Default disabled)")
    parser_lint.add_argument(
        "--no-mypy-check", dest="mypy", action="store_false",
        help="Do not perform mypy code analysis.")
    parser_lint.add_argument(
        "--no-ruff", dest="ruff", action="store_false",
        help="Do not check with ruff.")

    parser_test = subparsers.add_parser("test", help="Run tests")
    parser_test.set_defaults(function=test)
    parser_test.add_argument(
        "--no-test-files-check", dest="test_files", action="store_false",
        help="Do not check that for each source file there is a test file.")
    parser_test.add_argument(
        "--no-unit-tests", dest="unit_tests", action="store_false",
        help="Do not run unit tests.")

    parser_train = subparsers.add_parser("train", help="Train.")
    parser_train.set_defaults(function=train)

    parser_upgrade = subparsers.add_parser(
        "upgrade", help="upgrade all dependencies.")
    parser_upgrade.set_defaults(function=upgrade)

    parser_clean = subparsers.add_parser("clean", help="Clean temp files.")
    parser_clean.set_defaults(function=clean)

    parser_release = subparsers.add_parser("release", help="release me.")
    parser_release.add_argument("version", type=str,
                                help="release version.")
    parser_release.set_defaults(function=release)

    return parser.parse_args()


def run(*, function: Callable, log_level: str, log_file: str, **kwargs) -> None:
    """Setup logging and run a step."""
    logging.basicConfig(filename=log_file, level=log_level)
    if function != setup and util.find_spec("bouillon") is None:
        logger.error('Failed to import bouillon, run "boil setup" first.')
        exit(1)

    logger.debug(f'Running "{function.__name__}" step.')
    function(**kwargs)


if __name__ == "__main__":
    args = cli()
    run(**vars(args))

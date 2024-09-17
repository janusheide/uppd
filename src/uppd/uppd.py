# Copyright (c) 2020, Janus Heide.
# All rights reserved.
#
# Distributed under the "BSD 3-Clause License", see LICENSE.txt.

"""Update Python Project Dependencies.

Look through pyproject.toml and update dependencies and optional dependencies.
"""

from __future__ import annotations

import asyncio
from argparse import (
    ArgumentDefaultsHelpFormatter, ArgumentParser, FileType, Namespace,
)
from importlib.metadata import version
from itertools import zip_longest
from logging import basicConfig, getLevelName, getLogger
from pathlib import Path

from aiohttp import ClientSession
from packaging.requirements import Requirement, SpecifierSet
from packaging.specifiers import Specifier
from packaging.version import Version, parse
from tomlkit import dump, load

logger = getLogger(__name__)

def _find_in(sub_strings: list[str], string: str) -> str | None:
    """Return the first found sub_string in string."""
    return next((s for s in sub_strings if s in string), None)


async def get_package_info(package: str, session: ClientSession) -> dict:
    """Download package informations."""
    url = f"/simple/{package}/"
    headers = {"ACCEPT": "application/vnd.pypi.simple.v1+json"}

    async with session.get(url, headers=headers) as response:
        return await response.json()


def find_latest_version(
    package: dict, *, dev: bool, pre: bool, post: bool,
) -> str | None:
    """Find latets version of package."""
    versions = package["versions"]

    versions.sort(key=Version, reverse=True)
    for ver in versions:

        v = parse(ver)
        if not dev and v.is_devrelease:
            continue
        if not pre and v.is_prerelease:
            continue
        if not post and v.is_postrelease:
            continue

        for file in reversed(package["files"]):
            if (ver in file) and file["yanked"]:
                continue

            return ver

    return None


def set_version(
    specifier: Specifier, *, version: Version, match_operators: list[str],
) -> Specifier:
    """Set specifier version if operator matchecs."""
    if _find_in(match_operators, specifier.operator):
        return Specifier(f"{specifier.operator}{version}")

    return specifier


def set_versions(specifiers: SpecifierSet, **kwargs) -> SpecifierSet:
    """Set all versions for all specifiers that matches operatoers."""
    return SpecifierSet(
        ",".join([str(set_version(specifier=s, **kwargs)) for s in specifiers]))


async def upgrade_requirement(
    requirement: Requirement,
    *,
    session: ClientSession,
    match_operators: list[str],
    **kwargs: bool,
) -> Requirement:
    """Upgrade requirement."""
    if not requirement.specifier or not _find_in(
        match_operators, str(requirement.specifier),
    ):
        logger.debug(f"skipping {requirement} does not match {match_operators}.")
        return requirement

    updated = set_versions(
        requirement.specifier,
        version=find_latest_version(
            await get_package_info(requirement.name, session), **kwargs,
            ),
        match_operators=match_operators,
    )

    if requirement.specifier != updated:
        logger.info(f"{requirement} -> {requirement.name}{updated}")
        requirement.specifier = updated

    return requirement


async def upgrade_requirements(
    dependencies: list[str],
    *,
    skip: list[str],
    dev: list[str],
    pre: list[str],
    post: list[str],
    **kwargs,
) -> list[str]:
    """Upgrade requirements."""
    for e, d in enumerate(dependencies):
        requirement = Requirement(d)
        if requirement.name in skip:
            continue

        dependencies[e] = str(await upgrade_requirement(
            requirement,
            dev="*" in dev or requirement.name in dev,
            pre="*" in pre or requirement.name in pre,
            post="*" in post or requirement.name in post,
            **kwargs,
        ))

    return dependencies


def parse_arguments() -> Namespace:
    """Parse arguments."""
    parser = ArgumentParser(
        description="Update Python Project Dependencies.",
        formatter_class=ArgumentDefaultsHelpFormatter)

    parser.add_argument(
        "-i", "--infile",
        nargs="*",
        default="pyproject.toml",
        type=FileType("r"),
        help="Path(s) to input file(s)")

    parser.add_argument(
        "-o", "--outfile",
        nargs="+",
        default=[],
        type=Path,
        help="Path(s) to output file(s), defaults to overwritting inputs files.",
        )

    parser.add_argument(
        "-m", "--match_operators", nargs="*", default=["==", "<=", "~="],
        choices=["<", "<=", "==", ">=", ">", "~="],
        help="operators to upgrade.")

    parser.add_argument(
        "--skip", nargs="*", default=[""],
        help="List of dependencies to skip upgrade.")

    parser.add_argument(
        "--dev", nargs="*", default=[""],
        help="List of dependencies to upgrade to dev release.")

    parser.add_argument(
        "--pre", nargs="*", default=[""],
        help="List of dependencies to upgrade to pre release.")

    parser.add_argument(
        "--post", nargs="*", default=["*"],
        help="List of dependencies to upgrade to post release.")

    parser.add_argument(
        "--dry-run", action="store_true",
        help="Pipe loggining to file instead of stdout.")

    parser.add_argument(
        "--index-url", default="https://pypi.org",
        help="Base URL of the Python Package Index.")

    parser.add_argument(
        "--log-level", default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level.")

    parser.add_argument(
        "--log-file",
        type=Path,
        help="Pipe loggining to file instead of stdout.")

    parser.add_argument("-v", "--version", action="version", version=version("uppd"))

    return parser.parse_args()


async def main(
    *,
    log_file: Path,
    log_level: str,
    infile: FileType,
    outfile: list[Path],
    index_url: str,
    dry_run: bool,
    **kwargs,
) -> None:
    """Main."""
    basicConfig(
        filename=log_file,
        level=getLevelName(log_level),
        format = "%(levelname)s: %(message)s",
    )

    infiles = infile if isinstance(infile, list) else [infile]
    if len(outfile) > len(infiles):
        logger.critical("More output files than input files.")
        exit(1)

    for ifile, ofile in zip_longest(infiles, outfile):

        data = load(ifile)
        project = data.get("project")
        if project is None:
            logger.critical(f"No project section in input file: {ifile}")
            exit(1)

        try:
            async with ClientSession(index_url) as session:
                if dependencies := project.get("dependencies"):
                    logger.info("[project.dependencies]:")
                    await upgrade_requirements(
                        dependencies, session=session, **kwargs,
                    )

                if optional_dep := project.get("optional-dependencies"):
                    for k, dependencies in optional_dep.items():
                        logger.info(f"[project.optional-dependencies.{k}]:")
                        await upgrade_requirements(
                            dependencies, session=session, **kwargs,
                        )

        except ValueError:
            logger.critical("Invalid index-url.")
            exit(1)

        if dry_run:
            continue

        if ofile:
            with Path(ofile).open("w") as out:
                dump(data, out)
                continue

        with Path(ifile.name).open("w") as out:
            dump(data, out)


def main_cli() -> None:
    """Main."""
    args = parse_arguments()
    asyncio.run(main(**vars(args)))


if __name__ == "__main__":
    main_cli()

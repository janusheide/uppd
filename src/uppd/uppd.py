# Copyright (c) 2024, Janus Heide.
# All rights reserved.
#
# Distributed under the "BSD 3-Clause License", see LICENSE.txt.

"""Update Python Project Dependencies.

Look through pyproject.toml and update dependencies and optional dependencies.
"""

from __future__ import annotations

import sys
from argparse import (
    ArgumentDefaultsHelpFormatter, ArgumentParser, FileType, Namespace,
)
from asyncio import gather, run
from importlib.metadata import version
from io import TextIOWrapper
from logging import basicConfig, getLevelName, getLogger
from pathlib import Path

from aiohttp import ClientSession
from packaging.requirements import Requirement, SpecifierSet
from packaging.specifiers import Specifier
from packaging.version import Version, parse
from tomlkit import dump, load
from tomlkit.exceptions import ParseError

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
    for ver in reversed(package["versions"]):
        v = parse(ver)

        if not dev and v.is_devrelease:
            continue
        if not pre and v.is_prerelease:
            continue
        if not post and v.is_postrelease:
            continue

        for file in reversed(package["files"]):
            if (ver in file["filename"]) and not file["yanked"]:
                return ver

    return None


def set_version(
    specifier: Specifier, *, version: Version, match_operators: list[str],
) -> Specifier:
    """Set specifier version if operator matchecs."""
    if specifier.operator in match_operators:
        return Specifier(f"{specifier.operator}{version}")

    return specifier


def set_versions(specifiers: SpecifierSet, **kwargs) -> SpecifierSet:
    """Set all versions for all specifiers that matches operatoers."""
    return SpecifierSet(
        ",".join([str(set_version(specifier=s, **kwargs)) for s in specifiers]))


async def fetch_requirement(
    requirement: Requirement,
    *,
    match_operators: list[str],
    session: ClientSession,
    dev: list[str],
    pre: list[str],
    post: list[str],
) -> Requirement:
    """Fetch requirement."""
    if version := find_latest_version(
        await get_package_info(requirement.name, session),
        dev="*" in dev or requirement.name in dev,
        pre="*" in pre or requirement.name in pre,
        post="*" in post or requirement.name in post,
    ):
        updated = set_versions(
            requirement.specifier,
            version=version,
            match_operators=match_operators,
        )

        if requirement.specifier != updated:
            logger.info(f"{requirement} -> {requirement.name}{updated}")
            requirement.specifier = updated

    return requirement


async def upgrade_requirement(
    requirement: Requirement,
    *,
    match_operators: list[str],
    skip: list[str],
    **kwargs,
) -> Requirement:
    """Upgrade requirement."""
    if requirement.name in skip:
        return requirement

    if not requirement.specifier or not _find_in(
        match_operators, str(requirement.specifier),
    ):
        logger.debug(f"skipping {requirement} does not match {match_operators}.")
        return requirement

    return await fetch_requirement(
        requirement, match_operators=match_operators, **kwargs)


async def upgrade_requirements(
    dependencies: list[str],
    **kwargs,
) -> None:
    """Upgrade requirements."""
    for e, dep in enumerate(await gather(
        *[(upgrade_requirement(Requirement(d), **kwargs)) for d in dependencies],
    )):
        dependencies[e] = str(dep)


def cli(args) -> Namespace:
    """Parse arguments."""
    parser = ArgumentParser(
        description="Update Python Project Dependencies.",
        formatter_class=ArgumentDefaultsHelpFormatter)

    parser.add_argument(
        "-i", "--infile",
        default="pyproject.toml",
        type=FileType("r+"),
        help="path(s) to input file(s)",
        )

    infile = parser.parse_args(["-i", "pyproject.toml"]).infile
    uppd_settings = load(infile).get("tool", {}).get("uppd", {})

    parser.add_argument(
        "-o", "--outfile",
        default=uppd_settings.get("outfile", infile),
        type=FileType("w"),
        help="path(s) to output file(s).",
        )

    parser.add_argument(
        "-m", "--match-operators", nargs="*",
        default=uppd_settings.get("match_operators", ["==", "<=", "~="]),
        choices=["<", "<=", "==", ">=", ">", "~="],
        help="operators to upgrade.")

    parser.add_argument(
        "--skip", type=str, nargs="*", default=uppd_settings.get("skip", []),
        help="dependencies to skip upgrade.")

    parser.add_argument(
        "--dev", type=str, nargs="*", default=uppd_settings.get("dev", []),
        help="dependencies to upgrade to dev release.")

    parser.add_argument(
        "--pre", type=str, nargs="*", default=uppd_settings.get("pre", []),
        help="dependencies to upgrade to pre release.")

    parser.add_argument(
        "--post", type=str, nargs="*", default=uppd_settings.get("post", ["*"]),
        help="dependencies to upgrade to post release.")

    parser.add_argument(
        "--index-url", type=str, default=uppd_settings.get("index_url", "https://pypi.org"),
        help="base URL of the Python Package Index.")

    parser.add_argument(
        "--log-level", default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="logging level.")

    parser.add_argument(
        "--log-file",
        type=Path,
        help="pipe loggining to file instead of stdout.")

    parser.add_argument(
        "--dry-run", action="store_true",
        help="do not save changes to output file(s).")

    parser.add_argument("-v", "--version", action="version", version=version("uppd"))

    return parser.parse_args(args)


async def main(
    *,
    log_file: Path,
    log_level: str,
    infile: TextIOWrapper,
    outfile: TextIOWrapper,
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

    try:
        data = load(infile)
    except ParseError:
        logger.critical(f"Error parsing input toml file: {infile}")
        exit(1)

    project = data.get("project")
    if project is None:
        logger.critical(f"No project section in input file: {infile}")
        exit(1)

    deps = [
        project.get("dependencies", []),
        *project.get("optional-dependencies", {}).values(),
    ]

    try:
        async with ClientSession(index_url) as session:
            await gather(
                *[upgrade_requirements(dep, session=session, **kwargs) for dep in deps])

    except ValueError:
        logger.critical("Invalid index-url.")
        exit(1)

    if dry_run:
        return

    outfile.seek(0)
    dump(data, outfile)


def main_cli() -> None:
    """Main."""
    run(main(**vars(cli(sys.argv[1:]))))


if __name__ == "__main__":
    main_cli()

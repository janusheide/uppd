"""Update Python Project Dependencies.

Look through pyproject.tomnl and update any dependencies and optional
dependencies defined with '=='.
"""

import asyncio
import sys
from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser, Namespace
from logging import basicConfig, getLevelName, getLogger
from pathlib import Path

from aiohttp import ClientSession
from packaging import version
from packaging.requirements import Requirement, SpecifierSet
from packaging.specifiers import Specifier
from packaging.version import Version
from tomlkit import dump, load

logger = getLogger(__name__)


def _find_in(sub_strings: list[str], string: str) -> str | None:
    """Return the first found sub_string in string."""
    return next((s for s in sub_strings if s in string), None)


async def get_package_info(package: str, session: ClientSession) -> dict:
    """Check if dependency is candidate for update."""
    url = f"/pypi/{package}/json"
    async with session.get(url) as response:
        return await response.json()


def find_latest_version(
    package: dict,
    # *,
    # use_postreleases: bool = False,
    # use_prereleases: bool = False,
) -> str | None:
    # TODO allow to check that python_requires is not higher than the runtime

    releases = list(package["releases"].keys())
    releases.sort(key=version.Version, reverse=True)
    for r in releases:
        if package["releases"][r][0]["yanked"]:
            continue

        v = version.parse(r)
        if v.is_prerelease:
            continue
        if v.is_postrelease:
            continue
        if v.is_devrelease:
            continue

        return r

    return None


def set_version(*, specifier: Specifier, version: Version, match_operators: list[str]) -> Specifier:
    if _find_in(match_operators, specifier.operator):
        return Specifier(f"{specifier.operator}{version}")

    return specifier


def set_versions(*, specifier: SpecifierSet, **kwargs) -> SpecifierSet:
    # TODO nicer ?
    return SpecifierSet(",".join([str(set_version(specifier=s, **kwargs)) for s in specifier]))


async def upgrade_requirement(
    requirement: str,
    *,
    session: ClientSession,
    match_operators: list[str]
) -> str:
    r = Requirement(requirement)

    if not r.specifier or not _find_in(match_operators, str(r.specifier)):
        logger.debug(f"skipping {r} does not match operators.")
        return str(r)

    updated = set_versions(
        specifier=r.specifier,
        version=find_latest_version(await get_package_info(r.name, session)),
        match_operators=match_operators
    )

    if r.specifier != updated:
        logger.info(f"{r} -> {r.name}{updated}")
        r.specifier = updated

    return str(r)


def parse_arguments() -> Namespace:
    """Parse arguments."""
    parser = ArgumentParser(
        description="Update Python Project Dependencies.",
        formatter_class=ArgumentDefaultsHelpFormatter)

    parser.add_argument(
        "-p", "--project-file", nargs="*", default=["pyproject.toml"],
        help="Path to pyproject file(s)")

    parser.add_argument(
        "-m", "--match_operators", nargs="*", default=["==", "<=", "~≃"],
        choices=["<", "<=", "==", ">=", ">", "~="],
        help="operators to upgrade.")

    parser.add_argument(
        "--dry-run", action="store_true",
        help="Pipe loggining to file instead of stdout.")

    parser.add_argument(
        "--index-url", default="https://pypi.org",
        help="Base URL of the Python Package Index. Defaults to 'https://pypi.org'.")

    parser.add_argument(
        "--log-level", default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level.")

    parser.add_argument(
        "--log-file", type=str,
        help="Pipe loggining to file instead of stdout.")

    return parser.parse_args()


async def main(args: Namespace):
    """Main."""
    if args.log_file:
        basicConfig(filename=args.log_file, level=getLevelName(args.log_level))
    else:
        basicConfig(stream=sys.stdout, level=getLevelName(args.log_level))

    #TODO allow to upgrade to betas / preleases

    for pf in args.project_file:

        try:
            with Path(pf).open("r") as f:
                data = load(f)
                logger.info(f"== {pf} ==")
        except FileNotFoundError:
            logger.error(f"No such file '{pf}' - skipping.")
            continue

        project = data.get("project")
        if project is None:
            return

        logger.debug(args.index_url)
        try:
            async with ClientSession(args.index_url) as session:
                if dep := project.get("dependencies"):
                    logger.info("[project.dependencies]:")
                    for e, d in enumerate(dep):
                        dep[e] = await upgrade_requirement(
                            d, session=session, match_operators=args.match_operators)

                if optional_dep := project.get("optional-dependencies"):
                    for k, dep in optional_dep.items():
                        logger.info(f"[project.optional-dependencies.{k}]:")
                        for e, d in enumerate(dep):
                            dep[e] = await upgrade_requirement(
                                d, session=session, match_operators=args.match_operators)

        except ValueError:
            logger.critical("Invalid index-url.")
            exit(1)

        if not args.dry_run:
            with Path(pf).open("w") as f:
                dump(data, f)


def main_cli():
    args = parse_arguments()
    asyncio.run(main(args))


if __name__ == "__main__":
    args = parse_arguments()

    asyncio.run(main(args))

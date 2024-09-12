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
from tomlkit import dump, load

logger = getLogger(__name__)

def candidate(d: str) -> bool:

    if "===" in d:
        return False

    return "==" in d


async def get_package_info(
    session: ClientSession,
    package: str) -> dict:
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

        if  v.is_postrelease:
            continue

        if  v.is_devrelease:
            continue

        return r

    return None

async def bump_dependencies(session: ClientSession, dep: dict) -> None:

    for e, d in enumerate(dep):
        if not candidate(d):
            continue

        s = d.split("==")
        newest = find_latest_version(
            await get_package_info(session, s[0].split("[")[0]))

        if newest is None or newest == s[-1]:
            logger.debug(f"{d} -> {newest}")
            continue

        logger.info(f"{d} -> {newest}")
        dep[e] = f"{s[0]}=={newest}"

def parse_arguments() -> Namespace:
    """Parse arguments."""
    parser = ArgumentParser(
        description="Update Python Project Dependencies.",
        formatter_class=ArgumentDefaultsHelpFormatter)

    parser.add_argument(
        "-p", "--project-file", nargs="*", default=["pyproject.toml"],
        help="Path to pyproject file(s)")

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

    logger.debug(args)

    #TODO allow to upgrade to betas / preleases


    for pf in args.project_file:

        try:
            with Path(pf).open("r") as f:
                data = load(f)
                logger.info(f"== {pf} ==")
        except FileNotFoundError:
            logger.error(f"No such file '{pf}' - skipping.")
            continue

        # TODO split based on "==" and check if package if true

        try:
            async with ClientSession(args.index_url) as session:

                project = data.get("project")

                if project is None:
                    return

                if dep := project.get("dependencies"):
                    logger.info("[project.dependencies]:")
                    await bump_dependencies(session, dep)

                if optional_dep := project.get("optional-dependencies"):
                    for k, dep in optional_dep.items():
                        logger.info(f"[project.optional-dependencies.{k}]:")
                        await bump_dependencies(session, dep)

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

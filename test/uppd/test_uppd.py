# Copyright (c) 2020, Janus Heide.
# All rights reserved.
#
# Distributed under the "BSD 3-Clause License", see LICENSE.txt.

from aiohttp import ClientSession
from packaging.requirements import SpecifierSet
from packaging.specifiers import Specifier

from uppd import (
    find_latest_version, get_package_info, set_version, set_versions,
    upgrade_requirements,
)


async def test_get_package_info(index_url="https://pypi.org"):
    async with ClientSession(index_url) as session:
        assert await get_package_info("sampleproject", session=session)


def test_set_version():
    assert set_version(Specifier("==0"), version="1", match_operators=["=="]) == "==1"


def test_set_versions():
    assert set_versions(
        SpecifierSet("==0.1"),
        version="1",
        match_operators=["==", "<=", "~="],
        ) == SpecifierSet("==1")

    assert set_versions(
        SpecifierSet("<=0.1"),
        version="1",
        match_operators=["==", "<=", "~="],
        ) == SpecifierSet("<=1")

    assert set_versions(
        SpecifierSet("~=0.1"),
        version="1.0",
        match_operators=["==", "<=", "~="],
        ) == SpecifierSet("~=1.0")

    assert set_versions(
        SpecifierSet("~=0.1,==0.1"),
        version="1.0",
        match_operators=["==", "~="],
        ) == SpecifierSet("==1.0, ~=1.0")

    assert set_versions(
        SpecifierSet("~=0.2,>0.1"),
        version="1.0",
        match_operators=["==", "~="],
        ) == SpecifierSet(">0.1, ~=1.0")

    assert set_versions(
        SpecifierSet("~=0.2,>0.1"),
        version="1.0",
        match_operators=[],
        ) == SpecifierSet(">0.1, ~=0.2")


async def test_find_latest_version(index_url="https://pypi.org"):
    async with ClientSession(index_url) as session:
        sp = await get_package_info("sampleproject", session=session)
        assert find_latest_version(sp, dev=False, pre=False, post=False) == "3.0.0"
        assert find_latest_version(sp, dev=True, pre=False, post=False) == "3.0.0"
        assert find_latest_version(sp, dev=False, pre=True, post=False) == "3.0.0"
        assert find_latest_version(sp, dev=False, pre=False, post=True) == "3.0.0"


async def test_upgrade_requirements(index_url="https://pypi.org"):
    async with ClientSession(index_url) as session:

        assert await upgrade_requirements(
            ["sampleproject==2.0.0"],
            session=session,
            skip=[],
            dev=[],
            pre=[],
            post=[],
            match_operators=["=="],
            ) != ["sampleproject==2.0.0"]

        assert await upgrade_requirements(
            ["sampleproject==2.0.0"],
            session=session,
            skip=[],
            dev=[],
            pre=[],
            post=[],
            match_operators=[],
            ) == ["sampleproject==2.0.0"]

        assert await upgrade_requirements(
            ["sampleproject==2.0.0"],
            session=session,
            skip=["sampleproject"],
            dev=[],
            pre=[],
            post=[],
            match_operators=["=="],
            ) == ["sampleproject==2.0.0"]

        assert await upgrade_requirements(
            ["sampleproject==2.0.0"],
            session=session,
            skip=[],
            dev=["sampleproject"],
            pre=[],
            post=[],
            match_operators=["=="],
            ) != ["sampleproject==2.0.0"]

        assert await upgrade_requirements(
            ["sampleproject==2.0.0"],
            session=session,
            skip=[],
            dev=[],
            pre=["sampleproject"],
            post=[],
            match_operators=["=="],
            ) != ["sampleproject==2.0.0"]

        assert await upgrade_requirements(
            ["sampleproject==2.0.0"],
            session=session,
            skip=[],
            dev=[],
            pre=[],
            post=["sampleproject"],
            match_operators=["=="],
            ) != ["sampleproject==2.0.0"]

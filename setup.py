# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import json

from setuptools import find_packages, setup

with open("Pipfile.lock") as fd:
    lock_data = json.load(fd)

    install_requires = []
    for package_name, package_data in lock_data["default"].items():
        if "version" not in package_data:
            raise ValueError(
                f"Package {package_name} does " f"not have version key: {package_data}"
            )
        install_requires.append(package_name + package_data["version"])

setup(
    name="gpy",
    version="0.0.1",
    author="David Torralba Goitia",
    author_email="david.torralba.goitia@gmail.com",
    packages=find_packages(exclude=["tests"]),
    license="MIT",
    python_requires=">=3.7",
    include_package_data=True,
    zip_safe=False,
    install_requires=install_requires,
    entry_points={
        "console_scripts": [
            "gpy=gpy.cli:main",
        ],
    },
)

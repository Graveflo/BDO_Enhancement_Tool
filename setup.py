# - * -coding: utf - 8 - * -
import setuptools
from setuptools.command.build_py import build_py
from src.BDO_Enhancement_Tool.__main__ import RELEASE_VER

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()


class my_build_py(build_py):
    def find_package_modules(self, package, package_dir):
        modules = super().find_package_modules(package, package_dir)
        return [(pkg, mod, file, ) for (pkg, mod, file, ) in modules if not (pkg=='BDO_Enhancement_Tool.bdo_database' and mod=='create')]

setuptools.setup(
    name="BDO_Enhancement_Tool",
    version=RELEASE_VER,
    author="Graveflo",
    author_email="",
    description="Open source tool for planning fail stacks and enhancement priority in Black Desert Online",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ILikesCaviar/BDO_Enhancement_Tool",
    project_urls={
        "Bug Tracker": "https://github.com/ILikesCaviar/BDO_Enhancement_Tool/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    package_data={
        'BDO_Enhancement_Tool':['Images/*','Images/**/*', '*.png', '*.ico', 'based_settings.json'],
        'BDO_Enhancement_Tool.bdo_database': ['gear.sqlite3', 'tmp_imgs/.manifest'],
        'BDO_Enhancement_Tool.Core': ['Data/*.json']
    },
    cmdclass={'build_py': my_build_py},
    python_requires=">=3.6",
)
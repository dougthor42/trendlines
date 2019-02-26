# -*- coding: utf-8 -*-
from pathlib import Path
from setuptools import setup, find_packages


# Read the `__about__.py` file. This is how `cryptography` does it. Seems
# like a decent way, but I don't really like the `exec()`. /shrug.
about = {}
about_file = Path.cwd() / "src" / "trendlines" / "__about__.py"
with open(str(about_file)) as openf:
    exec(openf.read(), about)

long_descr = Path("./README.md").read_text()

requires = [
    "flask>=1.0",
    "peewee>=3.8",
]

setup(
    name=about["__package_name__"],
    version=about['__version__'],

    description=about['__description__'],
    long_description=long_descr,
    long_description_content_type="text/markdown",
    url=about['__project_url__'],

    author=about['__author__'],
    author_email=about['__email__'],

    package_dir={'': 'src'},
    packages=find_packages(where='src'),
    include_package_data=False,

    python_requires=">=3.5",
    install_requires=requires,
)

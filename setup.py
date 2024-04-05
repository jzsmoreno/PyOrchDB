from pathlib import Path

import setuptools
from pip._internal.req import parse_requirements

# Parse the requirements.txt file
requirements = parse_requirements("requirements.txt", session="hack")

# Get the list of requirements as strings
install_requires = [str(req.requirement) for req in requirements]
install_requires = install_requires[:-1]  # Remove "--find-links" line

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

about = {}
ROOT_DIR = Path(__file__).resolve().parent
PACKAGE_DIR = ROOT_DIR / "PyOrchDB"
with open(PACKAGE_DIR / "VERSION") as f:
    _version = f.read().strip()
    about["__version__"] = _version

setuptools.setup(
    name="PyOrchDB",
    version=about["__version__"],
    author="J. A. Moreno-Guerra",
    author_email="jzs.gm27@gmail.com",
    maintainer="David Pedroza",
    maintainer_email="david.pedroza.segoviano@gmail.com",
    description="A package for designing and implementing ETL",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jzsmoreno/PyOrchDB",
    project_urls={"Bug Tracker": "https://github.com/jzsmoreno/PyOrchDB/issues"},
    license="BSD 3-Clause",
    packages=setuptools.find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
    install_requires=install_requires,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
)

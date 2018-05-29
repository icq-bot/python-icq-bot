import io
from os import path

from setuptools import setup, find_packages

import icq

here = path.abspath(path.dirname(__file__))


def long_description():
    with io.open(file=path.join(here, "README.md"), encoding="utf-8") as file:
        return file.read()


def requirements():
    with io.open(file=path.join(here, "requirements.txt")) as file:
        return file.readlines()


setup(
    name="python-icq-bot",
    version=icq.__version__,
    description="Pure Python interface for ICQ Bot API. Bot cookbook for Humans.",
    long_description=long_description(),
    long_description_content_type="text/markdown",
    url="https://github.com/icq-bot/python-icq-bot",
    author="ICQ LLC (Mail.Ru Group)",
    author_email="support@icq.com",
    license="MIT",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Communications :: Chat",
        "Topic :: Internet",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Operating System :: OS Independent"
    ],
    keywords="python icq bot api",
    packages=find_packages(exclude=["example"]),
    install_requires=requirements(),
    python_requires=">= 2.7, != 3.0.*, != 3.1.*, != 3.2.*, != 3.3.*",
    include_package_data=True,
    zip_safe=False
)

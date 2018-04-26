from setuptools import setup, find_packages

setup(
    name="python-icq-bot",
    version="0.0.9",
    description="Pure Python interface for ICQ Bot API. Bot cookbook for Humans.",
    packages=find_packages(exclude=["example"]),
    url="https://github.com/icq-bot/python-icq-bot",
    zip_safe=False
)

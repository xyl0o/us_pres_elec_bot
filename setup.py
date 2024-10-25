import os
from setuptools import setup, find_packages


setup(
    name = "us-pres-elec-bot",
    version = "0.1",
    author = "Maximilian Bauregger",
    description = "A small telegram bot that sends you election updates",
    keywords = "telegram usa election",
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    install_requires=[
        "python-telegram-bot==13.0",
        "requests==2.24.0",
    ],
)
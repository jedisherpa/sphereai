# setup.py
# Author: Linus Torvalds (Systems Correctness)

from setuptools import setup, find_packages

# This is a standard setup.py file. It makes the tool installable via pip.
# It is simple, it is correct, and it works. There is no need for more.

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="sphere-cli",
    version="0.5.0",
    author="The Sphere Team",
    author_email="hello@sphereai.dev",
    description="A local-first multi-agent analysis tool with LLM integration, RSS feeds, and email digests.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jedisherpa/sphereai",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Environment :: Console",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.10",
    install_requires=[
        "click>=8.0.0",
        "rich>=13.0.0",
        "gitpython>=3.1.0",
        "feedparser>=6.0.0",
        "requests>=2.28.0",
        "pyyaml>=6.0.0",
    ],
    entry_points={
        "console_scripts": [
            "sphere=sphere.main:cli",
        ],
    },
)

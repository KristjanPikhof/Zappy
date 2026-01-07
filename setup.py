"""Setup script for Zappy the VPS Toolbox."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="zappy",
    version="1.0.0",
    author="Kristjan Pikhof",
    description="Zappy the VPS Toolbox - Comprehensive VPS management CLI tool",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/KristjanPikhof/zappy",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: System :: Systems Administration",
    ],
    python_requires=">=3.8",
    install_requires=[
        "rich>=13.0.0",
    ],
    entry_points={
        "console_scripts": [
            "zappy=zappy.cli:main",
        ],
    },
)

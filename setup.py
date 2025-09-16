#!/usr/bin/env python3

from setuptools import setup, find_packages
import os

# Read the README file
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# Read requirements
def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="netscan",
    version="1.0.0",
    author="Wasif Amin",
    author_email="wasif.amin@example.com",
    description="A comprehensive network penetration testing tool with automated scanning and reporting capabilities",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "app": [
            "ui/templates/*.html",
            "ui/static/*",
        ],
    },
    keywords="penetration-testing, network-security, vulnerability-scanning, nmap, nuclei, ssl-testing",
)
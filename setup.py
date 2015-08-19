__author__ = 'shako'
from setuptools import setup, find_packages

# dependencies
with open('requirements.txt') as f:
    deps = f.read().splitlines()

version = "0.1.0"

# main setup script
setup(
    name="minionKevin",
    version=version,
    description="mtbf feedback data to raptor",
    author="Mozilla Taiwan",
    author_email="tw-qa@mozilla.com",
    license="MPL",
    install_requires=deps,
    packages=find_packages(),
    entry_points={'console_scripts': ['banana = minionKevin.banana:main']},
    include_package_data=True,
    zip_safe=False
)

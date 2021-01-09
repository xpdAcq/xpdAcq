import sys
from os import path

from setuptools import setup, find_packages

# NOTE: This file must remain Python 2 compatible for the foreseeable future,
# to ensure that we error out properly for people with outdated setuptools
# and/or pip.
min_version = (3, 6)
if sys.version_info < min_version:
    error = ("\n"
             "pdfstream does not support Python {0}.{1}.\n"
             "Python {2}.{3} and above is required. Check your Python version like so:\n"
             "\n"
             "python3 --version\n"
             "\n"
             "This may be due to an out-of-date pip. Make sure you have pip >= 9.0.1.\n"
             "Upgrade pip like so:\n"
             "\n"
             "pip install --upgrade pip\n").format(*(sys.version_info[:2] + min_version))
    sys.exit(error)

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.md'), encoding='utf-8') as readme_file:
    readme = readme_file.read()

setup(
    name="xpdacq",
    version='0.12.0',
    packages=find_packages(),
    long_description=readme,
    long_description_content_type='text/markdown',
    description="acquisition module",
    zip_safe=False,
    package_data={
        "xpdacq": [
            "data/*.D",
            "tests/*.D",
            "tests/*.xls*",
            "tests/*.yml",
            "examples/*.yaml",
        ]
    },
    author="Songsheng Tao",
    author_email='st3107@columbia.edu',
    url="https://github.com/xpdAcq/xpdacq",
    install_requires=[
        "numpy>=1.11",
        "matplotlib>=1.5.1",
        "pyyaml",
        "boltons",
        "bluesky>=v0.5.1",
        "event_model",
    ]
)

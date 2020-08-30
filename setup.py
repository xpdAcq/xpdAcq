from setuptools import setup, find_packages


setup(
    name="xpdacq",
    version="0.10.4",
    packages=find_packages(),
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
    url="http:/github.com/xpdAcq/xpdacq",
    install_requires=[
        "numpy>=1.11",
        "matplotlib>=1.5.1",
        "pyyaml",
        "boltons",
        "bluesky>=v0.5.1",
        "event_model",
    ],
)

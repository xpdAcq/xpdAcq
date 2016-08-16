# suggest to install matplotlib, pyyaml from conda

from setuptools import setup, find_packages
setup(
    name = 'xpdacq',
    version = '0.0.3',
    packages = find_packages(),
    description = 'acquisition module',
    zip_safe = True,
    url = 'http:/github.com/xpdAcq/xpdacq',
    install_requires = [
                    'numpy >= 1.11',
                    'matplotlib >= 1.5.1',
                    'PyYaml',
                    'tifffile',
                    'boltons',
                    'bluesky',
                    'event_model'
                            ],
    dependency_links=[
        'https://github.com/NSLS-II/event-model/zipball/v1.0.2#egg=event_model-v1.0.2',
        "https://github.com/NSLS-II/bluesky/zipball/v0.5.3#egg=bluesky-v0.5.3"
        ]
    )

# suggest to install matplotlib, pyyaml from conda

from setuptools import setup, find_packages
setup(
    name = 'xpdacq',
    version = '0.0.3',
    packages = find_packages(),
    description = 'acquisition module',
    zip_safe = False,
    url = 'http:/github.com/xpdAcq/xpdacq',
    install_requires = [
                    'numpy >= 1.11',
                    'matplotlib >= 1.5.1',
                    'pyyaml',
                    'boltons',
                    'bluesky',
                    'event_model'
                            ],
    dependency_links=[
        'https://github.com/NSLS-II/event-model/zipball/master#egg=event_model-v1.0.2',
        'https://github.com/NSLS-II/bluesky/zipball/master#egg=bluesky-v0.5.1'
        ]
    )

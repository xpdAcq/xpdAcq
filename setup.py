from setuptools import setup, find_packages


setup(
    name='xpdacq',
    version='0.10.1',
    packages=find_packages(),
    description='acquisition module',
    zip_safe=False,
    package_data={'xpdacq': ['data/*.D', 'tests/*.D',
                             'tests/*.xls*', 'tests/*.yml',
                             'examples/*.yaml']},
    url='http:/github.com/xpdAcq/xpdacq'
)

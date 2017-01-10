from setuptools import setup, find_packages

setup(
    name='xpdacq',
    version='0.0.4',
    packages=find_packages(),
    description='acquisition module',
    zip_safe=False,
    package_data={'xpdacq':['examples/']},
    url='http:/github.com/chiahaoliu/xpdacq'
)

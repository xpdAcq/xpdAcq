from setuptools import setup, find_packages

setup(
    name='xpdacq',
    version='0.5.2',
    packages=find_packages(),
    description='acquisition module',
    zip_safe=False,
    package_data={'xpdacq':['examples/', 'data/']},
    url='http:/github.com/chiahaoliu/xpdacq'
)

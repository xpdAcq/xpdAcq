import ast
from setuptools import setup, find_packages


def find_version(filename):
    with open(filename) as f:
        initlines = f.readlines()
    version_line = None
    for line in initlines:
        if line.startswith('__version__'):
            vstr = line.strip().split()[-1]
            ver = ast.literal_eval(vstr)
            break
    return ver


setup(
    name='xpdacq',
    version=find_version('xpdacq/__init__.py'),
    packages=find_packages(),
    description='acquisition module',
    zip_safe=False,
    package_data={'xpdacq': ['examples/', 'data/']},
    url='http:/github.com/chiahaoliu/xpdacq'
)

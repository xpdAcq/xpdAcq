from setuptools import setup, find_packages
import versioneer

setup(
    name='xpdacq',
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    packages=find_packages(),
    description='acquisition module',
    zip_safe=False,
    url='http:/github.com/chiahaoliu/xpdacq'
)

# pylint: disable=missing-module-docstring

from setuptools import setup, find_packages

setup(
    # Needed to silence warnings (and to be a worthwhile package)
    name='jeedomdaemon',
    url='https://github.com/Mips2648/jeedom-daemon-py',
    author='Mips',
    # author_email='',
    # Needed to actually package something
    packages=find_packages(),
    # Needed for dependencies
    install_requires=['aiohttp'],
    # *strongly* suggested for sharing
    version='0.7.5',
    # The license can be anything you like
    license='MIT',
    description='A base to implement Jeedom daemon in python',
    # We will also need a readme eventually (there will be a warning)
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
)

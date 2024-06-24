# pylint: disable=missing-module-docstring

from setuptools import setup, find_packages

__version__ = "0.10.0"

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
    version=__version__,
    # The license can be anything you like
    license='MIT',
    description='A base to implement Jeedom daemon in python',
    # We will also need a readme eventually (there will be a warning)
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    keywords = ['JEEDOM', 'DAEMON', 'ASYNCIO'],
    classifiers=[
        'Development Status :: 4 - Beta',      # Chose either "3 - Alpha", "4 - Beta" or "5 - Production/Stable" as the current state of your package

        'Intended Audience :: Developers',      # Define that your audience are developers
        'Topic :: Software Development :: Build Tools',

        'License :: OSI Approved :: MIT License',   # Again, pick a license

        'Programming Language :: Python :: 3',      #Specify which pyhton versions that you want to support
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.11',
    ],
)

from setuptools import setup

setup(
    # Needed to silence warnings (and to be a worthwhile package)
    name='Jeedom daemon',
    url='https://github.com/Mips2648/jeedom-daemon-py',
    author='Mips',
    # author_email='',
    # Needed to actually package something
    packages=['jeedom-daemon-py'],
    # Needed for dependencies
    # install_requires=['numpy'],
    # *strongly* suggested for sharing
    version='0.1',
    # The license can be anything you like
    license='MIT',
    description='A base to implement Jeedom daemon in python',
    # We will also need a readme eventually (there will be a warning)
    # long_description=open('README.txt').read(),
)
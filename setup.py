from setuptools import setup
import buildcloth
from sys import version_info

REQUIRES = ['pyyaml']

if version_info < (2, 7):
    # no argparse in 2.6 standard
    REQUIRES.append('argparse')

setup(
    name='buildcloth',
    description='A framework for genarting build system description files, with support for Ninja and Make.',
    version=buildcloth.__version__,
    author='Sam Kleinman',
    author_email='sam@tychoish.com',
    license='Apache',
    url='http://cyborginstitute.org/projects/buildcloth',
    install_requires=REQUIRES,
    packages=['buildcloth'],
    setup_requires=['nose'],
    test_suite='test',
    entry_points={
        'console_scripts': [
            'buildc = buildcloth.buildc:main',
            ],
        },
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Topic :: Software Development :: Build Tools'
    ],
    )

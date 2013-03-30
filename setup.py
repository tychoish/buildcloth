from setuptools import setup
import buildcloth

setup(
    name='buildcloth',
    description='A framework for genarting build system description files, with support for Ninja and Make.',
    version=buildcloth.__version__,
    author='Sam Kleinman',
    author_email='sam@tychoish.com',
    license='Apache',
    url='http://cyborginstitute.org/projects/buildcloth',
    packages=['buildcloth'],
    setup_requires=['nose'],
    test_suite='test',
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: Apache Software License',
        'Topic :: Software Development :: Build Tools'
    ],
    )

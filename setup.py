try:
    from setuptools import setup  #Py2
except ImportError:
    from distutils.core import setup  #Py3

import sys

install_requires = []
# if sys.version_info < (3, 4):
#     install_requires.append('enum34')

setup(
    name='bashspy',
    version='0.1',
    url='https://github.com/sarvi/bashspy.git',
    license='GPLv3+',
    author='Sarvi Shanmugham',
    author_email='sarvi@yahoo.com',
    description='Python parser for bash using the open source  spy package',
    long_description='''Python parser for bash using the open source  spy package.


See https://github.com/sarvi/bashspy/blob/master/README.md for more info.''',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: System Shells',
        'Topic :: Text Processing',
    ],
    install_requires=install_requires,
    packages=['bashspy'],
)

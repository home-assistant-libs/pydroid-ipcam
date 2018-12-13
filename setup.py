from setuptools import setup

with open('README.rst') as f:
    long_description = f.read()

VERSION = "0.9"

setup(
    name='pydroid-ipcam',
    version=VERSION,
    license='BSD License',
    author='Pascal Vizeli',
    author_email='pvizeli@syshack.ch',
    url='https://github.com/pvizeli/pydroid-ipcam',
    download_url='https://github.com/pvizeli/pydroid-ipcam/tarball/'+VERSION,
    description=('A asyncio library for handling android ipcam'),
    long_description=long_description,
    classifiers=[
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Scientific/Engineering :: Atmospheric Science',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    keywords=['android', 'ipcam', 'api', 'asyncio'],
    zip_safe=False,
    platforms='any',
    py_modules=['pydroid_ipcam'],
    install_requires=[
        'aiohttp',
        'yarl',
    ],
)

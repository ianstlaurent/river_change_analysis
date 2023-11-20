#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = ['scikit-image',
        'matplotlib',
        'rasterio',
        'numpy',
        'shapely', 'ee', 'StringIO']

test_requirements = [ ]

setup(
    author="Ian St. Laurent",
    author_email='ianstlaurent7@gmail.com',
    python_requires='>=3.6',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    description="Analyzes rivers width, accretion, and erosion over time using Landsat imagery.",
    install_requires=requirements,
    license="MIT license",
    long_description=readme + '\n\n' + history,
    include_package_data=True,
    keywords='river_change_analysis',
    name='river_change_analysis',
    packages=find_packages(include=['river_change_analysis', 'river_change_analysis.*']),
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/ianstlaurent/river_change_analysis',
    version='0.1.0',
    zip_safe=False,
)

#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import find_packages, setup

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = [
    'Click>=6.0',
    'jinja2<2.9',
    'ansible>=2.2.0',
    'cookiecutter>=1.5.1',
    'stevedore>=1.18.0',
    'py>=1.4.32',
    'click-log>=0.1.8',
    'voluptuous>=0.9.3',
    'requests>=2.13.0'
]

test_requirements = [
    # TODO: put package test requirements here
]

setup(
    name='freckles',
    version='0.1.50',
    description="A dotfile manager",
    long_description=readme + '\n\n' + history,
    author="Markus Binsteiner",
    author_email='makkus@posteo.de',
    url='https://github.com/makkus/freckles',
    packages=find_packages(),
    # package_dir={'freckles':
                 # 'freckles'},
    entry_points={
        'console_scripts': [
            'freckles=freckles.cli:cli'
        ],
        'freckles.frecks': [
            'install=freckles.frecks:Install',
            'update-package-cache=freckles.frecks:Update',
            'upgrade-all-packages=freckles.frecks:Upgrade',
            'checkout-dotfiles=freckles.frecks:CheckoutDotfiles',
            'git-repo=freckles.frecks:CheckoutGitRepo',
            'stow=freckles.frecks:Stow',
            # 'install-pkg-managers=freckles.frecks:InstallPkgMgrs',
            'install-nix=freckles.frecks:InstallNix',
            'install-conda=freckles.frecks:InstallConda',
            'install-brew=freckles.frecks:InstallBrew',
            'delete=freckles.frecks:Delete',
            'create-folder=freckles.frecks:EnsureDirectory',
            # 'debug-vars=freckles.frecks:DebugVars',
            'ansible-role=freckles.frecks:Role',
            'ansible-task=freckles.frecks:Task'
        ]
    },
    include_package_data=True,
    install_requires=requirements,
    license="GNU General Public License v3",
    zip_safe=False,
    keywords='freckles',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.7',
    ],
    test_suite='tests',
    tests_require=test_requirements
)

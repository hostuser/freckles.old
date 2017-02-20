#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_freckles
----------------------------------

Tests for `freckles` module.
"""

import pytest

from contextlib import contextmanager
from click.testing import CliRunner

from freckles import freckles
from freckles import cli


@pytest.fixture
def response():
    """Sample pytest fixture.
    See more at: http://doc.pytest.org/en/latest/fixture.html
    """
    # import requests
    # return requests.get('https://github.com/audreyr/cookiecutter-pypackage')


def test_content(response):
    """Sample pytest test function with the pytest fixture as an argument.
    """
    # from bs4 import BeautifulSoup
    # assert 'GitHub' in BeautifulSoup(response.content).title.string

def test_command_line_interface():
    runner = CliRunner()
    result = runner.invoke(cli.cli)
    #assert result.exit_code == 0
    # assert 'freckles.cli.cli' in result.output
    help_result = runner.invoke(cli.cli, ['--help'])
    assert help_result.exit_code == 0
    assert 'Show this message and exit.' in help_result.output

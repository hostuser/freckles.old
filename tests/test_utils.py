#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_freckles
----------------------------------

Tests for `freckles` module.
"""

import pytest

import yaml

import freckles.utils

from contextlib import contextmanager
from click.testing import CliRunner

from freckles import freckles
from freckles import cli
from freckles import utils

SINGLE_RUN_WITH_ONE_VAR_DICT = {
    "vars": {"key1": "value1"},
    "runs": [
        {"name": "run1",
         "frecks": ["debug"]}
    ]
    }


def get_yaml_file_content(rel_path):

    with open(rel_path) as f:
        content = yaml.load(f)
    return content

@pytest.mark.parametrize("url, expected", [
    ("tests/resources/single_run_with_one_var.yml", SINGLE_RUN_WITH_ONE_VAR_DICT),
    ("")
])
def test_get_config(url, expected):

    config = utils.get_config(url)
    assert config == SINGLE_RUN_WITH_ONE_VAR_DICT

#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_freckles
----------------------------------

Tests for `freckles` module.
"""

import os
from contextlib import contextmanager

import yaml
from click.testing import CliRunner

import freckles.utils
import pytest
from freckles import cli, freckles, utils
from freckles.frkl import get_config

SINGLE_RUN_WITH_ONE_VAR_DICT = {
    "vars": {"key1": "value1"},
    "runs": [
        {"name": "run1",
         "frecks": ["debug"]}
    ]
    }

SINGLE_RUN_WITH_ONE_VAR_DICT_JSON = '{"vars": {"key1": "value1"}, "runs": [{"name": "run1", "frecks": ["debug"]}]}'

DEFAULT_DOTFILES_LIST = [{"base_dir": os.path.expanduser("~/dotfiles"), "paths": [], "remote": ""}]

DEFAULT_DOTFILES_LIST_REMOTE = [{"base_dir": os.path.expanduser("~/dotfiles"), "paths": [], "remote": "https://github.com/makkus/dotfiles.git"}]

def get_yaml_file_content(rel_path):

    with open(rel_path) as f:
        content = yaml.load(f)
    return content

def ensure_dotfiles_dir():

    if not os.path.exists(os.path.expanduser("~/dotfiles")):
        os.makedirs(os.path.expanduser("~/dotfiles"))

# @pytest.mark.parametrize("url, expected", [
#     ("tests/resources/single_run_with_one_var.yml", SINGLE_RUN_WITH_ONE_VAR_DICT),
#     ("https://raw.githubusercontent.com/makkus/freckles/master/tests/resources/single_run_with_one_var.yml", SINGLE_RUN_WITH_ONE_VAR_DICT),
#     ("gh:makkus/freckles/tests/resources/single_run_with_one_var.yml", SINGLE_RUN_WITH_ONE_VAR_DICT),
#     (SINGLE_RUN_WITH_ONE_VAR_DICT_JSON, SINGLE_RUN_WITH_ONE_VAR_DICT)
# ])
# def test_get_config(url, expected):

#     config = get_config(url)
#     assert config == expected

@pytest.mark.parametrize("item, expected", [
    ("~/dotfiles", DEFAULT_DOTFILES_LIST)
    # ("https://github.com/makkus/dotfiles.git", DEFAULT_DOTFILES_LIST_REMOTE)
])
def test_parse_dotfiles_item(item, expected):

    ensure_dotfiles_dir()
    result = utils.parse_dotfiles_item(item)
    assert result == expected

#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

import click

# configuration constants
FRECKLES_DEFAULT_DIR = click.get_app_dir('freckles', force_posix=True)


# freckles filenames and extensions
FRECKLES_DEFAULT_CONFIG_FILE_NAME = "config.yml"
FRECKLES_METADATA_FILENAME = ".frkl"


# freckles defaults/conventions
DEFAULT_DOTFILE_REPO_NAME = "dotfiles"
FRECKLES_DEFAULT_FRECKLES_CONFIG_PATH = "freckles/.freckles/default.yml"
FRECKLES_DEFAULT_EXECUTION_BASE_DIR = os.path.join(FRECKLES_DEFAULT_DIR, "runs")
FRECKLES_DEFAULT_EXECUTION_DIR_NAME = "current"
FRECKLES_DEFAULT_ARCHIVE_PLAYS = False
FRECK_DEFAULT_SUDO = False


# ERROR CODES
FRECKLES_CONFIG_ERROR_EXIT_CODE = 2
FRECKLES_EXECUTION_ERROR_EXIT_CODE = 4
FRECKLES_BUG_EXIT_CODE = 7


# freck configuration keys
GLOBAL_RUNS_KEY = "runs"
GLOBAL_VARS_KEY = "vars"
GLOBAL_LOAD_KEY = "load"

RUN_META_KEY = "meta"
RUN_RUNNER_NAME_KEY = "type"
INT_RUN_RUNNER_KEY = "runner_obj"
RUN_DESC_KEY = "desc"
FRECK_TASKS_KEY = "tasks"
RUN_VARS_KEY = "vars"
RUN_NUMBER_KEY = "nr"
RUN_NAME_KEY = "name"

FRECK_RUNNER_KEY = "runner" # TODO: add supported runners check


FRECK_DESC_KEY = "desc"
FRECK_INDEX_KEY = "freck_index"
FRECK_VARS_KEY = "vars"
FRECK_META_KEY = "meta"
FRECK_OBJECT_KEY = "freck_name"

INT_FRECK_KEY = "freck_object"
FRECK_NAME_KEY = "freck_name"
FRECK_CONFIGS_KEY = "freck_configs"
FRECK_ID_KEY = "freck_id"
FRECK_ITEM_NAME_KEY = "freck_item_name"
FRECK_PREPROCESS_KEY = "freck_preprocess"
FRECK_TASK_DESC = "freck_task_desc"
FRECK_NEW_RUN_AFTER_THIS_KEY = "new_run_after"
FRECK_SUDO_KEY = "become"
FRECK_BECOME_KEY = "freck_become"

FRECK_PRIORITY_KEY = "priority"

# configuration keys & defaults
FRECKLES_ANSIBLE_RUNNER = "ansible"
FRECKLES_DEFAULT_RUNNER = FRECKLES_ANSIBLE_RUNNER
FRECK_SUPPORTED_RUNNERS_KEY = "supported_runners"

## dotfiles keys & defaults
DOTFILES_BASE_KEY = "base_dir"
DOTFILES_PATHS_KEY = "paths"
DOTFILES_REMOTE_KEY = "remote"

DEFAULT_DOTFILE_DIR = os.path.expanduser("~/dotfiles")

DEFAULT_DOTFILE_PATHS = []
DEFAULT_DOTFILE_REMOTE = ""

## misc keys & defaults
PACKAGES_KEY = "packages"

## freck run defaults
FRECK_DEFAULT_PRIORITY = 10000
RUN_STARTED = "Run started"
RUN_FINISHED = "Run finished"

## general defaults
FRECK_DEFAULT_CONFIG = {
}

# freck run output keys & defaults
FRECKLES_STATE_KEY = "state"
FRECKLES_CHANGED_KEY = "changed"
FRECKLES_STDOUT_KEY = "stdout"
FRECKLES_STDERR_KEY = "stderr"

FRECKLES_STATE_FAILED = "failed"
FRECKLES_STATE_SKIPPED = "skipped"
FRECKLES_STATE_NO_CHANGE = "no change"
FRECKLES_STATE_CHANGED = "changed"


# to sort
PKG_MGR_KEY = "pkg_mgr"
PKG_MGRS_KEY = "pkg_mgrs"
DEFAULT_PACKAGE_MANAGER_STRING = "default"
PACKAGE_STATE_KEY = "pkg_state"
DEFAULT_PACKAGE_STATE = "present"
DEFAULT_PACKAGE_SUDO = True
TASK_NAME_KEY = "task_name"
FRECK_META_KEY = "meta"
TASK_IGNORE_STRING = "FRECKLES_IGNORE"



FRECKLES_DEFAULT_FRECKLES_BOOTSTRAP_CONFIG_PATH = "freckles/.freckles/bootstrap.yml"


# FRECKLES_DEFAULT_PROFILE = "<all>"


FRECKLES_GROUP_DETAILS_FILENAME = "freckles"


FRECKLES_DEFAULT_HOSTS = ["localhost"]


# FRECKLES_DEFAULT_LOG_DIR = os.path.join(FRECKLES_DEFAULT_EXECUTION_BASE_DIR, "log")
# FRECKLES_DEFAULT_LOG_FILE = os.path.join(FRECKLES_DEFAULT_LOG_DIR, "freckles.log")

FRECKLES_PLAYBOOK_DIR = "plays"
FRECKLES_PLAYBOOK_NAME = "freckles_playbook.yml"
FRECKLES_INVENTORY_DIR = "inventory"
FRECKLES_INVENTORY_FILE = "inventory.yml"
FRECKLES_EXECUTION_SCRIPT = "freckles_run.sh"

#DEFAULT_DOTFILES = [DEFAULT_DOTFILE_DIR]


DEFAULT_PACKAGE_STATE_KEY = "default_pkg_state"
DEFAULT_PACKAGE_SUDO_KEY = "default_pkg_sudo"




# FRECK_DEFAULT_PRIORITY_KEY = "default_freck_priority"


DOTFILES_DIR_KEY = "dotfiles_dir"

DOTFILES_KEY = "dotfiles"



FRECK_CONFIG_TEMPLATE_KEY = "freck_config_template"

FRECKLES_CALLBACK_PLUGIN_NAME = "freckles_callback"

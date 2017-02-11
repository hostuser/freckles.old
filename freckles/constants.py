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
FRECKLES_DEFAULT_FRECKLES_CONFIG_PATH = "freckles/.freckles/default.yml"
FRECKLES_DEFAULT_GROUP_NAME = "freckles"


# ERROR CODES
FRECKLES_CONFIG_ERROR_EXIT_CODE = 2
FRECKLES_EXECUTION_ERROR_EXIT_CODE = 4
FRECKLES_BUG_EXIT_CODE = 7


# freck configuration keys
FRECK_TYPE_KEY = "freck_type"
FRECK_NAME_KEY = "freck_name"
FRECK_ID_KEY = "freck_id"

FRECK_ITEM_NAME_KEY = "item_name"

FRECK_SUDO_KEY = "freck_sudo"
FRECK_RUNNER_KEY = "runner"
FRECK_ANSIBLE_RUNNER = "ansible"
FRECK_ANSIBLE_ROLES_KEY = "freck-roles"
FRECK_ANSIBLE_ROLE_KEY = "role"
FRECK_PRIORITY_KEY = "freck_priority"

# configuration keys & defaults

## dotfiles keys & defaults
DOTFILES_BASE_KEY = "base_dir"
DOTFILES_PATHS_KEY = "paths"
DOTFILES_REMOTE_KEY = "remote"

DEFAULT_DOTFILE_DIR = os.path.expanduser("~/dotfiles")
DEFAULT_DOTFILE_REPO_NAME = "dotfiles"
DEFAULT_DOTFILE_PATHS = []
DEFAULT_DOTFILE_REMOTE = ""

## misc keys & defaults
APPS_KEY = "apps"

## freck run defaults
FRECK_DEFAULT_PRIORITY = 10000

## general defaults
FRECK_DEFAULT_CONFIG = {
    FRECK_PRIORITY_KEY: FRECK_DEFAULT_PRIORITY
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
PACKAGE_STATE_KEY = "pkg_state"
DEFAULT_PACKAGE_STATE = "present"
DEFAULT_PACKAGE_SUDO = True




FRECKLES_DEFAULT_FRECKLES_BOOTSTRAP_CONFIG_PATH = "freckles/.freckles/bootstrap.yml"


# FRECKLES_DEFAULT_PROFILE = "<all>"


FRECKLES_GROUP_DETAILS_FILENAME = "freckles"


FRECKLES_DEFAULT_HOSTS = ["localhost"]
FRECKLES_DEFAULT_EXECUTION_BASE_DIR = os.path.join(FRECKLES_DEFAULT_DIR, "cache")
# FRECKLES_DEFAULT_LOG_DIR = os.path.join(FRECKLES_DEFAULT_EXECUTION_BASE_DIR, "log")
# FRECKLES_DEFAULT_LOG_FILE = os.path.join(FRECKLES_DEFAULT_LOG_DIR, "freckles.log")
FRECKLES_DEFAULT_EXECUTION_DIR_NAME = "build"
FRECKLES_PLAYBOOK_DIR = "plays"
FRECKLES_PLAYBOOK_NAME = "freckles_playbook.yml"
FRECKLES_INVENTORY_DIR = "inventory"
FRECKLES_INVENTORY_FILE = "inventory.yml"
FRECKLES_EXECUTION_SCRIPT = "freckles_run.sh"
FRECKLES_DEFAULT_INSTALL_ROLE_NAME = "install-pkg"
FRECKLES_DEFAULT_INSTALL_ROLE_URL = "https://github.com/makkus/ansible-install-pkgs"
FRECKLES_DEFAULT_INSTALL_NIX_ROLE_NAME = "install-nix"
FRECKLES_DEFAULT_INSTALL_NIX_ROLE_URL = "https://github.com/makkus/ansible-nix-single"
DEFAULT_STOW_SUDO = False
FRECKLES_DEFAULT_STOW_ROLE_NAME = "stow-pkg"
FRECKLES_DEFAULT_STOW_ROLE_URL = "https://github.com/makkus/ansible-stow"
FRECKLES_DEFAULT_CHECKOUT_ROLE_NAME = "checkout"
FRECKLES_DEFAULT_CHECKOUT_ROLE_URL = "https://github.com/makkus/ansible-checkout"
FRECKLES_DEFAULT_DELETE_ROLE_NAME = "delete"
FRECKLES_DEFAULT_DELETE_ROLE_URL = "https://github.com/makkus/ansible-delete"
DEFAULT_STOW_TARGET_BASE_DIR = os.path.expanduser("~/")
STOW_TARGET_BASE_DIR_KEY = "stow_target_dir"

#DEFAULT_DOTFILES = [DEFAULT_DOTFILE_DIR]

PKGS_KEY = "pkgs"

DEFAULT_PACKAGE_STATE_KEY = "default_pkg_state"
DEFAULT_PACKAGE_SUDO_KEY = "default_pkg_sudo"




# FRECK_DEFAULT_PRIORITY_KEY = "default_freck_priority"

FRECK_DEFAULT_SUDO = False

DOTFILES_DIR_KEY = "dotfiles_dir"

DOTFILES_KEY = "dotfiles"



FRECK_CONFIG_TEMPLATE_KEY = "freck_config_template"

FRECKLES_CALLBACK_PLUGIN_NAME = "freckles_callback"



#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import click

FRECKLES_DEFAULT_GROUP_NAME = "freckles"
FRECKLES_METADATA_FILENAME = ".freckles"
FRECKLES_DEFAULT_PROFILE = "<all>"


FRECKLES_GROUP_DETAILS_FILENAME = "freckles"

FRECKLES_DEFAULT_DIR = click.get_app_dir('freckles', force_posix=True)
FRECKLES_DEFAULT_CONFIG_FILE_NAME = "localhost.yml"
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
DEFAULT_STOW_SUDO = False
FRECKLES_DEFAULT_STOW_ROLE_NAME = "stow-pkg"
FRECKLES_DEFAULT_STOW_ROLE_URL = "https://github.com/makkus/ansible-stow"
DEFAULT_STOW_TARGET_BASE_DIR = os.path.expanduser("~/")
STOW_TARGET_BASE_DIR_KEY = "stow_target_dir"
DEFAULT_DOTFILES = [os.path.expanduser("~/dotfiles")]
DEFAULT_PACKAGE_STATE = "present"
DEFAULT_PACKAGE_SUDO = True

PKGS_KEY = "pkgs"
PKG_MGR_KEY = "pkg_mgr"
DEFAULT_PACKAGE_STATE_KEY = "default_pkg_state"
DEFAULT_PACKAGE_SUDO_KEY = "default_pkg_sudo"
PACKAGE_STATE_KEY = "pkg_state"

FRECK_TYPE_KEY = "freck_type"

ANSIBLE_ROLE_NAME_KEY = "role"
ANSIBLE_ROLE_URL_KEY = "ansible_role_url"
# FRECK_DEFAULT_PRIORITY_KEY = "default_freck_priority"
FRECK_PRIORITY_KEY = "freck_priority"
FRECK_DEFAULT_PRIORITY = 10000
FRECK_SUDO_KEY = "freck_sudo"
FRECK_DEFAULT_SUDO = False
ITEM_NAME_KEY = "item_name"
DOTFILES_DIR_KEY = "dotfiles_dir"
DOTFILES_BASE_DIR_KEY = "dotfiles_base_dir"

DOTFILES_KEY = "dotfiles"

DOTFILES_BASE_KEY = "base_dir"
DOTFILES_PATHS_KEY = "paths"
DOTFILES_PATH_KEY = "dotfiles_path"
DOTFILES_REMOTE_KEY = "remote"

FRECKLES_CONFIG_ERROR_EXIT_CODE = 2

FRECK_CONFIG_TEMPLATE_KEY = "freck_config_template"

FRECKLES_CALLBACK_PLUGIN_NAME = "freckles_callback"

FRECKLES_ID_KEY = "freckles_id"

FRECKLES_STATE_SKIPPED = "skipped"
FRECKLES_STATE_KEY = "state"

FRECKLES_CHANGED_KEY = "changed"
FRECKLES_STATE_NO_CHANGE = "no change"
FRECKLES_STATE_CHANGED = "changed"
FRECKLES_STDOUT_KEY = "stdout"
FRECKLES_STDERR_KEY = "stderr"
FRECKLES_STATE_FAILED = "failed"

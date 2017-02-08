#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import click


# configuration constants
FRECKLES_DEFAULT_DIR = click.get_app_dir('freckles', force_posix=True)
DEFAULT_DOTFILE_DIR = os.path.expanduser("~/dotfiles")

# freckles filenames and extensions
FRECKLES_DEFAULT_CONFIG_FILE_NAME = "config.yml"
FRECKLES_METADATA_FILENAME = ".frkl"


# ERROR CODES
FRECKLES_CONFIG_ERROR_EXIT_CODE = 2
FRECKLES_EXECUTION_ERROR_EXIT_CODE = 4
FRECKLES_BUG_EXIT_CODE = 7


# freck configuration keys
FRECK_TYPE_KEY = "freck_type"
FRECK_NAME_KEY = "freck_name"
FRECK_ID_KEY = "freck_id"










FRECKLES_DEFAULT_DOTFILE_REPO_NAME = "dotfiles"
FRECKLES_DEFAULT_FRECKLES_CONFIG_PATH = "freckles/.freckles/default.yml"
FRECKLES_DEFAULT_FRECKLES_BOOTSTRAP_CONFIG_PATH = "freckles/.freckles/bootstrap.yml"


FRECKLES_DEFAULT_GROUP_NAME = "freckles"
#FRECKLES_DEFAULT_PROFILE = "<all>"


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
DEFAULT_DOTFILE_PATHS = []
#DEFAULT_DOTFILE_REMOTE = ""
#DEFAULT_DOTFILES = [DEFAULT_DOTFILE_DIR]
DEFAULT_PACKAGE_STATE = "present"
DEFAULT_PACKAGE_SUDO = True

PKGS_KEY = "pkgs"
PKG_MGR_KEY = "pkg_mgr"
DEFAULT_PACKAGE_STATE_KEY = "default_pkg_state"
DEFAULT_PACKAGE_SUDO_KEY = "default_pkg_sudo"
PACKAGE_STATE_KEY = "pkg_state"


ANSIBLE_ROLE_KEY = "role"
ANSIBLE_ROLES_KEY = "freck-roles"
# FRECK_DEFAULT_PRIORITY_KEY = "default_freck_priority"
FRECK_PRIORITY_KEY = "freck_priority"
FRECK_DEFAULT_PRIORITY = 10000
FRECK_SUDO_KEY = "freck_sudo"
FRECK_DEFAULT_SUDO = False
ITEM_NAME_KEY = "item_name"
DOTFILES_DIR_KEY = "dotfiles_dir"

DOTFILES_KEY = "dotfiles"

DOTFILES_BASE_KEY = "base_dir"
DOTFILES_PATHS_KEY = "paths"
DOTFILES_REMOTE_KEY = "remote"


FRECK_CONFIG_TEMPLATE_KEY = "freck_config_template"

FRECKLES_CALLBACK_PLUGIN_NAME = "freckles_callback"


FRECKLES_STATE_SKIPPED = "skipped"
FRECKLES_STATE_KEY = "state"

FRECKLES_CHANGED_KEY = "changed"
FRECKLES_STATE_NO_CHANGE = "no change"
FRECKLES_STATE_CHANGED = "changed"
FRECKLES_STDOUT_KEY = "stdout"
FRECKLES_STDERR_KEY = "stderr"
FRECKLES_STATE_FAILED = "failed"

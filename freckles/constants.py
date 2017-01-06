#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

FRECKLES_DEFAULT_GROUP_NAME = "freckles"
FRECKLES_METADATA_FILENAME = ".freckles"
FRECKLES_DEFAULT_PROFILE = "<all>"
FRECKLES_DEFAULT_PACKAGE_STATE = "present"
FRECKLES_DEFAULT_PACKAGE_SUDO = True
FRECKLES_GROUP_DETAILS_FILENAME = "freckles"

FRECKLES_DEFAULT_EXECUTION_BASE_DIR = os.path.expanduser("~/.cache/freckles")
FRECKLES_DEFAULT_EXECUTION_DIR_NAME = "build"
FRECKLES_PLAYBOOK_DIR = "plays"
FRECKLES_INSTALL_PLAYBOOK_NAME = "freckles_install_playbook.yml"
FRECKLES_STOW_PLAYBOOK_NAME = "freckles_stow_playbook.xml"
FRECKLES_INVENTORY_DIR = "inventory"
FRECKLES_INVENTORY_FILE = "inventory.yml"
FRECKLES_EXECUTION_SCRIPT = "freckles_run.sh"
FRECKLES_DEFAULT_INSTALL_ROLE_NAME = "ansible-freckles"
FRECKLES_DEFAULT_STOW_ROLE_NAME = "ansible-stow"
FRECKLES_DEFAULT_STOW_TARGET_BASE_DIR = os.path.expanduser("~/")

FRECKLES_DEFAULT_ANSIBLE_FRECKLES_ROLE_URL = "https://github.com/makkus/ansible-freckles"
FRECKLES_DEFAULT_ANSIBLE_STOW_ROLE_URL = "https://github.com/makkus/ansible-stow"

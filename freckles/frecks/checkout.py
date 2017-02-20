# -*- coding: utf-8 -*-
from freckles import Freck
from freckles.utils import parse_dotfiles_item, get_pkg_mgr_from_path, create_dotfiles_dict
import os
from freckles.constants import *
import sys
import copy
import logging
log = logging.getLogger("freckles")
from voluptuous import Schema, ALLOW_EXTRA, Any
from freckles.runners.ansible_runner import FRECK_ANSIBLE_ROLE_KEY, FRECK_ANSIBLE_ROLES_KEY

FRECKLES_DEFAULT_CHECKOUT_ROLE_NAME = "checkout"
FRECKLES_DEFAULT_CHECKOUT_ROLE_URL = "frkl:ansible-checkout"

class CheckoutDotfiles(Freck):

    def get_config_schema(self):
        return False

    def create_run_items(self, freck_name, freck_type, freck_desc, config):

        dotfiles = parse_dotfiles_item(config[DOTFILES_KEY])

        if len(dotfiles) == 0:
            return []

        dirs_used = []
        result = []
        for df in dotfiles:
            base_dir = df.get(DOTFILES_BASE_KEY, DEFAULT_DOTFILE_DIR)
            if base_dir in dirs_used:
                log.error("Basedir '{}' used more than once, this is not possible. Exiting...")
                sys.exit(FRECKLES_CONFIG_ERROR_EXIT_CODE)

            paths = df.get(DOTFILES_PATHS_KEY, [""])
            remote = df.get(DOTFILES_REMOTE_KEY, "")

            if not remote:
                continue

            temp_config = copy.copy(config)
            temp_config[DOTFILES_REMOTE_KEY] = remote
            temp_config[DOTFILES_BASE_KEY] = base_dir
            temp_config[INT_FRECK_ITEM_NAME_KEY] = "{} => {}".format(remote, base_dir)
            result.append(temp_config)

        return result

    def default_freck_config(self):

        return {
            FRECK_SUDO_KEY: False,
            DOTFILES_KEY: DEFAULT_DOTFILE_DIR,
            FRECK_RUNNER_KEY: FRECKLES_ANSIBLE_RUNNER,
            FRECK_ANSIBLE_ROLES_KEY: {FRECKLES_DEFAULT_CHECKOUT_ROLE_NAME: FRECKLES_DEFAULT_CHECKOUT_ROLE_URL},
            FRECK_ANSIBLE_ROLE_KEY: FRECKLES_DEFAULT_CHECKOUT_ROLE_NAME
        }

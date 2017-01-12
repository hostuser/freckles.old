# -*- coding: utf-8 -*-
from freckles import Freck
from freckles.utils import parse_dotfiles_item, get_pkg_mgr_from_path, create_dotfiles_dict
import os
from freckles.constants import *
import sys

import logging
log = logging.getLogger(__name__)

class Stow(Freck):

    def create_playbook_items(self, config):

        dotfiles = parse_dotfiles_item(config[DOTFILES_KEY])

        apps = create_dotfiles_dict(dotfiles, default_details=config)

        return apps.values()

    def default_freck_config(self):

        return {
            FRECK_SUDO_KEY: DEFAULT_STOW_SUDO,
            ANSIBLE_ROLE_NAME_KEY: FRECKLES_DEFAULT_STOW_ROLE_NAME,
            ANSIBLE_ROLE_URL_KEY: FRECKLES_DEFAULT_STOW_ROLE_URL,
            DOTFILES_KEY: DEFAULT_DOTFILES,
            STOW_TARGET_BASE_DIR_KEY: DEFAULT_STOW_TARGET_BASE_DIR
        }

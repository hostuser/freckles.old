# -*- coding: utf-8 -*-
from freckles import Freck
from freckles.utils import parse_dotfiles_item, get_pkg_mgr_from_path, create_dotfiles_dict, check_dotfile_items
import os
from freckles.constants import *
import sys

import logging
log = logging.getLogger(__name__)

class InstallNix(Freck):

    def create_playbook_items(self, config):

        if os.path.isdir("/nix") and os.access('/nix', os.W_OK):
            config[FRECK_SUDO_KEY] = False
        config[ITEM_NAME_KEY] = "single-user"
        return [config]

    def default_freck_config(self):

        return {
            FRECK_PRIORITY_KEY:100,
            FRECK_SUDO_KEY: True,
            ANSIBLE_ROLES_KEY:
            { FRECKLES_DEFAULT_INSTALL_NIX_ROLE_NAME: FRECKLES_DEFAULT_INSTALL_NIX_ROLE_URL },
            ANSIBLE_ROLE_KEY: FRECKLES_DEFAULT_INSTALL_NIX_ROLE_NAME

        }

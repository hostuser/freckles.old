# -*- coding: utf-8 -*-
from freckles import Freck
from freckles.utils import parse_dotfiles_item, get_pkg_mgr_from_path, create_dotfiles_dict, check_dotfile_items
import os
from freckles.constants import *
import sys
import copy
import logging
from voluptuous import Schema, ALLOW_EXTRA, Any
log = logging.getLogger(__name__)

class Delete(Freck):

    def get_config_schema(self):
        return False

    def create_playbook_items(self, config):

        result = []
        for f in config["files"]:
            temp_config = copy.copy(config)
            if os.path.isabs(f):
                temp_config[ITEM_NAME_KEY] = f
            else:
                temp_config[ITEM_NAME_KEY] = os.path.join(os.path.expanduser("~"), f)

            result.append(temp_config)

        return result

    def default_freck_config(self):

        return {
            FRECK_SUDO_KEY: False,
            ANSIBLE_ROLES_KEY: {
                FRECKLES_DEFAULT_DELETE_ROLE_NAME: FRECKLES_DEFAULT_DELETE_ROLE_URL },
            ANSIBLE_ROLE_KEY: FRECKLES_DEFAULT_DELETE_ROLE_NAME,
            FRECK_PRIORITY_KEY: FRECK_DEFAULT_PRIORITY+99
        }

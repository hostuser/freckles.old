# -*- coding: utf-8 -*-
import logging
import sys
from voluptuous import Schema, ALLOW_EXTRA, Any, Required

from freckles import Freck
from freckles.constants import *
from freckles.utils import parse_dotfiles_item, get_pkg_mgr_from_path, create_dotfiles_dict, get_pkg_mgr_from_marker_file, get_pkg_mgr_sudo, dict_merge, create_apps_dict
import copy

log = logging.getLogger("freckles")

ROLE_FRECK_ROLE_NAME = "freck_role"
ROLE_URL_KEY = "role_url"

class Role(Freck):

    def create_playbook_items(self, config):

        role = config[ROLE_URL_KEY]

        # we're going the opposite direction this time, filling up the 'default' runner values instead of reading them...

        roles_dict = { FRECK_ANSIBLE_ROLE_KEY: ROLE_FRECK_ROLE_NAME }
        roles_dict[FRECK_ANSIBLE_ROLES_KEY] = { ROLE_FRECK_ROLE_NAME: role }

        config[FRECK_RUNNER_KEY][FRECK_ANSIBLE_RUNNER] = roles_dict

        return [config]

    def default_freck_config(self):
        return {
            FRECK_SUDO_KEY: True,
            FRECK_RUNNER_KEY: {
                FRECK_ANSIBLE_RUNNER: {
                }
            }
        }

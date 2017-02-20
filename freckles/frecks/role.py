# -*- coding: utf-8 -*-
import logging
import sys
import copy
from voluptuous import Schema, ALLOW_EXTRA, Any, Required
from freckles.exceptions import FrecklesConfigError
from freckles import Freck
from freckles.constants import *
from freckles.runners.ansible_runner import FRECK_ANSIBLE_ROLE_KEY, FRECK_ANSIBLE_ROLES_KEY, ANSIBLE_TASK_TYPE, ANSIBLE_ROLE_TYPE, ROLE_ROLES_KEY, ROLE_TO_USE_KEY
from freckles.utils import parse_dotfiles_item, get_pkg_mgr_from_path, create_dotfiles_dict, get_pkg_mgr_from_marker_file, get_pkg_mgr_sudo, dict_merge, create_apps_dict
import copy


log = logging.getLogger("freckles")

ROLE_VARS_KEY = "role_vars"

class Role(Freck):

    def create_run_items(self, freck_name, freck_type, freck_desc, config):

        # we're going the opposite direction this time, filling up the 'default' runner values instead of reading them...

        if freck_type == ANSIBLE_ROLE_TYPE:
            role_to_use = freck_name
            role_vars = {}
        elif freck_type != FRECK_DEFAULT_TYPE:
            raise FrecklesConfigError("Freck type is neither {} nor {}, can't continue".format(FRECK_DEFAULT_TYPE, ANSIBLE_ROLE_TYPE), FRECK_TYPE_KEY, freck_type)
        else:
            role_to_use = config.get(ROLE_TO_USE_KEY, False)
            if not role_to_use:
                role_to_use = freck_name
            role_vars = config.get(ROLE_VARS_KEY, False)
            if not role_vars:
                role_vars = config

        roles = config[ROLE_ROLES_KEY]
        config[FRECK_ANSIBLE_ROLES_KEY] = roles
        config[FRECK_ANSIBLE_ROLE_KEY] = role_to_use

        if isinstance(role_vars, dict):
            # means only one freck
            dict_merge(config, role_vars)
            return [config]
        elif isinstance(role_vars, (list, tuple)):
            # means we'll create a bunch of frecks
            result = []
            for v in role_vars:
                role_config = copy.deepcopy(config)
                dict_merge(role_config, v)
                result.append(role_config)
            return result
        else:
            raise FrecklesConfigError("Can't figure out type of 'role_vars' value for role {}: {}". format(role_name, role_vars))

    def default_freck_config(self):
        return {
            FRECK_SUDO_KEY: True,
            FRECK_RUNNER_KEY: FRECKLES_ANSIBLE_RUNNER,
        }

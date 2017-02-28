# -*- coding: utf-8 -*-
import copy
import logging
import pprint
import sys

from freckles import Freck
from freckles.constants import *
from freckles.exceptions import FrecklesConfigError
from freckles.runners.ansible_runner import (ANSIBLE_ROLE_TYPE,
                                             ANSIBLE_TASK_TYPE,
                                             FRECK_META_ROLE_DICT_KEY,
                                             FRECK_META_ROLE_KEY,
                                             FRECK_META_ROLES_KEY,
                                             ROLE_ROLES_KEY, ROLE_TO_USE_KEY)
from freckles.utils import (create_apps_dict, create_dotfiles_dict, dict_merge,
                            get_pkg_mgr_from_marker_file,
                            get_pkg_mgr_from_path, get_pkg_mgr_sudo,
                            parse_dotfiles_item)
from voluptuous import ALLOW_EXTRA, Any, Required, Schema

log = logging.getLogger("freckles")

ROLE_VARS_KEY = "role_vars"

class Role(Freck):

    def can_be_used_for(self, freck_meta):

        can = TASK_NAME_KEY in freck_meta.keys() and FRECK_META_ROLES_KEY in freck_meta.keys() and freck_meta[TASK_NAME_KEY] in freck_meta[FRECK_META_ROLES_KEY].keys()
        return can

    def create_run_item(self, freck_meta, develop=False):

        role = freck_meta[TASK_NAME_KEY]

        freck_meta[FRECK_META_ROLE_KEY] = role
        freck_meta[FRECK_ITEM_NAME_KEY] = role
        freck_meta[FRECK_DESC_KEY] = "applying role"
        freck_meta[FRECK_META_ROLE_DICT_KEY] = {"role": role}


        # pprint.pprint(freck_meta)
        return freck_meta

    def default_freck_config(self):
        return {
        }

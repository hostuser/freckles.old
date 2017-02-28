# -*- coding: utf-8 -*-
import abc
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

class AbstractRole(Freck):

    def can_be_used_for(self, freck_meta):

        return False

    @abc.abstractmethod
    def get_role(self, freck_meta):
        pass

    def get_desc(self, freck_meta):
        return False

    def get_item_name(self, freck_meta):
        return False

    def get_additional_roles(self, freck_meta):
        return False

    def get_sudo(self, freck_meta):
        return True

    def create_run_item(self, freck_meta, develop=False):

        role = self.get_role(freck_meta)

        freck_meta[FRECK_META_ROLE_KEY] = role
        item_name = self.get_item_name(freck_meta)
        if not item_name:
            item_name = role
        freck_meta[FRECK_ITEM_NAME_KEY] = item_name
        desc = self.get_desc(freck_meta)
        if not desc:
            desc = "applying role"
        freck_meta[FRECK_DESC_KEY] = desc
        freck_meta[FRECK_META_ROLE_DICT_KEY] = {"role": role}

        freck_meta[FRECK_SUDO_KEY] = self.get_sudo(freck_meta)

        additional_roles = self.get_additional_roles(freck_meta)
        if additional_roles:
            roles = freck_meta.get(FRECK_META_ROLES_KEY, {})
            dict_merge(roles, additional_roles)
            freck_meta[FRECK_META_ROLES_KEY] = roles

        return freck_meta


class Role(AbstractRole):

    def can_be_used_for(self, freck_meta):
        can = TASK_NAME_KEY in freck_meta.keys() and FRECK_META_ROLES_KEY in freck_meta.keys() and freck_meta[TASK_NAME_KEY] in freck_meta[FRECK_META_ROLES_KEY].keys()
        return can

    def get_role(self, freck_meta):
        return freck_meta[TASK_NAME_KEY]

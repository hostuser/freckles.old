# -*- coding: utf-8 -*-
import abc
import copy
import logging
import pprint
import sys

from freckles import Freck
from freckles.constants import *
from freckles.exceptions import FrecklesConfigError
from freckles.runners.ansible_runner import (ANSIBLE_ROLE_PROCESSED,
                                             ANSIBLE_ROLE_TYPE,
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

    def get_additional_vars(self, freck_meta):
        return False

    def get_unique_task_id(self, freck_meta):
        return False

    @staticmethod
    def create_role_dict(role, item_name=None, desc=None, sudo=True, additional_roles={}, additional_vars={}, unique_task_id=False):

        freck_meta = {}
        freck_meta[FRECK_META_ROLE_KEY] = role
        if not item_name:
            item_name = role
        freck_meta[FRECK_ITEM_NAME_KEY] = item_name
        if not desc:
            desc = "applying role"
        freck_meta[FRECK_DESC_KEY] = desc
        freck_meta[FRECK_META_ROLE_DICT_KEY] = {"role": role}

        freck_meta[FRECK_SUDO_KEY] = sudo

        if additional_roles:
            roles = freck_meta.get(FRECK_META_ROLES_KEY, {})
            dict_merge(additional_roles, roles)
            freck_meta[FRECK_META_ROLES_KEY] = additional_roles

        if additional_vars:
            vars = freck_meta.get(FRECK_VARS_KEY, {})
            dict_merge(additional_vars, vars)
            freck_meta[FRECK_VARS_KEY] = additional_vars

        freck_meta[FRECK_NAME_KEY] = ANSIBLE_ROLE_TYPE
        freck_meta[ANSIBLE_ROLE_PROCESSED] = True

        if unique_task_id:
            freck_meta[UNIQUE_TASK_ID_KEY] = unique_task_id

        return freck_meta

    def create_run_item(self, freck_meta, develop=False):

        if freck_meta.get(ANSIBLE_ROLE_PROCESSED, False):
            return freck_meta

        role = self.get_role(freck_meta)

        item_name = self.get_item_name(freck_meta)
        desc = self.get_desc(freck_meta)

        sudo = self.get_sudo(freck_meta)

        additional_roles = self.get_additional_roles(freck_meta)
        if additional_roles:
            dict_merge(additional_roles, freck_meta.get(FRECK_META_ROLES_KEY, {}))
        else:
            additional_roles = freck_meta.get(FRECK_META_ROLES_KEY, {})

        additional_vars = self.get_additional_vars(freck_meta)
        if additional_vars:
            dict_merge(additional_vars, freck_meta.get(FRECK_VARS_KEY, {}))
        else:
            additional_vars = freck_meta.get(FRECK_VARS_KEY, {})

        unique_task_id = self.get_unique_task_id(freck_meta)
        if not unique_task_id:
            unique_task_id = freck_meta.get(UNIQUE_TASK_ID_KEY, False)

        freck_meta = AbstractRole.create_role_dict(role, item_name=item_name, desc=desc, sudo=sudo, additional_roles=additional_roles, additional_vars=additional_vars, unique_task_id=unique_task_id)

        return freck_meta


class Role(AbstractRole):

    def can_be_used_for(self, freck_meta):
        can = TASK_NAME_KEY in freck_meta.keys() and FRECK_META_ROLES_KEY in freck_meta.keys() and freck_meta[TASK_NAME_KEY] in freck_meta[FRECK_META_ROLES_KEY].keys()
        return can

    def get_role(self, freck_meta):
        return freck_meta[TASK_NAME_KEY]

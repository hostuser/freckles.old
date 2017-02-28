# -*- coding: utf-8 -*-
import abc
import copy
import logging
import pprint
import sys

import click

from freckles import Freck
from freckles.constants import *
from freckles.exceptions import FrecklesConfigError
from freckles.runners.ansible_runner import (ANSIBLE_TASK_TYPE,
                                             FRECK_META_ROLE_DICT_KEY,
                                             FRECK_META_ROLE_KEY,
                                             FRECK_META_ROLES_KEY,
                                             FRECK_META_TASKS_KEY,
                                             FRECK_META_TYPE_KEY,
                                             TASK_BECOME_KEY,
                                             TASK_DEFAULT_BECOME,
                                             TASK_TEMPLATE_KEYS)
from freckles.utils import (create_apps_dict, create_dotfiles_dict, dict_merge,
                            get_pkg_mgr_from_marker_file,
                            get_pkg_mgr_from_path, get_pkg_mgr_sudo,
                            parse_dotfiles_item)
from voluptuous import ALLOW_EXTRA, Any, Required, Schema

log = logging.getLogger("freckles")


GENERATED_ROLE_ID_COUNTER = 1
GENERATED_ROLE_NAME_PREFIX = "custom_role"


class AbstractTask(Freck):
    """Generic task neck that can be used directly, or overwritten for more custom stuff.

    """

    def get_task_name(self, freck_meta):
        return False

    def get_task_desc(self, freck_meta):
        return False

    def get_task_become(self, freck_meta):
        return False

    def get_task_vars(self, freck_meta):
        return False

    def get_task_template_keys(self, freck_meta):
        return False

    def get_additional_roles(self, freck_meta):
        return {}

    def get_item_name(self, freck_meta):
        return False

    def create_run_item(self, freck_meta, develop=False):

        global GENERATED_ROLE_ID_COUNTER

        freck_name = self.get_task_name(freck_meta) or freck_meta[FRECK_NAME_KEY]
        freck_desc = self.get_task_desc(freck_meta) or freck_meta[FRECK_DESC_KEY]
        task_name = self.get_task_name(freck_meta) or freck_meta[TASK_NAME_KEY]
        become = self.get_task_become(freck_meta) or freck_meta[FRECK_SUDO_KEY]
        vars = self.get_task_vars(freck_meta) or freck_meta[FRECK_VARS_KEY]
        item_name = self.get_item_name(freck_meta) or freck_meta[FRECK_ITEM_NAME_KEY] or freck_name
        template_keys = self.get_task_template_keys(freck_meta) or vars.keys()
        task = {"name": freck_desc, "type": task_name, "task": {"vars": {"role_{0:04d}_task_{1:06d}".format(GENERATED_ROLE_ID_COUNTER, 1): copy.deepcopy(template_keys)}, "become": become}}
        role_name = "{}_{}".format(GENERATED_ROLE_NAME_PREFIX, GENERATED_ROLE_ID_COUNTER)
        add_roles = self.get_additional_roles(freck_meta)
        if add_roles:
            add_roles.update(freck_meta.get(RESULT_ROLES_KEY, {}))

        result = {}
        result[FRECK_NAME_KEY] = freck_name
        result[FRECK_DESC_KEY] = freck_desc
        result[TASK_NAME_KEY] = task_name
        result[FRECK_SUDO_KEY] = become
        result[FRECK_VARS_KEY] = vars
        result[TASK_TEMPLATE_KEYS] = template_keys

        result[FRECK_META_TASKS_KEY] = {
            role_name: [task]
        }
        result[FRECK_META_ROLE_DICT_KEY] = {"role": role_name}
        result[FRECK_META_ROLES_KEY] = add_roles
        result[FRECK_ITEM_NAME_KEY] = item_name
        result[FRECK_ID_KEY] = freck_meta[FRECK_ID_KEY]

        GENERATED_ROLE_ID_COUNTER = GENERATED_ROLE_ID_COUNTER + 1

        return result


class Task(AbstractTask):
    """Generic task neck that can be used directly, or overwritten for more custom stuff.

    """

    def can_be_used_for(self, freck_meta):
        return True

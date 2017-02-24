# -*- coding: utf-8 -*-
import copy
import logging
import sys

from freckles import Freck
from freckles.constants import *
from freckles.exceptions import FrecklesConfigError
from freckles.runners.ansible_runner import (ANSIBLE_TASK_TYPE,
                                             FRECK_META_ROLE_KEY,
                                             FRECK_META_ROLES_KEY,
                                             FRECK_META_TASKS_KEY,
                                             FRECK_META_TYPE_KEY)
from freckles.utils import (create_apps_dict, create_dotfiles_dict, dict_merge,
                            get_pkg_mgr_from_marker_file,
                            get_pkg_mgr_from_path, get_pkg_mgr_sudo,
                            parse_dotfiles_item)
from voluptuous import ALLOW_EXTRA, Any, Required, Schema

log = logging.getLogger("freckles")

TASKS_NAME_KEY = "tasks"

GENERATED_ROLE_ID_COUNTER = 1

class Task(Freck):

    def create_run_items(self, freck_meta, config):

        global GENERATED_ROLE_ID_COUNTER

        freck_type = freck_meta[FRECK_META_TYPE_KEY]
        freck_name = freck_meta[FRECK_NAME_KEY]
        freck_desc = freck_meta[FRECK_DESC_KEY]

        task = {"name": freck_desc, "type": freck_name, "task": {"run_{0:04d}_task_{1:06d}".format(GENERATED_ROLE_ID_COUNTER, 1): copy.deepcopy(config)}}

        GENERATED_ROLE_ID_COUNTER = GENERATED_ROLE_ID_COUNTER + 1

        freck_meta[FRECK_META_TASKS_KEY] = [task]

        freck_meta[FRECK_ITEM_NAME_KEY] = freck_name
        freck_meta[FRECK_DESC_KEY] = "ansible task"

        return [freck_meta]


    def default_freck_config(self):
        return {
        }

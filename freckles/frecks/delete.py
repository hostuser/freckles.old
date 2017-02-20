# -*- coding: utf-8 -*-
import copy
import logging

import os

from freckles import Freck
from freckles.constants import *
from freckles.runners.ansible_runner import FRECK_ANSIBLE_ROLE_KEY, FRECK_ANSIBLE_ROLES_KEY

log = logging.getLogger("freckles")
FILES_TO_DELETE_KEY = "files-to-delete"

FRECKLES_DEFAULT_DELETE_ROLE_NAME = "delete"
FRECKLES_DEFAULT_DELETE_ROLE_URL = "frkl:ansible-delete"

class Delete(Freck):

    def get_config_schema(self):
        return False

    def create_run_items(self, freck_name, freck_type, freck_desc, config):

        result = []
        for f in config[FILES_TO_DELETE_KEY]:
            temp_config = copy.copy(config)
            if f.startswith("~"):
                temp_config[INT_FRECK_ITEM_NAME_KEY] = os.path.expanduser(f)
            elif os.path.isabs(f):
                temp_config[INT_FRECK_ITEM_NAME_KEY] = f
            else:
                temp_config[INT_FRECK_ITEM_NAME_KEY] = os.path.join(os.path.expanduser("~"), f)

            result.append(temp_config)

        return result

    def default_freck_config(self):

        return {
            FRECK_SUDO_KEY: False,
            FRECK_PRIORITY_KEY: FRECK_DEFAULT_PRIORITY+99,
            FRECK_RUNNER_KEY: FRECKLES_ANSIBLE_RUNNER,
            FRECK_ANSIBLE_ROLES_KEY: {
                FRECKLES_DEFAULT_DELETE_ROLE_NAME: FRECKLES_DEFAULT_DELETE_ROLE_URL },
            FRECK_ANSIBLE_ROLE_KEY: FRECKLES_DEFAULT_DELETE_ROLE_NAME
        }

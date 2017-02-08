# -*- coding: utf-8 -*-
import copy
import logging

from freckles import Freck
from freckles.constants import *

log = logging.getLogger("freckles")

class Delete(Freck):

    def get_config_schema(self):
        return False

    def create_playbook_items(self, config):

        result = []
        for f in config["files"]:
            temp_config = copy.copy(config)
            if os.path.isabs(f):
                temp_config[FRECK_ITEM_NAME_KEY] = f
            else:
                temp_config[FRECK_ITEM_NAME_KEY] = os.path.join(os.path.expanduser("~"), f)

            result.append(temp_config)

        return result

    def default_freck_config(self):

        return {
            FRECK_SUDO_KEY: False,
            FRECK_ANSIBLE_ROLES_KEY: {
                FRECKLES_DEFAULT_DELETE_ROLE_NAME: FRECKLES_DEFAULT_DELETE_ROLE_URL },
            FRECK_ANSIBLE_ROLE_KEY: FRECKLES_DEFAULT_DELETE_ROLE_NAME,
            FRECK_PRIORITY_KEY: FRECK_DEFAULT_PRIORITY+99
        }

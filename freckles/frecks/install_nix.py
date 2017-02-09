# -*- coding: utf-8 -*-
import logging

from freckles import Freck
from freckles.constants import *

log = logging.getLogger("freckles")

class InstallNix(Freck):

    def get_config_schema(self):
        return False

    def create_playbook_items(self, config):

        if os.path.isdir("/nix") and os.access('/nix', os.W_OK):
            config[FRECK_SUDO_KEY] = False
        config[FRECK_ITEM_NAME_KEY] = "single-user"
        return [config]

    def default_freck_config(self):

        return {
            FRECK_PRIORITY_KEY:100,
            FRECK_SUDO_KEY: True,
            FRECK_RUNNER_KEY: {
                FRECK_ANSIBLE_RUNNER: {
                    FRECK_ANSIBLE_ROLES_KEY: {
                        FRECKLES_DEFAULT_INSTALL_NIX_ROLE_NAME: FRECKLES_DEFAULT_INSTALL_NIX_ROLE_URL},
                    FRECK_ANSIBLE_ROLE_KEY: FRECKLES_DEFAULT_INSTALL_NIX_ROLE_NAME
                }
            }
        }

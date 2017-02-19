# -*- coding: utf-8 -*-
import logging

from freckles import Freck
from freckles.constants import *
from freckles.runners.ansible_runner import FRECK_ANSIBLE_ROLE_KEY, FRECK_ANSIBLE_ROLES_KEY

log = logging.getLogger("freckles")

FRECKLES_DEFAULT_INSTALL_PKG_MGRS_ROLE_NAME = "install-pkg-mgrs"
FRECKLES_DEFAULT_INSTALL_PKG_MGRS_ROLE_URL = "frkl:ansible-install-pkg-mgrs"

class InstallPkgMgrs(Freck):

    def get_config_schema(self):
        return False

    def create_run_items(self, config):


        while True:
            try:
                config.get(PKG_MGRS_KEY, []).remove("default")
            except ValueError:
                break

        if not config.get(PKG_MGRS_KEY, False):
            return []

        if "nix" in config.get(PKG_MGRS_KEY, []):
            if not os.path.isdir("/nix") or not os.access('/nix', os.W_OK):
                config[FRECK_SUDO_KEY] = True
        config[FRECK_ITEM_NAME_KEY] = "{}".format(", ".join(config.get(PKG_MGRS_KEY)))
        return [config]

    def default_freck_config(self):

        return {
            FRECK_PRIORITY_KEY:100,
            FRECK_SUDO_KEY: False,
            FRECK_RUNNER_KEY: FRECKLES_ANSIBLE_RUNNER,
            FRECK_ANSIBLE_ROLES_KEY: {
                FRECKLES_DEFAULT_INSTALL_PKG_MGRS_ROLE_NAME: FRECKLES_DEFAULT_INSTALL_PKG_MGRS_ROLE_URL},
            FRECK_ANSIBLE_ROLE_KEY: FRECKLES_DEFAULT_INSTALL_PKG_MGRS_ROLE_NAME
        }

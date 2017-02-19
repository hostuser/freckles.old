# -*- coding: utf-8 -*-
import logging

from freckles import Freck

log = logging.getLogger("freckles")

class DebugVars(Freck):

    def get_config_scheme(self):
        return False

    def create_run_items(self, config):

        log.debug("Entering debug create_playbook_items...")
        log.debug(config)
        log.debug("Finished debug create_playbook_items.")
        return []

    def default_freck_config(self):

        return {}

# -*- coding: utf-8 -*-
from freckles import Freck
from freckles.utils import parse_dotfiles_item, get_pkg_mgr_from_path, create_dotfiles_dict, check_dotfile_items
import os
from freckles.constants import *
import sys
import copy
from voluptuous import Schema, ALLOW_EXTRA, Any
import logging
log = logging.getLogger("freckles")

class DebugVars(Freck):

    def get_config_scheme(self):
        return False

    def create_playbook_items(self, config):

        log.debug("Entering debug create_playbook_items...")
        log.debug(config)
        log.debug("Finished debug create_playbook_items.")
        return []

    def default_freck_config(self):

        return {}

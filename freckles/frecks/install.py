# -*- coding: utf-8 -*-
from freckles.freckles import Freck, ANSIBLE_ROLE_NAME_KEY, FRECK_PRIORITY_KEY, FRECK_DEFAULT_PRIORITY, FRECK_SUDO_KEY
from freckles.utils import parse_dotfiles_item, get_pkg_mgr_from_path, create_dotfiles_dict
import os
from freckles.constants import *
import sys

import logging
log = logging.getLogger(__name__)

class Install(Freck):

    def create_playbook_items(self, config):

        dotfiles = parse_dotfiles_item(config[DOTFILES_KEY])

        apps = create_dotfiles_dict(dotfiles, default_details=config)

        for app, details in apps.iteritems():

            # if the path of the dotfile dir contains either 'deb', 'rpm', or 'nix', use this as the default package manager. Can still be overwritten by metadata file
            if not details.get(PKG_MGR_KEY, False):
                pkg_mgr = get_pkg_mgr_from_path(details[DOTFILES_DIR_KEY])
                if pkg_mgr:
                    details[PKG_MGR_KEY] = pkg_mgr

            # check if pkgs key exists
            if not details.get(PKGS_KEY, False):
                details[PKGS_KEY] = {"default": [details[APP_NAME_KEY]]}

            # check if 'pkgs' key is a dict, if not, use its value and put it into the 'default' key
            if not type(details["pkgs"]) == dict:
                temp = details["pkgs"]
                details["pkgs"] = {}
                details["pkgs"]["default"] = temp

            # check if an 'default' pkgs key exists, if not, use the package name
            if not details.get("pkgs").get("default", False):
                details["pkgs"]["default"] = [details[APP_NAME_KEY]]

        return apps.values()

    def default_freck_config(self):

        return {
            PACKAGE_STATE_KEY: DEFAULT_PACKAGE_STATE,
            FRECK_SUDO_KEY: DEFAULT_PACKAGE_SUDO,
            ANSIBLE_ROLE_NAME_KEY: FRECKLES_DEFAULT_INSTALL_ROLE_NAME,
            ANSIBLE_ROLE_URL_KEY: FRECKLES_DEFAULT_INSTALL_ROLE_URL,
            DOTFILES_KEY: DEFAULT_DOTFILES
        }

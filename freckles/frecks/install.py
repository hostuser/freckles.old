# -*- coding: utf-8 -*-
from freckles import Freck
from freckles.utils import parse_dotfiles_item, get_pkg_mgr_from_path, create_dotfiles_dict, check_dotfile_items, get_pkg_mgr_from_marker_file, get_pkg_mgr_sudo
import os
from freckles.constants import *
import sys

import logging
log = logging.getLogger(__name__)

class Install(Freck):

    def create_playbook_items(self, config):

        dotfiles = parse_dotfiles_item(config[DOTFILES_KEY])
        existing_dotfiles = check_dotfile_items(dotfiles)

        if not existing_dotfiles:
            # log.info("\t -> No existing or configured dotfile directories. Not installing anything...")
            return []

        apps = create_dotfiles_dict(dotfiles, default_details=config)

        for app, details in apps.iteritems():

            # if the path of the dotfile dir contains either 'deb', 'rpm', or 'nix', use this as the default package manager. Can still be overwritten by metadata file
            if not details.get(PKG_MGR_KEY, False):
                pkg_mgr = get_pkg_mgr_from_path(details[DOTFILES_DIR_KEY])
                if pkg_mgr:
                    details[PKG_MGR_KEY] = pkg_mgr
                 # if the folder contains a file called .nix.frkl or .no_install.frkl or .conda.frkl than that can determine the pkg mgr too, and it'd override the path
                pkg_mgr = get_pkg_mgr_from_marker_file(details[DOTFILES_DIR_KEY])
                if pkg_mgr:
                     details[PKG_MGR_KEY] = pkg_mgr

            # check if pkgs key exists
            if not details.get(PKGS_KEY, False):
                details[PKGS_KEY] = {"default": [details[ITEM_NAME_KEY]]}

            if details.get(PKG_MGR_KEY, False):
                sudo = get_pkg_mgr_sudo(details[PKG_MGR_KEY])
                details[FRECK_SUDO_KEY] = sudo

            # check if 'pkgs' key is a dict, if not, use its value and put it into the 'default' key
            if not type(details["pkgs"]) == dict:
                temp = details["pkgs"]
                details["pkgs"] = {}
                details["pkgs"]["default"] = temp

            # check if an 'default' pkgs key exists, if not, use the package name
            if not details.get("pkgs").get("default", False):
                details["pkgs"]["default"] = [details[ITEM_NAME_KEY]]

        return apps.values()

    def handle_task_output(self, task, output_details):

        state = FRECKLES_STATE_SKIPPED
        changed = False
        failed = False
        stderr = []
        for details in output_details:

            if details[FRECKLES_STATE_KEY] == FRECKLES_STATE_SKIPPED:
                continue
            elif details[FRECKLES_STATE_KEY] == FRECKLES_STATE_FAILED:
                state = FRECKLES_STATE_FAILED
                if details["result"].get("msg", False):
                    stderr.append(details["result"]["msg"])
                for r in  details["result"].get("results", []):
                    if r.get("msg", False):
                        stderr.append(r["msg"])

            else:
            # this is the one we are interested in, there should only be one, right?
                temp_changed = details["result"][FRECKLES_CHANGED_KEY]
                if temp_changed:
                    pkg_mgr = details["action"]
                    state = "installed (using '{}')".format(pkg_mgr)
                    changed = True
                else:
                    state = "already present"

                break

        return {FRECKLES_STATE_KEY: state, FRECKLES_CHANGED_KEY: changed, FRECKLES_STDERR_KEY: stderr}

    def default_freck_config(self):

        return {
            PACKAGE_STATE_KEY: DEFAULT_PACKAGE_STATE,
            FRECK_SUDO_KEY: DEFAULT_PACKAGE_SUDO,
            ANSIBLE_ROLES_KEY:
            { FRECKLES_DEFAULT_INSTALL_ROLE_NAME: FRECKLES_DEFAULT_INSTALL_ROLE_URL },
            ANSIBLE_ROLE_KEY: FRECKLES_DEFAULT_INSTALL_ROLE_NAME

        }

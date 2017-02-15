# -*- coding: utf-8 -*-
import logging
import sys
from voluptuous import Schema, ALLOW_EXTRA, Any, Required

from freckles import Freck
from freckles.constants import *
from freckles.utils import parse_dotfiles_item, get_pkg_mgr_from_path, create_dotfiles_dict, get_pkg_mgr_from_marker_file, get_pkg_mgr_sudo, dict_merge, create_apps_dict
import copy

log = logging.getLogger("freckles")

SUPPORTED_PKG_MGRS = ["deb", "rpm", "nix", "no_install", "conda", "default"]
INSTALL_IGNORE_KEY = "no_install"
ACTION_KEY = "install_action"
PKGS_KEY = "pkgs"   # this is the key that is used in the role

FRECKLES_DEFAULT_INSTALL_ROLE_NAME = "install-pkg"
FRECKLES_DEFAULT_INSTALL_ROLE_URL = "https://github.com/makkus/ansible-install-pkgs"

class Install(Freck):

    def get_config_schema(self):

        s = Schema({
            Required(DOTFILES_KEY): list,
            PKG_MGR_KEY: Any(*SUPPORTED_PKG_MGRS),
            PKGS_KEY: dict
        }, extra=ALLOW_EXTRA)

        return s

    def pre_process_config(self, config):

        ignore_list = config.get(INSTALL_IGNORE_KEY, [])
        # check whether there are non-dotfile apps to isntall
        if config.get(PACKAGES_KEY, False):
            apps = create_apps_dict(config[PACKAGES_KEY], default_details=config)
        else:
           dotfiles = parse_dotfiles_item(config[DOTFILES_KEY])
           # existing_dotfiles = check_dotfile_items(dotfiles)
           # if not existing_dotfiles:
               # log.info("\t -> No existing or configured dotfile directories. Not installing anything...")
               # return False
           apps = create_dotfiles_dict(dotfiles, default_details=config)

        configs = []

        for app, details in apps.iteritems():
            if app in ignore_list:
                continue

            # if the path of the dotfile dir contains either 'deb', 'rpm', or 'nix', use this as the default package manager. Can still be overwritten by metadata file
            if not details.get(PKG_MGR_KEY, False):
                dotfiles_dir = details.get(DOTFILES_DIR_KEY, False)
                if dotfiles_dir:
                    pkg_mgr = get_pkg_mgr_from_path(dotfiles_dir)
                    if pkg_mgr:
                        details[PKG_MGR_KEY] = pkg_mgr
                    # if the folder contains a file called .nix.frkl or .no_install.frkl or .conda.frkl than that can determine the pkg mgr too, and it'd override the path
                    pkg_mgr = get_pkg_mgr_from_marker_file(details.get(DOTFILES_DIR_KEY, False))
                    if pkg_mgr:
                        details[PKG_MGR_KEY] = pkg_mgr

            # check if pkgs key exists
            if not details.get(PKGS_KEY, False):
                details[PKGS_KEY] = {"default": [details[FRECK_ITEM_NAME_KEY]]}

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
                details["pkgs"]["default"] = [details[FRECK_ITEM_NAME_KEY]]

            configs.append(details)

        return configs

    def create_playbook_items(self, config):

        return [config]

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
            DOTFILES_KEY: [DEFAULT_DOTFILE_DIR],
            PACKAGE_STATE_KEY: DEFAULT_PACKAGE_STATE,
            FRECK_SUDO_KEY: DEFAULT_PACKAGE_SUDO,
            ACTION_KEY: "install",
            FRECK_RUNNER_KEY: {
                FRECK_ANSIBLE_RUNNER: {
                    FRECK_ANSIBLE_ROLES_KEY: { FRECKLES_DEFAULT_INSTALL_ROLE_NAME: FRECKLES_DEFAULT_INSTALL_ROLE_URL },
                    FRECK_ANSIBLE_ROLE_KEY: FRECKLES_DEFAULT_INSTALL_ROLE_NAME
                }
            }
        }


class Update(Freck):

    def pre_process_config(self, config):

        result = []
        for pkg_mgr in config.get("pkg_mgrs", ["default"]):
            details = copy.deepcopy(config)
            if pkg_mgr != "default":
                details[PKG_MGR_KEY] = pkg_mgr

            details[FRECK_ITEM_NAME_KEY] = "update {} package cache".format(pkg_mgr)
            result.append(details)

        return result

    def create_playbook_items(self, config):

        return [config]

    def default_freck_config(self):
        return {
            FRECK_SUDO_KEY: DEFAULT_PACKAGE_SUDO,
            ACTION_KEY: "update_cache",
            FRECK_RUNNER_KEY: {
                FRECK_ANSIBLE_RUNNER: {
                    FRECK_ANSIBLE_ROLES_KEY: { FRECKLES_DEFAULT_INSTALL_ROLE_NAME: FRECKLES_DEFAULT_INSTALL_ROLE_URL },
                    FRECK_ANSIBLE_ROLE_KEY: FRECKLES_DEFAULT_INSTALL_ROLE_NAME
                }
            }
        }


class Upgrade(Freck):

    def pre_process_config(self, config):

        result = []
        for pkg_mgr in config.get("pkg_mgrs", ["default"]):
            details = copy.deepcopy(config)
            details[PKG_MGR_KEY] = pkg_mgr

            details[FRECK_ITEM_NAME_KEY] = "upgrade {} packages".format(pkg_mgr)
            result.append(details)

        return result

    def create_playbook_items(self, config):

        return [config]

    def default_freck_config(self):
        return {
            FRECK_SUDO_KEY: DEFAULT_PACKAGE_SUDO,
            ACTION_KEY: "upgrade",
            FRECK_RUNNER_KEY: {
                FRECK_ANSIBLE_RUNNER: {
                    FRECK_ANSIBLE_ROLES_KEY: { FRECKLES_DEFAULT_INSTALL_ROLE_NAME: FRECKLES_DEFAULT_INSTALL_ROLE_URL },
                    FRECK_ANSIBLE_ROLE_KEY: FRECKLES_DEFAULT_INSTALL_ROLE_NAME
                }
            }
        }

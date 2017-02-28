# -*- coding: utf-8 -*-
import copy
import logging
import platform
import pprint
import sys

from ansible.module_utils.facts import Distribution
from freckles import Freck
from freckles.constants import *
from freckles.exceptions import FrecklesConfigError
from freckles.runners.ansible_runner import (FRECK_META_ROLE_KEY,
                                             FRECK_META_ROLES_KEY)
from freckles.utils import (create_apps_dict, create_dotfiles_dict, dict_merge,
                            get_pkg_mgr_from_marker_file,
                            get_pkg_mgr_from_path, get_pkg_mgr_sudo,
                            parse_dotfiles_item)
from role import Role
from sets import Set
from task import AbstractTask
from voluptuous import ALLOW_EXTRA, Any, Required, Schema

log = logging.getLogger("freckles")

SUPPORTED_PKG_MGRS = ["apt", "yum", "nix", "pip", "git", "no_install", "conda", "brew", "default"]
DEFAULT_PKG_MGRS = {
    "Debian": "apt",
    "RedHat": "yum",
    "Darwin": "brew"
}

PKG_MGRS_COMMANDS = {
    "apt": {"update": {"update_cache": True}, "upgrade": {"upgrade": "dist"}},
    "yum": {"update": False, "upgrade": {"name": "'*'", "state": "latest"}},
    "nix": {"update": {"update_cache": True}, "upgrade": {"upgrade": True}},
    "conda": {"update": False, "upgrade": {"upgrade": True}},
    "brew": {"update": {"update_homebrew": True, "upgrade_homebrew": False}, "upgrade": {"upgrade_all": True, "update_homebrew": False}}
}

INSTALL_IGNORE_KEY = "no_install"
ACTION_KEY = "install_action"
PKGS_KEY = "pkgs"   # this is the key that is used in the role

USE_DOTFILES_KEY = "use_dotfiles"
USE_DOTFILES_DEFAULT = False
USE_PACKAGES_KEY = "use_packages_var"
USE_PACKAGES_DEFAULT = True

ENSURE_PACKAGE_MANAGER_KEY = "ensure_pkg_manager"
ENSURE_PACKAGE_MANAGER_DEFAULT = False

UPDATE_PACKAGE_CACHE_KEY = "update_cache"
UPDATE_PACKAGE_CACHE_DEFAULT = False
UPGRADE_PACKAGES_KEY = "upgrade_packages"
UPGRADE_PACKAGES_DEFAULT = False

PRIORITY_SOURCE_KEY = "priority_source"
PRIORITY_SOURCE_DEFAULT = PACKAGES_KEY

FRECKLES_DEFAULT_INSTALL_ROLE_NAME = "install-pkg"
FRECKLES_DEFAULT_INSTALL_ROLE_URL = "frkl:ansible-install-pkgs"

FRECKLES_DEFAULT_INSTALL_PKG_MGRS_ROLE_NAME = "install-pkg-mgrs"
FRECKLES_DEFAULT_INSTALL_PKG_MGRS_ROLE_URL = "frkl:ansible-install-pkg-mgrs"

ADD_PKG_MGR_PATH_KEY = "add_path"
ADD_PKG_MGR_PATH_DEFAULT = True
ADD_PKG_MGR_PATH_DEFAULT_WHEN_AUTO_INSTALL_PKG_MGR = False

GIT_CONFIG_UPDATE_DEFAULT = True

INSTALL_BREW_KEY = "install-brew"

def get_os_family():

    d = Distribution(None)
    d.populate()
    return d.facts["os_family"]

def get_default_pkg_mgr():

    return DEFAULT_PKG_MGRS.get(get_os_family(), False)

class Install(AbstractTask):

    def get_config_schema(self):

        s = Schema({
            Required(PACKAGES_KEY): list,
            PKG_MGR_KEY: Any(*SUPPORTED_PKG_MGRS),
            PKGS_KEY: dict,
            INSTALL_IGNORE_KEY: list
        }, extra=ALLOW_EXTRA)

        return s


    def process_leaf(self, leaf, supported_runners=[FRECKLES_DEFAULT_RUNNER], debug=False):

        config = leaf[FRECK_VARS_KEY]
        freck_meta = leaf[FRECK_META_KEY]

        ignore_list = config.get(INSTALL_IGNORE_KEY, [])
        # check whether there are non-dotfile apps to isntall

        apps = create_apps_dict(config[PACKAGES_KEY], default_details=config)

        package_mgrs = Set()

        configs = []

        for app, details in apps.iteritems():
            if app in ignore_list:
                continue

            meta = copy.deepcopy(leaf[FRECK_META_KEY])

            if PKG_MGR_KEY not in details.keys():
                meta[PKG_MGR_KEY] = get_default_pkg_mgr()
                if not meta.get(PKG_MGR_KEY, False):
                    raise FrecklesConfigError("Can't find default package manager for: {}".format(get_os_family()))

            else:
                meta[PKG_MGR_KEY] = details[PKG_MGR_KEY]

            sudo = get_pkg_mgr_sudo(meta[PKG_MGR_KEY])
            meta[FRECK_SUDO_KEY] = sudo

            package_mgrs.add(meta[PKG_MGR_KEY])

            # check if 'pkgs' key is a dict, if not, use its value and put it into the 'default' key

            # check if pkgs key exists
            pkgs = details.get(PKGS_KEY, False)
            if not pkgs:
                if "packages" in details.keys():
                    pkgs = {"default": details["packages"]}
                else:
                    pkgs = {"default": [app]}
            if not isinstance(pkgs, dict):

                if isinstance(pkgs, basestring):
                    temp = pkgs
                    pkgs = {}
                    pkgs["default"] = [temp]
                elif isinstance(pkgs, list):
                    temp = pkgs
                    pkgs = {}
                    pkgs["default"] = temp

            # TODO: sanity check of config
            if meta[PKG_MGR_KEY] in pkgs.keys():
                packages = pkgs[PKG_MGR_KEY]
            else:
                packages = pkgs["default"]

            if isinstance(packages, basestring):
                packages = [packages]

            meta[TASK_NAME_KEY] = meta[PKG_MGR_KEY]
            meta[FRECK_DESC_KEY] = "{} -> install".format(meta[PKG_MGR_KEY])

            for p in packages:
                meta_copy = copy.deepcopy(meta)
                meta_copy[FRECK_ITEM_NAME_KEY] = p
                meta_copy[FRECK_VARS_KEY] = {"name": p, "state": "present"}
                configs.append(meta_copy)


        # if config.get(ENSURE_PACKAGE_MANAGER_KEY, ENSURE_PACKAGE_MANAGER_DEFAULT):
        #     for pkg_mgr in package_mgrs:
        #         extra_configs = create_pkg_mgr_install_config(pkg_mgr)
        #         if ADD_PKG_MGR_PATH_KEY in config.keys():
        #             add_path = config[ADD_PKG_MGR_PATH_KEY]
        #         else:
        #             add_path = ADD_PKG_MGR_PATH_DEFAULT_WHEN_AUTO_INSTALL_PKG_MGR
        #         for c in extra_configs:
        #             c[ADD_PKG_MGR_PATH_KEY] = add_path

        #         configs.extend(extra_configs)

        # if config.get(UPDATE_PACKAGE_CACHE_KEY, UPDATE_PACKAGE_CACHE_DEFAULT):
        #     extra_configs = update_package_cache(package_mgrs)
        #     configs.extend(extra_configs)

        # if config.get(UPGRADE_PACKAGES_KEY, UPGRADE_PACKAGES_DEFAULT):
        #     extra_configs = upgrade_packages(package_mgrs)
        #     configs.extend(extra_configs)

        return (FRECKLES_ANSIBLE_RUNNER,  configs)

    # def create_run_items(self, freck_meta, config):

    #     if PKG_MGR_KEY in config.keys() and config[PKG_MGR_KEY] == 'git':
    #         # this is needed, otherwise ansible tries to use the udpate method of a dict and fails
    #         for pkg_mgr in ['default', 'git']:
    #             for item in config[PKGS_KEY].get('default', []):
    #                 if isinstance(item, dict):
    #                     if not "update" in config.keys():
    #                         item["git_update"] = GIT_CONFIG_UPDATE_DEFAULT
    #                     else:
    #                         item["git_update"] = config["update"]

    #     return [config]


    def get_task_config(self, freck_meta, config):

        task_name = config[PKG_MGR_KEY]
        become = get_pkg_mgr_sudo(task_name)
        item_name = config["name"]

        template_keys = ["name", "state"]

        if "state" not in config.keys():
            config["state"] = "present"

        add_roles = { FRECKLES_DEFAULT_INSTALL_ROLE_NAME: FRECKLES_DEFAULT_INSTALL_ROLE_URL }
        return {
            TASK_MODULE_NAME_KEY: task_name,
            TASK_ITEM_NAME_KEY: item_name,
            TASK_DESC_KEY: "{} -> install".format(task_name),
            TASK_TEMPLATE_KEYS: template_keys,
            TASK_BECOME_KEY: become,
            TASK_ADDITIONAL_ROLES_KEY: add_roles,
            FRECK_VARS_KEY: config
        }

    # def handle_task_output(self, task, output_details):

    #     state = FRECKLES_STATE_SKIPPED
    #     changed = False
    #     failed = False
    #     stderr = []

    #     if task.get(ACTION_KEY) != "install":
    #         result = super(Install, self).handle_task_output(task, output_details)
    #         return result

    #     for details in output_details:

    #         if details[FRECKLES_STATE_KEY] == FRECKLES_STATE_SKIPPED:
    #             continue
    #         elif details[FRECKLES_STATE_KEY] == FRECKLES_STATE_FAILED:
    #             state = FRECKLES_STATE_FAILED
    #             if details["result"].get("msg", False):
    #                 stderr.append(details["result"]["msg"])
    #             for r in  details["result"].get("results", []):
    #                 if r.get("msg", False):
    #                     stderr.append(r["msg"])

    #         else:
    #         # this is the one we are interested in, there should only be one, right?
    #             temp_changed = details["result"][FRECKLES_CHANGED_KEY]
    #             if temp_changed:
    #                 pkg_mgr = details["action"]
    #                 state = "ok (using '{}')".format(pkg_mgr)
    #                 changed = True
    #             else:
    #                 state = "already present"

    #             break

    #     return {FRECKLES_STATE_KEY: state, FRECKLES_CHANGED_KEY: changed, FRECKLES_STDERR_KEY: stderr}

    def default_freck_config(self):
        return {
            # PACKAGE_STATE_KEY: DEFAULT_PACKAGE_STATE,
            # FRECK_SUDO_KEY: DEFAULT_PACKAGE_SUDO,
            # ACTION_KEY: "install",
            # FRECK_RUNNER_KEY: FRECKLES_ANSIBLE_RUNNER,
            # FRECK_META_ROLES_KEY: { FRECKLES_DEFAULT_INSTALL_ROLE_NAME: FRECKLES_DEFAULT_INSTALL_ROLE_URL },
            # FRECK_META_ROLE_KEY: FRECKLES_DEFAULT_INSTALL_ROLE_NAME
        }


class Update(AbstractTask):

    def pre_process_config(self, freck_meta, config):

        result = []
        if "pkg_mgrs" not in config.keys():
            pkg_mgr = "default"
            if "pkg_mgr" in config.keys():
                pkg_mgr = config["pkg_mgr"]
            pkg_mgrs = [pkg_mgr]
        else:
            pkg_mgrs = config["pkg_mgrs"]


        for pkg_mgr in pkg_mgrs:
            details = {}
            # TAG: local-only
            if pkg_mgr == "default":
                temp = get_default_pkg_mgr()
            else:
                temp = pkg_mgr

            if not PKG_MGRS_COMMANDS[temp]["update"]:
                continue

            details[PKG_MGR_KEY] = temp

            result.append(details)

        return result

    def get_task_config(self, freck_meta, config):

        pkg_mgr = config["pkg_mgr"]
        vars = PKG_MGRS_COMMANDS[pkg_mgr]["update"]
        become = get_pkg_mgr_sudo(pkg_mgr)
        return {
            TASK_MODULE_NAME_KEY: pkg_mgr,
            TASK_ITEM_NAME_KEY: "{} package cache".format(pkg_mgr),
            TASK_DESC_KEY: "update",
            FRECK_VARS_KEY: vars,
            TASK_BECOME_KEY: become
        }


    def default_freck_config(self):
        return {}


class InstallNix(Role):

    def get_role(self):
        return "install_pkg_mgrs"

    def get_additional_vars(self):
        return {"pkg_mgr": "nix"}

    def get_item_name(self):
        return "nix"

    def get_desc(self):
        return "install pkg-manager"

    def get_additional_roles(self):
        return {"install_pkg_mgrs": "frkl:ansible-install-pkg-mgrs"}

class InstallConda(Role):

    def get_role(self):
        return "install_pkg_mgrs"

    def get_additional_vars(self):
        return {"pkg_mgr": "conda"}

    def get_additional_roles(self):
        return {"install_pkg_mgrs": "frkl:ansible-install-pkg-mgrs"}

    def get_item_name(self):
        return "conda"

    def get_desc(self):
        return "install pkg-manager"

class InstallPkgMgrs(Freck):

    def get_config_schema(self):
        return False

    def create_run_items(self, freck_name, freck_type, freck_desc, config):

        while True:
            try:
                config.get(PKG_MGRS_KEY, []).remove("default")
            except ValueError:
                break

        result = []
        for pkg_mgr in config.get(PKG_MGRS_KEY, []):
            new_configs = create_pkg_mgr_install_config(pkg_mgr)
            for c in new_configs:
                dict_merge(c, config)
                result.append(c)

        return result

    def default_freck_config(self):

        return {}

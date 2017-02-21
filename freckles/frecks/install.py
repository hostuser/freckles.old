# -*- coding: utf-8 -*-
import copy
import logging
import sys

from freckles import Freck
from freckles.constants import *
from freckles.exceptions import FrecklesConfigError
from freckles.runners.ansible_runner import (FRECK_ANSIBLE_ROLE_KEY,
                                             FRECK_ANSIBLE_ROLES_KEY)
from freckles.utils import (create_apps_dict, create_dotfiles_dict, dict_merge,
                            get_pkg_mgr_from_marker_file,
                            get_pkg_mgr_from_path, get_pkg_mgr_sudo,
                            parse_dotfiles_item)
from sets import Set
from voluptuous import ALLOW_EXTRA, Any, Required, Schema

log = logging.getLogger("freckles")

SUPPORTED_PKG_MGRS = ["deb", "rpm", "nix", "no_install", "conda", "default"]
INSTALL_IGNORE_KEY = "no_install"
ACTION_KEY = "install_action"
PKGS_KEY = "pkgs"   # this is the key that is used in the role

USE_DOTFILES_KEY = "use_dotfiles"
USE_DOTFILES_DEFAULT = True
USE_PACKAGES_KEY = "use_packages_var"
USE_PACKAGES_DEFAULT = True

ENSURE_PACKAGE_MANAGER_KEY = "ensure_pkg_manager"
ENSURE_PACKAGE_MANAGER_DEFAULT = False

UPDATE_PACKAGE_CACHE_KEY = "update_cache"
UPDATE_PACKAGE_CACHE_DEFAULT = True
UPGRADE_PACKAGES_KEY = "upgrade_packages"
UPGRADE_PACKAGES_DEFAULT = False

PRIORITY_SOURCE_KEY = "priority_source"
PRIORITY_SOURCE_DEFAULT = PACKAGES_KEY

FRECKLES_DEFAULT_INSTALL_ROLE_NAME = "install-pkg"
FRECKLES_DEFAULT_INSTALL_ROLE_URL = "frkl:ansible-install-pkgs"

FRECKLES_DEFAULT_INSTALL_PKG_MGRS_ROLE_NAME = "install-pkg-mgrs"
FRECKLES_DEFAULT_INSTALL_PKG_MGRS_ROLE_URL = "frkl:ansible-install-pkg-mgrs"

UPDATE_DEFAULT_CONFIG = {
    INT_FRECK_PRIORITY_KEY: 100,
    FRECK_SUDO_KEY: DEFAULT_PACKAGE_SUDO,
    ACTION_KEY: "update_cache",
    FRECK_RUNNER_KEY: FRECKLES_ANSIBLE_RUNNER,
    FRECK_ANSIBLE_ROLES_KEY: { FRECKLES_DEFAULT_INSTALL_ROLE_NAME: FRECKLES_DEFAULT_INSTALL_ROLE_URL },
    FRECK_ANSIBLE_ROLE_KEY: FRECKLES_DEFAULT_INSTALL_ROLE_NAME
}

UPGRADE_DEFAULT_CONFIG = {
    INT_FRECK_PRIORITY_KEY: 200,
    FRECK_SUDO_KEY: DEFAULT_PACKAGE_SUDO,
    ACTION_KEY: "upgrade",
    FRECK_RUNNER_KEY: FRECKLES_ANSIBLE_RUNNER,
    FRECK_ANSIBLE_ROLES_KEY: { FRECKLES_DEFAULT_INSTALL_ROLE_NAME: FRECKLES_DEFAULT_INSTALL_ROLE_URL },
    FRECK_ANSIBLE_ROLE_KEY: FRECKLES_DEFAULT_INSTALL_ROLE_NAME
}

INSTALL_PKG_MANAGERS_DEFAULT_CONFIG = {
    INT_FRECK_PRIORITY_KEY: 10,
    FRECK_SUDO_KEY: False,
    FRECK_RUNNER_KEY: FRECKLES_ANSIBLE_RUNNER,
    FRECK_ANSIBLE_ROLES_KEY: {
        FRECKLES_DEFAULT_INSTALL_PKG_MGRS_ROLE_NAME: FRECKLES_DEFAULT_INSTALL_PKG_MGRS_ROLE_URL},
    FRECK_ANSIBLE_ROLE_KEY: FRECKLES_DEFAULT_INSTALL_PKG_MGRS_ROLE_NAME
}

INSTALL_MAC_BREW_DEFAULT_CONFIG = {
    INT_FRECK_PRIORITY_KEY: 10,
    FRECK_SUDO_KEY: True,
    FRECK_RUNNER_KEY: FRECKLES_ANSIBLE_RUNNER,
    FRECK_ANSIBLE_ROLES_KEY: {
        FRECKLES_DEFAULT_INSTALL_PKG_MGRS_ROLE_NAME: "https://github.com/geerlingguy/ansible-role-homebrew.git",
        "elliotweiser.osx-command-line-tools": "https://github.com/elliotweiser/ansible-osx-command-line-tools.git"
    },
    FRECK_ANSIBLE_ROLE_KEY: FRECKLES_DEFAULT_INSTALL_PKG_MGRS_ROLE_NAME
}

def create_pkg_mgr_install_config(pkg_mgr):

    if pkg_mgr == DEFAULT_PACKAGE_MANAGER_STRING or pkg_mgr == INSTALL_IGNORE_KEY:
        return []

    if pkg_mgr == "brew":
        config = copy.deepcopy(INSTALL_MAC_BREW_DEFAULT_CONFIG)
    else:
        config = copy.deepcopy(INSTALL_PKG_MANAGERS_DEFAULT_CONFIG)

    config[PKG_MGRS_KEY] = pkg_mgr

    # TAG: local-only
    if "nix" == pkg_mgr:
        if not os.path.isdir("/nix") or not os.access('/nix', os.W_OK):
            config[FRECK_SUDO_KEY] = True

    config[INT_FRECK_ITEM_NAME_KEY] = "{}".format(pkg_mgr)
    config[INT_FRECK_DESC_KEY] = "install package manager"
    return [config]

def update_package_cache(pkg_mgrs):

    pkg_mgrs = copy.deepcopy(pkg_mgrs)
    try:
        pkg_mgrs.remove(INSTALL_IGNORE_KEY)
    except:
        pass

    result = []
    for pkg_mgr in pkg_mgrs:
        details = copy.deepcopy(UPDATE_DEFAULT_CONFIG)
        if pkg_mgr != "default":
            details[PKG_MGR_KEY] = pkg_mgr

        details[INT_FRECK_ITEM_NAME_KEY] = "{} package cache".format(pkg_mgr)
        details[INT_FRECK_DESC_KEY] = "update"
        result.append(details)

    return result

def upgrade_packages(pkg_mgrs):

    pkg_mgrs = copy.deepcopy(pkg_mgrs)
    try:
        pkg_mgrs.remove(INSTALL_IGNORE_KEY)
    except:
        pass

    result = []
    for pkg_mgr in pkg_mgrs:
        details = copy.deepcopy(UPGRADE_DEFAULT_CONFIG)
        details[PKG_MGR_KEY] = pkg_mgr

        details[INT_FRECK_ITEM_NAME_KEY] = "{} packages".format(pkg_mgr)
        details[INT_FRECK_DESC_KEY] = "upgrade"
        result.append(details)

    return result

class Install(Freck):

    def get_config_schema(self):

        s = Schema({
            PACKAGES_KEY: list,
            DOTFILES_KEY: list,
            PKG_MGR_KEY: Any(*SUPPORTED_PKG_MGRS),
            PKGS_KEY: dict
        }, extra=ALLOW_EXTRA)

        return s

    def pre_process_config(self, config):

        ignore_list = config.get(INSTALL_IGNORE_KEY, [])
        # check whether there are non-dotfile apps to isntall
        apps = {}
        if config.get(USE_DOTFILES_KEY, USE_DOTFILES_DEFAULT) and config.get(DOTFILES_KEY, False):
            dotfiles = parse_dotfiles_item(config[DOTFILES_KEY])
            apps_dotfiles = create_dotfiles_dict(dotfiles, default_details=config)
            for app, details in apps_dotfiles.iteritems():
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
        else:
            apps_dotfiles = {}

        if config.get(USE_PACKAGES_KEY, USE_PACKAGES_DEFAULT) and config.get(PACKAGES_KEY, False):
            apps_packages = create_apps_dict(config[PACKAGES_KEY], default_details=config)
        else:
            apps_packages = {}


        priority_source = config.get(PRIORITY_SOURCE_KEY, PRIORITY_SOURCE_DEFAULT)
        if priority_source != PACKAGES_KEY and priority_source != DOTFILES_KEY:
            raise FrecklesConfigError("priority source key needs to either be '{}' or '{}', but is: {}".format(PACKAGES_KEY, DOTFILES_KEY, priority_source), PRIORITY_SOURCE_KEY, priority_source)

        if priority_source == PACKAGES_KEY:
            dict_merge(apps, apps_dotfiles)
            dict_merge(apps, apps_packages)
        else:
            dict_merge(apps, apps_packages)
            dict_merge(apps, apps_dotfiles)

        configs = []

        package_mgrs = Set()

        for app, details in apps.iteritems():
            if app in ignore_list:
                continue

            # check if pkgs key exists
            if not details.get(PKGS_KEY, False):
                details[PKGS_KEY] = {"default": [details[INT_FRECK_ITEM_NAME_KEY]]}

            if details.get(PKG_MGR_KEY, False):
                sudo = get_pkg_mgr_sudo(details[PKG_MGR_KEY])
                details[FRECK_SUDO_KEY] = sudo
            else:
                details[PKG_MGR_KEY] = DEFAULT_PACKAGE_MANAGER_STRING

            package_mgrs.add(details[PKG_MGR_KEY])

            # check if 'pkgs' key is a dict, if not, use its value and put it into the 'default' key
            if not type(details["pkgs"]) == dict:
                temp = details["pkgs"]
                details["pkgs"] = {}
                details["pkgs"]["default"] = temp

            # check if an 'default' pkgs key exists, if not, use the package name
            if not details.get("pkgs").get("default", False):
                details["pkgs"]["default"] = [details[INT_FRECK_ITEM_NAME_KEY]]

            details[INT_FRECK_DESC_KEY] = "install package"

            configs.append(details)

        if config.get(ENSURE_PACKAGE_MANAGER_KEY, ENSURE_PACKAGE_MANAGER_DEFAULT):
            for pkg_mgr in package_mgrs:
                extra_configs = create_pkg_mgr_install_config(package_mgrs)
                configs.extend(extra_configs)

        if config.get(UPDATE_PACKAGE_CACHE_KEY, UPDATE_PACKAGE_CACHE_DEFAULT):
            extra_configs = update_package_cache(package_mgrs)
            configs.extend(extra_configs)

        if config.get(UPGRADE_PACKAGES_KEY, UPGRADE_PACKAGES_DEFAULT):
            extra_configs = upgrade_packages(package_mgrs)
            configs.extend(extra_configs)

        return configs

    def create_run_items(self, freck_name, freck_type, freck_desc, config):

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
                    state = "ok (using '{}')".format(pkg_mgr)
                    changed = True
                else:
                    state = "already present"

                break

        return {FRECKLES_STATE_KEY: state, FRECKLES_CHANGED_KEY: changed, FRECKLES_STDERR_KEY: stderr}

    def default_freck_config(self):
        return {
            PACKAGE_STATE_KEY: DEFAULT_PACKAGE_STATE,
            FRECK_SUDO_KEY: DEFAULT_PACKAGE_SUDO,
            ACTION_KEY: "install",
            FRECK_RUNNER_KEY: FRECKLES_ANSIBLE_RUNNER,
            FRECK_ANSIBLE_ROLES_KEY: { FRECKLES_DEFAULT_INSTALL_ROLE_NAME: FRECKLES_DEFAULT_INSTALL_ROLE_URL },
            FRECK_ANSIBLE_ROLE_KEY: FRECKLES_DEFAULT_INSTALL_ROLE_NAME
        }


class Update(Freck):

    def pre_process_config(self, config):

        result = []
        for pkg_mgr in config.get("pkg_mgrs", ["default"]):
            details = copy.deepcopy(config)
            if pkg_mgr != "default":
                details[PKG_MGR_KEY] = pkg_mgr

            details[INT_FRECK_ITEM_NAME_KEY] = "update {} package cache".format(pkg_mgr)
            result.append(details)

        result = update_package_cache(config.get("pkg_mgrs", DEFAULT_PACKAGE_MANAGER_STRING))
        return result

    def create_run_items(self, freck_name, freck_type, freck_desc, config):

        config[INT_FRECK_DESC_KEY] = "update"
        return [config]

    def default_freck_config(self):
        return UPDATE_DEFAULT_CONFIG


class Upgrade(Freck):

    def pre_process_config(self, config):

        result = []
        for pkg_mgr in config.get("pkg_mgrs", ["default"]):
            details = copy.deepcopy(config)
            details[PKG_MGR_KEY] = pkg_mgr

            details[INT_FRECK_ITEM_NAME_KEY] = "upgrade {} packages".format(pkg_mgr)
            result.append(details)

        return result

    def create_run_items(self, freck_name, freck_type, freck_desc, config):

        config[INT_FRECK_DESC_KEY] = "upgrade"
        return [config]

    def default_freck_config(self):
        return UPGRADE_DEFAULT_CONFIG


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

        return INSTALL_PKG_MANAGERS_DEFAULT_CONFIG

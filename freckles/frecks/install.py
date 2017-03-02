# -*- coding: utf-8 -*-
import copy
import logging
import platform
import pprint
import sys

from ansible.module_utils.facts import Distribution
from checkout import GIT_VALID_KEYS
from freckles import Freck
from freckles.constants import *
from freckles.exceptions import FrecklesConfigError
from freckles.runners.ansible_runner import (FRECK_META_ROLE_DICT_KEY,
                                             FRECK_META_ROLE_KEY,
                                             FRECK_META_ROLES_KEY)
from freckles.utils import (create_apps_dict, create_dotfiles_dict, dict_merge,
                            get_pkg_mgr_from_marker_file,
                            get_pkg_mgr_from_path, get_pkg_mgr_sudo,
                            parse_dotfiles_item)
from role import AbstractRole, Role
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
    "no_install": {"update": False, "upgrade": False, "valid_install_keys": []},
    "apt": {"update": {"update_cache": True}, "upgrade": {"upgrade": "dist"}, "valid_install_keys": ["allow_unauthenticated", "autoremove", "cache_valid_time", "deb", "default_release", "dpkg_options", "force", "install_recommends", "only_upgrade", "purge", "state", "update_cache", "upgrade"]},
    "yum": {"update": False, "upgrade": {"name": "'*'", "state": "latest"}, "valid_install_keys": ["conf_file", "disable_gpg_check", "disablerepo", "enablerepo", "exclude", "insstallroot", "list", "skip_broken", "state", "update_cache", "validate_certs"]},
    "nix": {"update": {"update_cache": True}, "upgrade": {"upgrade": True}, "roles": {"install_nix_pkg": "frkl:ansible-nix-pkgs"}, "valid_install_keys": ["state"]},
    "conda": {"update": False, "upgrade": False, "roles": {"install_conda_pkgs": "frkl:ansible-conda-pkgs"}, "valid_install_keys": ["upgrade", "channels", "environment", "state"]},
    "brew": {"update": {"update_homebrew": True, "upgrade_homebrew": False}, "upgrade": {"upgrade_all": True, "update_homebrew": False, "valid_install_keys": ["install_options", "path", "state"]}},
    "git": {"update": False, "upgrade": False, "valid_install_keys": GIT_VALID_KEYS}
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
        package_mgrs = Set()

        if config.get(USE_DOTFILES_KEY, False) and config.get(DOTFILES_KEY, False):
            dotfiles = parse_dotfiles_item(config[DOTFILES_KEY])
            apps_dotfiles = create_dotfiles_dict(dotfiles, default_details=config)
            for app, details in apps_dotfiles.iteritems():
                if not details.get(PKG_MGR_KEY, False):
                    dotfiles_dir = details.get(DOTFILES_DIR_KEY, False)
                    if dotfiles_dir:
                        # if the folder contains a file called .nix.frkl or .no_install.frkl or .conda.frkl than that can determine the pkg mgr too, and it'd override the path

                        pkg_mgr = get_pkg_mgr_from_marker_file(dotfiles_dir)
                        if pkg_mgr:
                            details[PKG_MGR_KEY] = pkg_mgr
        else:
            apps_dotfiles = {}


        apps_packages = create_apps_dict(config.get(PACKAGES_KEY, {}), default_details=config)

        priority_source = config.get(PRIORITY_SOURCE_KEY, PRIORITY_SOURCE_DEFAULT)
        if priority_source != PACKAGES_KEY and priority_source != DOTFILES_KEY:
            raise FrecklesConfigError("priority source key needs to either be '{}' or '{}', but is: {}".format(PACKAGES_KEY, DOTFILES_KEY, priority_source), PRIORITY_SOURCE_KEY, priority_source)

        apps = {}
        if priority_source == PACKAGES_KEY:
            dict_merge(apps, apps_dotfiles)
            dict_merge(apps, apps_packages)
        else:
            dict_merge(apps, apps_packages)
            dict_merge(apps, apps_dotfiles)

        configs = []

        for app, details in apps.iteritems():

            if app in ignore_list:
                continue

            meta = {}

            if PKG_MGR_KEY not in details.keys() or details[PKG_MGR_KEY] == 'default':
                meta[PKG_MGR_KEY] = get_default_pkg_mgr()
                if not meta.get(PKG_MGR_KEY, False):
                    raise FrecklesConfigError("Can't find default package manager for: {}".format(get_os_family()))
            else:
                meta[PKG_MGR_KEY] = details[PKG_MGR_KEY]

            if meta[PKG_MGR_KEY] == "no_install":
                continue

            sudo = get_pkg_mgr_sudo(meta[PKG_MGR_KEY])
            meta[FRECK_SUDO_KEY] = sudo
            meta[TASK_NAME_KEY] = meta[PKG_MGR_KEY]
            meta[FRECK_DESC_KEY] = "{} -> install".format(meta[PKG_MGR_KEY])

            package_mgrs.add(meta[PKG_MGR_KEY])

            # check if 'pkgs' key is a dict, if not, use its value and put it into the 'default' key
            if meta[PKG_MGR_KEY] == 'git':
                pkgs = details.get(PKGS_KEY, False)
                if not pkgs:
                    raise FrecklesConfigError("No packages specified for git install: {}".format(details), PKGS_KEY, details)

                for pkg in pkgs:
                    if not isinstance(pkg, dict):
                        raise FrecklesConfigError("For installing packages via git, you need to provide a dict as value.", PKGS_KEY, pkg)

                    dest = pkg.get('dest', False)
                    if not dest:
                        raise FrecklesConfigError("For installing packages via git, you need to provide a 'dest' key: '{}'".format(pkg), "dest", pkg)
                    repo = pkg.get('repo', False)
                    if not repo:
                        raise FrecklesConfigError("For installing packages via git, you need to provide a 'repo' key: '{}'".format(pkg), "repo", pkg)

                    meta_copy = copy.deepcopy(meta)
                    meta_copy[FRECK_VARS_KEY] = {'repo': repo, 'dest': dest}
                    meta_copy[FRECK_ITEM_NAME_KEY] = repo
                    for key in details.keys():
                        if key in PKG_MGRS_COMMANDS[meta[PKG_MGR_KEY]].get("valid_install_keys", []):
                            meta_copy[FRECK_VARS_KEY][key] = details[key]
                    configs.append(meta_copy)
            else:
                # check if pkgs key exists
                pkgs = details.get(PKGS_KEY, False)
                if not pkgs:
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

                if "roles" in PKG_MGRS_COMMANDS[meta[PKG_MGR_KEY]].keys():
                    meta[FRECK_META_ROLES_KEY] = PKG_MGRS_COMMANDS[meta[PKG_MGR_KEY]]["roles"]

                for p in packages:
                    meta_copy = copy.deepcopy(meta)
                    meta_copy[FRECK_ITEM_NAME_KEY] = p
                    meta_copy[FRECK_VARS_KEY] = {"name": p}
                    for key in details.keys():
                        if key in PKG_MGRS_COMMANDS[meta[PKG_MGR_KEY]].get("valid_install_keys", []):
                            meta_copy[FRECK_VARS_KEY][key] = details[key]
                    configs.append(meta_copy)


        if config.get(ENSURE_PACKAGE_MANAGER_KEY, ENSURE_PACKAGE_MANAGER_DEFAULT):
            for pkg_mgr in package_mgrs:
                if pkg_mgr == "conda":
                    extra_config = InstallConda.get_install_conda_meta()
                elif pkg_mgr == "nix":
                    extra_config = InstallNix.get_install_nix_meta()
                else:
                    #TODO: brew
                    continue
                if config.get("add_path", False):
                    extra_config.setdefault(FRECK_VARS_KEY, {})["add_path"] = True

                # pprint.pprint(extra_config)
                extra_config[FRECK_PRIORITY_KEY] = 10
                configs.append(extra_config)

        if config.get(UPDATE_PACKAGE_CACHE_KEY, UPDATE_PACKAGE_CACHE_DEFAULT):
            for pkg_mgr in package_mgrs:
                if PKG_MGRS_COMMANDS.get(pkg_mgr).get("update", False):
                    extra_config = Update.create_update_meta(pkg_mgr)
                    extra_config[FRECK_PRIORITY_KEY] = 100
                    configs.append(extra_config)

        if config.get(UPGRADE_PACKAGES_KEY, UPGRADE_PACKAGES_DEFAULT):
            if PKG_MGRS_COMMANDS.get(pkg_mgr).get("upgrade", False):
                extra_config = Upgrade.create_upgrade_meta(pkg_mgr)
                extra_config[FRECK_PRIORITY_KEY] = 500
                configs.append(extra_config)

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


class Update(AbstractTask):

    UNIQUE_TASK_ID_PREFIX = "UPDATE_PKGS"

    @staticmethod
    def create_update_meta(pkg_mgr):

        new_meta = {}
        new_meta[TASK_NAME_KEY] = pkg_mgr
        update = PKG_MGRS_COMMANDS[pkg_mgr]["update"]
        if update:
            new_meta[FRECK_VARS_KEY] = update
        else:
            new_meta[FRECK_VARS_KEY] = {}
        new_meta[FRECK_DESC_KEY] = "update"
        new_meta[FRECK_SUDO_KEY] = get_pkg_mgr_sudo(pkg_mgr)
        new_meta[FRECK_ITEM_NAME_KEY] = "{} package cache".format(pkg_mgr)
        new_meta[UNIQUE_TASK_ID_KEY] = "{}_{}".format(Update.UNIQUE_TASK_ID_PREFIX, pkg_mgr)
        return new_meta

    def process_leaf(self, leaf, supported_runners=[FRECKLES_DEFAULT_RUNNER], debug=False):

        config = leaf.get(FRECK_VARS_KEY, {})
        meta = leaf[FRECK_META_KEY]

        result = []
        if PKG_MGRS_KEY not in config.keys():
            pkg_mgr = "default"
            if PKG_MGR_KEY in config.keys():
                pkg_mgr = config[PKG_MGR_KEY]
            pkg_mgrs = [pkg_mgr]
        else:
            pkg_mgrs = config["pkg_mgrs"]

        for pkg_mgr in pkg_mgrs:

            new_meta = {}
            # TAG: local-only
            if pkg_mgr == "default":
                temp = get_default_pkg_mgr()
            else:
                temp = pkg_mgr

            if not PKG_MGRS_COMMANDS[temp]["update"]:
                continue

            new_meta = Update.create_update_meta(temp)

            result.append(new_meta)

        return (FRECKLES_ANSIBLE_RUNNER, result)

class Upgrade(AbstractTask):

    UNIQUE_TASK_ID_PREFIX = "UPGRADE"

    @staticmethod
    def create_upgrade_meta(pkg_mgr):

        new_meta = {}
        new_meta[TASK_NAME_KEY] = pkg_mgr
        upgrade = PKG_MGRS_COMMANDS[pkg_mgr]["upgrade"]
        if upgrade:
            new_meta[FRECK_VARS_KEY] = upgrade
        else:
            new_meta[FRECK_VARS_KEY] = {}
        new_meta[FRECK_DESC_KEY] = "upgrade"
        new_meta[FRECK_SUDO_KEY] = get_pkg_mgr_sudo(pkg_mgr)
        new_meta[FRECK_ITEM_NAME_KEY] = "{} packages".format(pkg_mgr)

        new_meta[UNIQUE_TASK_ID_KEY] = "{}_{}".format(Upgrade.UNIQUE_TASK_ID_PREFIX, pkg_mgr)
        return new_meta

    def process_leaf(self, leaf, supported_runners=[FRECKLES_DEFAULT_RUNNER], debug=False):

        config = leaf.get(FRECK_VARS_KEY, {})
        meta = leaf[FRECK_META_KEY]

        result = []
        if PKG_MGRS_KEY not in config.keys():
            pkg_mgr = "default"
            if PKG_MGR_KEY in config.keys():
                pkg_mgr = config[PKG_MGR_KEY]
            pkg_mgrs = [pkg_mgr]
        else:
            pkg_mgrs = config["pkg_mgrs"]

        for pkg_mgr in pkg_mgrs:

            new_meta = {}
            # TAG: local-only
            if pkg_mgr == "default":
                temp = get_default_pkg_mgr()
            else:
                temp = pkg_mgr

            if not PKG_MGRS_COMMANDS[temp]["upgrade"]:
                continue

            # new_meta[PKG_MGR_KEY] = temp
            new_meta = Upgrade.create_upgrade_meta(temp)
            result.append(new_meta)

        return (FRECKLES_ANSIBLE_RUNNER, result)


class InstallNix(AbstractRole):

    UNIQUE_TASK_ID = "install_nix"

    @staticmethod
    def get_install_nix_meta():
        return AbstractRole.create_role_dict("install_nix", item_name="nix", desc="install package manager", sudo=True, additional_roles={"install_nix": "frkl:ansible-nix-pkg-mgr"}, unique_task_id=InstallNix.UNIQUE_TASK_ID)

    def get_unique_task_id(self, freck_meta):
        return InstallNix.UNIQUE_TASK_ID

    def get_role(self, freck_meta):
        return "install_nix"

    def get_desc(self, freck_meta):
        return "install package manager"

    def get_item_name(self, freck_meta):
        return "nix"

    def get_sudo(self, freck_meta):
        return True

    def get_additional_roles(self, freck_meta):

        return {"install_nix": "frkl:ansible-nix-pkg-mgr"}

class InstallConda(AbstractRole):

    UNIQUE_TASK_ID = "install_conda"

    @staticmethod
    def get_install_conda_meta():

        return AbstractRole.create_role_dict("install_conda", item_name="conda", desc="install package manager", sudo=False, additional_roles={"install_conda": "frkl:ansible-conda-pkg-mgr"}, additional_vars={"conda_rel_path": ".freckles/opt"}, unique_task_id=InstallConda.UNIQUE_TASK_ID)

    def get_unique_task_id(self, freck_meta):
        return InstallConda.UNIQUE_TASK_ID

    def get_role(self, freck_meta):
        return "install_conda"

    def get_additional_roles(self, freck_meta):
        return {"install_conda": "frkl:ansible-conda-pkg-mgr"}

    def get_item_name(self, freck_meta):
        return "conda"

    def get_desc(self, freck_meta):
        return "install package manager"

    def get_additional_vars(self, freck_meta):
        return {"conda_rel_path": ".freckles/opt"}

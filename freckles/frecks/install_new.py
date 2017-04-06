# -*- coding: utf-8 -*-
import copy
import json
import logging
import platform
import pprint
import sys

from ansible.module_utils import basic
from ansible.module_utils.facts import Distribution
from freckles import Freck
from freckles.constants import *
from freckles.exceptions import FrecklesConfigError
from freckles.frecks.checkout import GIT_VALID_KEYS
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

SUPPORTED_PKG_MGRS = ["apt", "yum", "deb", "nix", "pip", "git", "no_install", "conda", "homebrew", "default"]
DEFAULT_PKG_MGRS = {
    "Debian": "apt",
    "RedHat": "yum",
    "Darwin": "homebrew"
}

ENSURE_PACKAGE_MANAGER_KEY = "ensure_pkg_manager"

PKG_MGRS_COMMANDS = {
    "no_install": {"update": False, "upgrade": False, "valid_install_keys": [], "ansible_module": "no_install"},
    "deb": {"ansible_module": "apt", "update": False, "upgrade": False, "valid_install_keys": ["deb", "dpkg_options", "force", "install_recommends", "only_upgrade", "purge", "state", "update_cache"]},
    "apt": {"ansible_module": "apt", "update": {"update_cache": True}, "upgrade": {"upgrade": "dist"}, "valid_install_keys": ["allow_unauthenticated", "autoremove", "cache_valid_time", "default_release", "dpkg_options", "force", "install_recommends", "only_upgrade", "purge", "state", "update_cache", "upgrade"]},
    "yum": {"ansible_module": "yum", "update": False, "upgrade": {"name": "'*'", "state": "latest"}, "valid_install_keys": ["conf_file", "disable_gpg_check", "disablerepo", "enablerepo", "exclude", "insstallroot", "list", "skip_broken", "state", "update_cache", "validate_certs"]},
    "nix": {"ansible_module": "nix", "update": {"update_cache": True}, "upgrade": {"upgrade": True}, "roles": {"install_nix_pkg": "frkl:ansible-nix-pkgs"}, "valid_install_keys": ["state"]},
    "conda": {"ansible_module": "conda", "update": False, "upgrade": False, "roles": {"install_conda_pkgs": "frkl:ansible-conda-pkgs"}, "valid_install_keys": ["upgrade", "channels", "environment", "state"]},
    "homebrew": {"ansible_module": "homebrew", "update": {"update_homebrew": True, "upgrade_homebrew": False}, "upgrade": {"upgrade_all": True, "update_homebrew": False, "valid_install_keys": ["install_options", "path", "state"]}, ENSURE_PACKAGE_MANAGER_KEY: True},
    "git": {"update": False, "upgrade": False, "valid_install_keys": GIT_VALID_KEYS}
}

INSTALL_IGNORE_KEY = "no_install"
ACTION_KEY = "install_action"
PKGS_KEY = "pkgs"   # this is the key that is used in the role

USE_DOTFILES_KEY = "use_dotfiles"
USE_DOTFILES_DEFAULT = False
USE_PACKAGES_KEY = "use_packages_var"
USE_PACKAGES_DEFAULT = True

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

    # pf = basic.get_platform()
    # if pf == 'Darwin':
        # return pf
    # distribution = basic.get_distribution()
    # print(distribution)
    # osfamily = Distribution.OS_FAMILY.get(distribution)
    # print(osfamily)
    # return osfamily

    basic._ANSIBLE_ARGS = '{"ANSIBLE_MODULE_ARGS": {}}'
    module = basic.AnsibleModule({})
    d = Distribution(module)
    d.populate()
    os_family = d.facts["os_family"]
    return os_family


def get_default_pkg_mgr():

    return DEFAULT_PKG_MGRS.get(get_os_family(), False)


class Install(AbstractTask):

    def process_leaf(self, leaf, supported_runners=[FRECKLES_DEFAULT_RUNNER], debug=False):

        config = leaf[FRECK_VARS_KEY]
        freck_meta = leaf[FRECK_META_KEY]

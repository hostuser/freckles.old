# -*- coding: utf-8 -*-
from os import sep, path, listdir
from constants import FRECKLES_METADATA_FILENAME
from stevedore import extension
import sys
import yaml
import copy
from constants import *

import logging
log = logging.getLogger("freckles")

DEB_MATCH = "{}{}{}".format(sep, 'deb', sep)
RPM_MATCH = "{}{}{}".format(sep, 'rpm', sep)
NIX_MATCH = "{}{}{}".format(sep, 'nix', sep)
NO_INSTALL_MATCH = "{}{}{}".format(sep, "no_install", sep)

def parse_dotfiles_item(item):
    """Parses an item in a config file, and depending on its type returns a complete list of dicts."""

    if isinstance(item, basestring):
        dotfiles = [{DOTFILES_BASE_KEY: item, DOTFILES_PATHS_KEY: [], DOTFILES_REMOTE_KEY: ""}]
        return dotfiles
    elif isinstance(item, dict):
        paths = item.get(DOTFILES_PATHS_KEY, [])
        remote = item.get(DOTFILES_REMOTE_KEY, "")
        base = item.get(DOTFILES_BASE_KEY, False)
        if not base:
            log.error("Config item for plugin 'install' is dict, but no key {}.".format(DOTFILES_BASE_KEY))
            sys.exit(FRECKLES_CONFIG_ERROR_EXIT_CODE)

        dotfiles = [{DOTFILES_BASE_KEY: base, DOTFILES_PATHS_KEY: paths, DOTFILES_REMOTE_KEY: remote}]
        return dotfiles
    elif isinstance(item, (list, tuple)):
        dotfiles = []
        for sub_item in item:
            temp_dotfiles = parse_dotfiles_item(sub_item)
            dotfiles.extend(temp_dotfiles)
        return dotfiles

def get_pkg_mgr_from_path(path):

    if NIX_MATCH in path:
        return 'nix'
    elif DEB_MATCH in path:
        return 'deb'
    elif RPM_MATCH in path:
        return 'rpm'
    elif NO_INSTALL_MATCH in path:
        return 'no_install'
    else:
        return False

def load_extensions():

    log.debug("Loading extensions...")
    mgr = extension.ExtensionManager(
        namespace='freckles.frecks',
        invoke_on_load=True
    )
    log.debug("Registered plugins: {}".format(", ".join(ext.name for ext in mgr.extensions)))

    return {ext.name: ext.plugin() for ext in mgr.extensions}

def playbook_needs_sudo(playbook_items):
    """Checks whether a playbook needs to use 'become' or not."""

    return bool([x for x in playbook_items.values() if x.get(FRECK_SUDO_KEY, False)])


def create_playbook_dict(playbook_items, host_group=FRECKLES_DEFAULT_GROUP_NAME):

    temp_root = {}
    temp_root["hosts"] = host_group
    temp_root["gather_facts"] = True

    temp_root["roles"] = playbook_items.values()

    return temp_root

def extract_roles(playbook_items):

    roles = {}
    for item in playbook_items.values():
        name = item.get(ANSIBLE_ROLE_NAME_KEY, False)
        url = item.get(ANSIBLE_ROLE_URL_KEY, False)

        if name and url:
            roles[name] = url

    return roles


def create_dotfiles_dict(base_dirs, default_details):

    apps = {}

    for dir in base_dirs:
        base = dir.get(DOTFILES_BASE_KEY, False)
        if not base:
            log.error("No {} key for dotfile entry found, can't continue.".format(DOTFILES_BASE_KEY))
            sys.exit(2)

        remote = dir.get(DOTFILES_REMOTE_KEY, "")
        paths = dir.get(DOTFILES_PATHS_KEY, [])

        if not paths:
            paths = [""]

        for dotfile_path in paths:

            temp_full_path = path.join(base, dotfile_path)

            for item in listdir(temp_full_path):
                if not item.startswith(".") and path.isdir(path.join(temp_full_path, item)):
                    # defaults
                    dotfile_dir = path.join(temp_full_path, item)
                    apps[item] = copy.deepcopy(default_details)
                    apps[item][ITEM_NAME_KEY] = item
                    apps[item][DOTFILES_DIR_KEY] = dotfile_dir
                    apps[item][DOTFILES_BASE_DIR_KEY] = temp_full_path
                    apps[item][DOTFILES_BASE_KEY] = base
                    if remote:
                        apps[item][DOTFILES_REMOTE_KEY] = remote
                    if dotfile_path:
                        apps[item][DOTFILES_PATH_KEY] = dotfile_path

                    freckles_metadata_file = path.join(dotfile_dir, FRECKLES_METADATA_FILENAME)
                    if path.exists(freckles_metadata_file):
                        stream = open(freckles_metadata_file, 'r')
                        temp = yaml.load(stream)
                        apps[item].update(temp)


    return apps

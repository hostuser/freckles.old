# -*- coding: utf-8 -*-
from os import sep, path, listdir
from constants import FRECKLES_METADATA_FILENAME
from stevedore import extension
import sys
import yaml
import copy
import subprocess
from constants import *

import logging
log = logging.getLogger("freckles")

DEB_MARKER_FILE = ".{}{}".format('deb', FRECKLES_METADATA_FILENAME)
RPM_MARKER_FILE = ".{}{}".format('rpm', FRECKLES_METADATA_FILENAME)
NIX_MARKER_FILE = ".{}{}".format('nix', FRECKLES_METADATA_FILENAME)
CONDA_MARKER_FILE = ".{}{}".format('conda', FRECKLES_METADATA_FILENAME)
NO_INSTALL_MARKER_FILE = ".{}{}".format('no_install', FRECKLES_METADATA_FILENAME)

DEB_MATCH = "{}{}{}".format(sep, 'deb', sep)
RPM_MATCH = "{}{}{}".format(sep, 'rpm', sep)
NIX_MATCH = "{}{}{}".format(sep, 'nix', sep)
CONDA_MATCH = "{}{}{}".format(sep, 'conda', sep)
NO_INSTALL_MATCH = "{}{}{}".format(sep, "no_install", sep)

def parse_dotfiles_item(item):
    """Parses an item in a config file, and depending on its type returns a complete list of dicts."""

    if isinstance(item, basestring):
        dotfiles = [{DOTFILES_BASE_KEY: os.path.expanduser(item), DOTFILES_PATHS_KEY: [], DOTFILES_REMOTE_KEY: ""}]
        return dotfiles
    elif isinstance(item, dict):
        paths = item.get(DOTFILES_PATHS_KEY, [])
        remote = item.get(DOTFILES_REMOTE_KEY, "")
        base = os.path.expanduser(item.get(DOTFILES_BASE_KEY, False))
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

def expand_repo_url(repo_url):

    if repo_url.startswith("gh:"):
        return "github"
    elif repo_url.startswith("bb:"):
        return "bitbucket"
    else:
        return repo_url

def can_passwordless_sudo():

    p = subprocess.Popen('sudo -n ls', shell=True)
    r = p.wait()
    return r == 0

def expand_bootstrap_config_url(config_url):

    return expand_config_url(config_url, default_repo=FRECKLES_DEFAULT_DOTFILE_REPO_NAME, default_path=FRECKLES_DEFAULT_FRECKLES_BOOTSTRAP_CONFIG_PATH)

def expand_config_url(config_url, default_repo=FRECKLES_DEFAULT_DOTFILE_REPO_NAME, default_path=FRECKLES_DEFAULT_FRECKLES_CONFIG_PATH):

    if config_url.startswith("gh:"):
        tokens = config_url.split(":")
        if len(tokens) == 1 or len(tokens) > 4:
            log.error("Can't parse github config url '{}'. Exiting...")
            sys.exit(FRECKLES_CONFIG_ERROR_EXIT_CODE)
        if len(tokens) >= 2:
            host = "https://raw.githubusercontent.com"
            username = tokens[1]
            repo = default_repo
            path = default_path
        if len(tokens) >= 3:
            repo = tokens[2]
        if len(tokens) == 4:
            path = tokens[3]

        return "{}/{}/{}/master/{}".format(host, username, repo, path)

    elif config_url.startswith("bb:"):
        return "bitbucket"
    else:
        return config_url

def check_dotfile_items(dotfiles):

    result = []
    for d in dotfiles:
        paths = d[DOTFILES_PATHS_KEY]
        if not paths:
            paths = [""]
        base = d[DOTFILES_BASE_KEY]
        remote = d[DOTFILES_REMOTE_KEY]

        for p in paths:
            full_path = os.path.join(base, p)
            if os.path.isdir(full_path):
                result.append(full_path)

    return result

def get_pkg_mgr_sudo(mgr):
    if mgr == 'no_install':
        return False
    elif mgr == 'nix':
        return False
    elif mgr == 'conda':
        return False
    else:
        return True

def get_pkg_mgr_from_marker_file(p):

    if path.exists(path.join(p, NO_INSTALL_MARKER_FILE)):
        return 'no_install'
    if path.exists(path.join(p, NIX_MARKER_FILE)):
        return 'nix'
    elif path.exists(path.join(p, CONDA_MARKER_FILE)):
        return 'conda'
    elif path.exists(path.join(p, DEB_MARKER_FILE)):
        return 'deb'
    elif path.exists(path.join(p, RPM_MARKER_FILE)):
        return 'rpm'
    else:
        return False

def get_pkg_mgr_from_path(p):

    if NIX_MATCH in p:
        return 'nix'
    elif CONDA_MATCH in p:
        return 'conda'
    elif DEB_MATCH in p:
        return 'deb'
    elif RPM_MATCH in p:
        return 'rpm'
    elif NO_INSTALL_MATCH in p:
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
        item_roles = item.get(ANSIBLE_ROLES_KEY, {})
        roles.update(item_roles)

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
                    apps[item][DOTFILES_BASE_KEY] = temp_full_path
                    if remote:
                        apps[item][DOTFILES_REMOTE_KEY] = remote
                    if dotfile_path:
                        apps[item][DOTFILES_PATHS_KEY] = dotfile_path

                    freckles_metadata_file = path.join(dotfile_dir, FRECKLES_METADATA_FILENAME)
                    if path.exists(freckles_metadata_file):
                        stream = open(freckles_metadata_file, 'r')
                        temp = yaml.load(stream)
                        apps[item].update(temp)


    return apps

# -*- coding: utf-8 -*-
from os import sep, path, listdir
from constants import FRECKLES_METADATA_FILENAME
from stevedore import extension
import sys
import pprint
import yaml
import json
import copy
import subprocess
from constants import *
import collections
import os
import urllib2
from exceptions import FrecklesConfigError

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


def dict_merge(dct, merge_dct):
    """ Recursive dict merge. Inspired by :meth:``dict.update()``, instead of
    updating only top-level keys, dict_merge recurses down into dicts nested
    to an arbitrary depth, updating keys. The ``merge_dct`` is merged into
    ``dct``.

    Copied from: https://gist.github.com/angstwad/bf22d1822c38a92ec0a9

    :param dct: dict onto which the merge is executed
    :param merge_dct: dct merged into dct
    :return: None
    """
    for k, v in merge_dct.iteritems():
        if (k in dct and isinstance(dct[k], dict)
                and isinstance(merge_dct[k], collections.Mapping)):
            dict_merge(dct[k], merge_dct[k])
        else:
            dct[k] = merge_dct[k]



def expand_config_url(url):

    if not url.startswith("gh:") and not url.startswith("bb:"):
        return url

    if  url.startswith("gh:"):
        tokens = url.split(":")
        if len(tokens) == 1 or len(tokens) > 4:
            raise FrecklesConfigError("Can't parse github config url '{}'. Exiting...", 'config', url)
        if len(tokens) >= 2:
            host = "https://raw.githubusercontent.com"
            username = tokens[1]
            repo = DEFAULT_DOTFILE_REPO_NAME
            path = FRECKLES_DEFAULT_FRECKLES_CONFIG_PATH
        if len(tokens) >= 3:
            repo = tokens[2]
        if len(tokens) == 4:
            path = tokens[3]
        url = "{}/{}/{}/master/{}".format(host, username, repo, path)
        log.debug("Expanding '{}' as url: {}".format(url, url))
        return url
    elif url.startswith("bb:"):
        # TODO bitbucket
        raise Exception("Not implemented")


def get_config(config_file_url):
    """Retrieves the config (if necessary), and converts it to a dict.

    Config can be either a path to a local yaml file, an url to a remote yaml file, or a json string.

    For the case that a url is provided, there are a few abbreviations available:

    TODO
    """

    config_file_url = expand_config_url(config_file_url)

    # check if file first
    if os.path.exists(config_file_url):
        log.debug("Opening as file: {}".format(config_file_url))
        with open(config_file_url) as f:
            config_yaml = yaml.load(f)
        return config_yaml
    # check if url
    elif config_file_url.startswith("http"):
        # TODO: exception handling
        log.debug("Opening as url: {}".format(config_file_url))
        response = urllib2.urlopen(config_file_url)
        content = response.read()
        return yaml.load(content)
    else:
        # try to convert a json string
        try:
            config = json.loads(config_file_url)
            return config
        except:
            raise FrecklesConfigError("Can't parse config, doesn't seem to be a file nor a json string: {}".format(config_file_url), 'config', config_file_url)


def create_runs(configs):
    """Creates all runs using the list of provided configs.

    Configs will be overlayed (as described in XXX).

    Args:
        configs (list): a list of configs (paths, urls, etc.)
    """

    result_runs = []

    current_default_vars = {}  # copy.deepcopy(seed_vars)

    for config in configs:

        config_dict = get_config(config)

        runs = config_dict.get("runs", {})
        vars = config_dict.get("vars", {})

        # first we merge the 'file-global' vars
        dict_merge(current_default_vars, vars)

        # now we create a set of vars for each freck in each run
        i = 1
        for run_item in runs:

            name = run_item.get("name", False)
            number = i
            if not name:
                name = "run_{}".format(i)

            i = i+1

            vars = run_item.get("vars", {})
            frecks = run_item.get("frecks", [])
            run_vars = copy.deepcopy(current_default_vars)
            dict_merge(run_vars, vars)
            run_frecks = []
            j = 1
            for freck in frecks:
                 if isinstance(freck, dict):
                    if len(freck) != 1:
                        raise FrecklesConfigError("Can't read freck configuration in run {}, not exactly one key in dict.".fromat(name), "config", freck)
                    freck_type = freck.keys()[0]
                    freck_metadata = freck[freck_type]
                    if not isinstance(freck_metadata, dict):
                        raise FrecklesConfigError("Freck configuration for type {} in run {} not a dict, don't know what to do with that...".format(freck_type, name), "config", freck_metadata)

                    freck_name = freck_metadata.get("name", "freck_{}_{}".format(j, freck_type))
                    freck_inner_vars = freck_metadata.get("vars", {})
                 elif not isinstance(freck, basestring):
                     raise FrecklesConfigError("Can't parse config in run {}".format(name), "config", freck)
                 else:
                     freck_type = freck
                     freck_inner_vars = {}
                     freck_name = "freck_{}_{}".format(j, freck_type)

                 freck_vars = copy.deepcopy(run_vars)
                 dict_merge(freck_vars, freck_inner_vars)
                 run_frecks.append({"name": freck_name, "vars": freck_vars, "type": freck_type})
                 j = j + 1
            run = {"name": name, "frecks": run_frecks, "nr": number}
            result_runs.append(run)

    return result_runs


# def guess_local_default_config(base_dir=None, paths=None, remote=None):

#     result = {}
#     result["default_vars"] = {}
#     result["default_vars"][DOTFILES_KEY] = {}

#     if not base_dir:
#         if os.path.isdir(DEFAULT_DOTFILE_DIR):
#             result["default_vars"][DOTFILES_KEY][DOTFILES_BASE_KEY] = DEFAULT_DOTFILE_DIR
#     else:
#         if os.path.isdir(base_dir):
#             result["default_vars"][DOTFILES_KEY][DOTFILES_BASE_KEY] = base_dir
#         else:
#             log.error("Directory '{}' does not exist. Exiting...".format(base_dir))
#             sys.exit(FRECKLES_CONFIG_ERROR_EXIT_CODE)

#     if not result["default_vars"][DOTFILES_KEY].get(DOTFILES_BASE_KEY, False):
#         return False

#     if paths:
#         if not result["default_vars"][DOTFILES_KEY].get(DEFAULT_DOTFILE_DIR, False):
#             log.error("Paths specified, but not base dir. Can't continue, exiting...")
#             sys.exit(FRECKLES_CONFIG_ERROR_EXIT_CODE)
#         for p in paths:
#             path = os.path.join(result["default_vars"][DOTFILES_KEY][DEFAULT_DOTFILE_DIR], p)
#             if not os.path.isdir(path):
#                 log.error("Combined dotfile path '{} does not exist, exiting...".format(path))
#                 sys.exit(FRECKLES_CONFIG_ERROR_EXIT_CODE)


#     # check if base_dir is git repo
#     remotes = []
#     if result["default_vars"][DOTFILES_KEY].get(DOTFILES_BASE_KEY, False):
#         git_config_file = os.path.join(result["default_vars"][DOTFILES_KEY][DOTFILES_BASE_KEY], ".git", "config")
#         if os.path.isfile(git_config_file):
#             with open(git_config_file) as f:
#                 content = f.readlines()
#             in_remote = False
#             for line in content:
#                 if not in_remote:
#                     if "[remote " in line:
#                         in_remote = True
#                     continue
#                 else:
#                     if "url = " in line:
#                         remote = line.strip().split()[-1]
#                         remotes.append(remote)
#                         in_remote = False
#                         continue

#     # TODO: this all is a bit crude, should just use git exe to figure out remotes
#     if not remote:
#         if len(remotes) == 1:
#             result["default_vars"][DOTFILES_KEY][DOTFILES_REMOTE_KEY] = remotes[0]
#         elif len(remotes) > 1:
#             log.error("Can't guess git remote, more than one configured. Exiting...")
#             sys.exit(FRECKLES_CONFIG_ERROR_EXIT_CODE)
#     else:
#         if len(remotes) == 1:
#             if remotes[0] == remote:
#                 result["default_vars"][DOTFILES_KEY][DOTFILES_REMOTE_KEY] = remote
#             else:
#                 log.error("Provided git remote '{}' differs from local one '{}'. Exiting...".format(remote, remotes[0]))
#                 sys.exit(FRECKLES_CONFIG_ERROR_EXIT_CODE)
#         elif len(remotes) == 0:
#             log.error("git remote provided, but local repo is not configured to use it. Exiting...")
#             sys.exit(FRECKLES_CONFIG_ERROR_EXIT_CODE)
#         else:
#             if remote in remotes:
#                 result["default_vars"][DOTFILES_KEY][DOTFILES_REMOTE_KEY] = remote
#             else:
#                 log.error("Provided remote repo url does not match with locally available ones. Exiting...")
#                 sys.exit(FRECKLES_CONFIG_ERROR_EXIT_CODE)

#     if result["default_vars"][DOTFILES_KEY].get(DOTFILES_REMOTE_KEY, False):
#         result["runs"] = [
#             {"frecks": {"checkout": {}}},
#             {"frecks": {"install": {}, "stow": {}}}
#         ]
#     else:
#         result["runs"] = [
#             {"frecks": {"install": {}, "stow": {}}}
#         ]

#     return result

def parse_dotfiles_item(item):
    """Parses an item in a config file, and depending on its type returns a complete list of dicts.

    More details about dotfiles and the format they can be specified can be found here: XXX

    This method is mostly for convenience, as it allows users to provide either a string, in which case it is assumed it's a local or remote path/url (and, depending on that, either the base_dir or remote value), a fully descriptive dict, or a list of strings and/or dicts.
    """

    if isinstance(item, basestring):

        # lets see if it is a local, existing path
        try:
            temp_path = os.path.expanduser(item)
            if os.path.exists(temp_path):
                dotfiles = [{DOTFILES_BASE_KEY: os.path.expanduser(item), DOTFILES_PATHS_KEY: DEFAULT_DOTFILE_PATHS, DOTFILES_REMOTE_KEY: DEFAULT_DOTFILE_REMOTE}]
                return dotfiles
        except:
            pass

        # or maybe its a remote url
        temp_url = expand_config_url(item)
        if temp_url.startswith("http"):
            dotfiles = [{DOTFILES_BASE_KEY: DEFAULT_DOTFILE_DIR, DOTFILES_PATHS_KEY: DEFAULT_DOTFILE_PATHS, DOTFILES_REMOTE_KEY: temp_url}]
            return dotfiles
        else:
            raise FrecklesConfigError("Can't parse dotfiles item: {}".format(item), "dotfiles", item)
    elif isinstance(item, dict):
        paths = item.get(DOTFILES_PATHS_KEY, DEFAULT_DOTFILE_PATHS)
        remote = item.get(DOTFILES_REMOTE_KEY, DEFAULT_DOTFILE_REMOTE)
        base = os.path.expanduser(item.get(DOTFILES_BASE_KEY, False))
        if not base:
            raise FrecklesConfigError("Config item for plugin 'install' is dict, but no key {}.".format(DOTFILES_BASE_KEY), "config", item)

        dotfiles = [{DOTFILES_BASE_KEY: base, DOTFILES_PATHS_KEY: paths, DOTFILES_REMOTE_KEY: remote}]
        return dotfiles
    elif isinstance(item, (list, tuple)):
        dotfiles = []
        for sub_item in item:
            temp_dotfiles = parse_dotfiles_item(sub_item)
            dotfiles.extend(temp_dotfiles)
        return dotfiles

def can_passwordless_sudo():
    """Checks if the user can use passwordless sudo on this host."""

    p = subprocess.Popen('sudo -n ls', shell=True)
    r = p.wait()
    return r == 0


# def check_dotfile_items(dotfiles):
#
#     result = []
#     for d in dotfiles:
#         paths = d[DOTFILES_PATHS_KEY]
#         if not paths:
#             paths = [""]
#         base = d[DOTFILES_BASE_KEY]
#         remote = d[DOTFILES_REMOTE_KEY]
#
#         for p in paths:
#             full_path = os.path.join(base, p)
#             if os.path.isdir(full_path):
#                 result.append(full_path)
#
#     return result

def get_pkg_mgr_sudo(mgr):
    """Simple function to determine whether a given package manager needs sudo rights or not.
    """
    if mgr == 'no_install':
        return False
    elif mgr == 'nix':
        return False
    elif mgr == 'conda':
        return False
    else:
        return True

def get_pkg_mgr_from_marker_file(p):
    """Checks whether there exists a package manager marker file in a dotfile directory, if it does, the name of the package manager is returned."""

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
    """Checks whether the dotfiles directories' path has a 'marker'-component to it. If it does, the package manager to use is returned."""

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
    """Loads all the extensions that can be found."""

    log2 = logging.getLogger("stevedore")
    out_hdlr = logging.StreamHandler(sys.stdout)
    out_hdlr.setFormatter(logging.Formatter('PLUGIN ERROR -> %(message)s'))
    out_hdlr.setLevel(logging.DEBUG)
    log2.addHandler(out_hdlr)
    log2.setLevel(logging.INFO)

    log.debug("Loading extensions...")
    mgr = extension.ExtensionManager(
        namespace='freckles.frecks',
        invoke_on_load=True,
        propagate_map_exceptions=True
    )
    log.debug("Registered plugins: {}".format(", ".join(ext.name for ext in mgr.extensions)))

    return {ext.name: ext.plugin() for ext in mgr.extensions}

def playbook_needs_sudo(playbook_items):
    """Checks whether a playbook needs to use 'become' or not."""

    return bool([x for x in playbook_items.values() if x.get(FRECK_SUDO_KEY, False)])

def create_playbook_dict(playbook_items, host_group=FRECKLES_DEFAULT_GROUP_NAME):
    """Assembles the dictionary to create the playbook from."""
    temp_root = {}
    temp_root["hosts"] = host_group
    temp_root["gather_facts"] = True

    temp_root["roles"] = playbook_items.values()

    return temp_root

def extract_ansible_roles(playbook_items):
    """Extracts all ansible roles that will be used in a run.

    The result is used to download the roles automatically before the run starts.
    """

    roles = {}
    for item in playbook_items.values():
        item_roles = item.get(FRECK_RUNNER_KEY, {}).get(FRECK_ANSIBLE_RUNNER, {}).get(FRECK_ANSIBLE_ROLES_KEY, {})
        roles.update(item_roles)

    return roles


def create_apps_dict(apps, default_details):
    """Creates a dictionary that can be used by the install/stow Frecks, and potentially others.

    This doesn't really do much, it just checks whether the provided list element is a string or dict. If it's a string, it will use that as the item name, otherwise it expects a dict with one element with the app name as key, and the config vars as value.

    Args:
        apps (list): a list of strings or dicts or both
        default_details (dict): the details to seed each app item with

    Results:
        dict: a dict with the app names as keys, and the app details as values
    """

    result = {}
    for app in apps:
        details = copy.deepcopy(default_details)
        if isinstance(app, dict):
            if len(app) != 1:
                raise FrecklesConfigError("More than one key provided in app configuration, needs to be either dict of lengths one, or string: {}".format(app), "apps", app)
            app_name = app.keys()[0]
            app_details = app.values()[0]
            if not app_details:
                app_details = {}
            dict_merge(details, app_details)
            details[FRECK_ITEM_NAME_KEY] = app_name

        elif isinstance(app, str):
            details[FRECK_ITEM_NAME_KEY] = app

        else:
            raise FrecklesConfigError("Can't parse apps configuration: {}".format(app), "apps", app)

        result[details[FRECK_ITEM_NAME_KEY]] = details

    return result


def create_dotfiles_dict(base_dirs, default_details):
    """Walks through all the provided dotfiles, and creates a dictionary with values according to what it finds, per folder.

    Args:
       base_dirs (list): a list of dotfile dictionaries (see: XXX)
       default_details (list): details to use for each entry as default (which can be overwritten), this would differ for every Freck that calls this method
    """

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

            if not os.path.isdir(temp_full_path):
                log.debug("Not a directory, ignoring: {}".format(temp_full_path))
                continue

            for item in listdir(temp_full_path):
                if not item.startswith(".") and path.isdir(path.join(temp_full_path, item)):
                    # defaults
                    dotfile_dir = path.join(temp_full_path, item)
                    apps[item] = copy.deepcopy(default_details)
                    apps[item][FRECK_ITEM_NAME_KEY] = item
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

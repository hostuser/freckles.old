# -*- coding: utf-8 -*-
import abc
import copy
import json
import logging
import os
import pprint
import sys
import urllib2
import uuid
from collections import OrderedDict
from exceptions import FrecklesConfigError, FrecklesRunError
from operator import itemgetter

import click
import six
import yaml

import sets
from constants import *
from freckles_runner import FrecklesRunner
from runners.ansible_runner import AnsibleRunner
from sets import Set
from utils import (check_schema, dict_merge, get_pkg_mgr_from_path,
                   load_extensions)
from voluptuous import ALLOW_EXTRA, Any, Schema

log = logging.getLogger("freckles")

FRKL_KEY_PREFIX = "_frkl"
FRKL_META_LEVEL_KEY = "{}_level".format(FRKL_KEY_PREFIX)
NO_STEM_INDICATOR = "-99999"
DEFAULT_LOAD_KEY = "load"

def get_config(config_file_url, repo, path):
    """Retrieves the config (if necessary), and converts it to a dict.

    Config can be either a path to a local yaml file, an url to a remote yaml file, or a json string.

    For the case that a url is provided, there are a few abbreviations available:

    TODO
    """

    if isinstance(config_file_url, dict):
        return config_file_url

    config_file_url = expand_config_url(config_file_url, repo, path)

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

def expand_config_url(url, default_repo, default_repo_path):

    if not url.startswith("gh:") and not url.startswith("bb:"):
        return url

    if  url.startswith("gh:"):
        tokens = url.split(":")
        if len(tokens) == 1 or len(tokens) > 4:
            raise FrecklesConfigError("Can't parse github config url '{}'. Exiting...", 'config', url)
        if len(tokens) >= 2:
            host = "https://raw.githubusercontent.com"
            username = tokens[1]
            repo = default_repo
            path = default_repo_path
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

def get_and_load_configs(config_url, default_repo, default_path, load_external=True, load_key=DEFAULT_LOAD_KEY):
    """ Retrieves and loads config from url, parses it and downloads 'load' configs if applicable.
    """

    log.debug("Loading config: {}".format(config_url))
    config_dict = get_config(config_url, default_repo, default_path)
    result = [config_dict]

    load = config_dict.get(load_key, [])
    if load and load_external:
        if isinstance(load, basestring):
            new_configs = get_and_load_configs(load, default_repo, default_path)
            result.extend(new_configs)
        elif isinstance(load, (tuple, list)):
            for config in load:
                new_configs = get_and_load_configs(config, default_repo, default_path)
                result.extend(new_configs)
        else:
            raise FrecklesConfigError("Can't load external config, type not recognized: {}".format(load), GLOBAL_LOAD_KEY, load)

    return result

def flatten_root(root):

    result = []
    for item in root:

        result_dict = {}
        for var, value_dicts in item.iteritems():
            result_dict[var] = {}
            for value_dict in value_dicts:
                dict_merge(result_dict[var], value_dict)

        result.append(result_dict)

    return result

class Frkl(object):

    def __init__(self, configs, stem_key, other_valid_keys, default_leaf_key, default_leaf_default_key, default_leaf_default_value_key, default_repo, default_repo_path):

        self.stem_key = stem_key
        self.other_keys = other_valid_keys

        self.default_repo = default_repo
        self.default_path = default_repo_path

        #TODO: check default_leaf key in all_keys
        self.default_leaf_key = default_leaf_key
        self.default_leaf_default_key = default_leaf_default_key
        #TODO: check default_value_dict in all_keys
        self.default_leaf_value_dict_key = default_leaf_default_value_key

        self.all_keys = Set([self.default_leaf_key, self.default_leaf_value_dict_key, self.stem_key])
        self.all_keys.update(self.other_keys)

        self.configs = []
        for c in configs:
            self.configs.append(get_config(c, self.default_repo, self.default_path))
        self.root = []
        self.meta_dict = {}

        self.frklize_config(self.root, self.configs, self.meta_dict, 0)

        # pprint.pprint(self.root)
        self.leafs = flatten_root(self.root)


    def frklize_config(self, root, configs, meta_dict_parent, level, add_level=False):

        for c in configs:

            meta_dict = copy.deepcopy(meta_dict_parent)

            # if none of the known keys are used in the config,
            # we assume it's a 'default_key'-dict
            base_dict = c

            if isinstance(base_dict, basestring):
                base_dict = {self.default_leaf_key: {self.default_leaf_default_key: base_dict}}

            if not any(x in base_dict.keys() for x in self.all_keys):
                if len(base_dict.keys()) != 1:
                    raise Exception("If not using the full config format, leaf nodes are only allowed to have one key: {}".format(base_dict))

                key = base_dict.keys()[0]
                if any(x in base_dict[key].keys() for x in self.all_keys):
                    temp_base_dict = base_dict[key]
                    dict_merge(temp_base_dict, {self.default_leaf_key: {self.default_leaf_default_key: key}})
                    base_dict = temp_base_dict
                else:
                    temp_base_dict = {self.default_leaf_key: {self.default_leaf_default_key: key}}
                    dict_merge(temp_base_dict, {self.default_leaf_value_dict_key: base_dict[key]})
                    base_dict = temp_base_dict

            stem = base_dict.pop(self.stem_key, NO_STEM_INDICATOR)

            for key in base_dict.keys():
                if key not in self.all_keys:
                    raise Exception("Key '{}' not allowed (in {})".format(key, base_dict))

                if add_level:
                    base_dict[key][FRKL_META_LEVEL_KEY] = level

                meta_dict.setdefault(key, []).append(base_dict[key])

            if not stem:
                continue
            elif stem == NO_STEM_INDICATOR:
                root.append(copy.deepcopy(meta_dict))
            elif isinstance(stem, (list, tuple)) and not isinstance(stem, basestring):
                self.frklize_config(root, stem, meta_dict, level+1)
            else:
                raise Exception("Value of {} must be list (is: '{}')".format(self.stem_key, type(stem)))
# -*- coding: utf-8 -*-

import os
import yaml
import pprint
import json
from freckles_runner import FrecklesRunner
from utils import get_pkg_mgr_from_path, load_extensions
import six
import abc
from constants import *
import sys
import copy
import pprint
import logging
log = logging.getLogger(__name__)
from operator import itemgetter


FRECK_DEFAULT_CONFIG = {
    FRECK_PRIORITY_KEY: FRECK_DEFAULT_PRIORITY
}

@six.add_metaclass(abc.ABCMeta)
class Freck(object):

    def __init__(self):
        pass

    def default_freck_config(self):
        """Returns the default config, can be overwritten by the user config."""
        return {}

    def calculate_freck_config(self, user_default_config, user_freck_config):

        freck_config = copy.deepcopy(FRECK_DEFAULT_CONFIG)
        freck_config.update(copy.deepcopy(self.default_freck_config()))
        freck_config.update(user_default_config)
        freck_config.update(user_freck_config)

        return freck_config


    @abc.abstractmethod
    def create_playbook_items(self):
        """List of items to be included in the playbook."""
        pass

class Freckles(object):

    def __init__(self, config):

        self.frecks = load_extensions()
        self.hosts = {}
        if not config.get("hosts", False):
            config["hosts"] = ["localhost"]

        for host in config["hosts"]:
            if host == "localhost" or host == "127.0.0.1":
                self.hosts[host] = {"ansible_connection": "local"}
            else:
                self.hosts[host] = {}

        if not config.get("frecks", False):
            log.info("No frecks configured, doing nothing.")
            sys.exit(0)

        self.config = config


    def list_all(self):
        pprint.pprint(self.apps)

    def list(self, package_managers="apt", tags=None):
        print yaml.dump(self.apps, default_flow_style=False)

    # def create_inventory_yml(self):

        # groups = {self.group_name: {"vars": {"freckles": self.apps}, "hosts": [host for host in self.hosts.keys()]}}
        # hosts = self.hosts

        # inv = Inventory({"groups": groups, "hosts": hosts})
        # return inv.list()

    def create_playbook_items(self):
        """Create a list of sorted playbook items that can be included in a playbook section"""

        default_user_config = self.config["frecks"].get("default", {})

        playbook_items = []

        for freck_type, freck_config_item in self.config["frecks"].iteritems():

            if freck_type == "default":
                continue

            freck = self.frecks.get(freck_type, False)
            if not freck:
                log.error("Can't find freckles plugin: {}".format(freck_type))

            freck_config = freck.calculate_freck_config(default_user_config, freck_config_item)

            playbook_items.extend(freck.create_playbook_items(freck_config))

        sorted_playbook_items = sorted(playbook_items, key=itemgetter(FRECK_PRIORITY_KEY, ANSIBLE_ROLE_NAME_KEY))

        return sorted_playbook_items

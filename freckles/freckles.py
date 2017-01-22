# -*- coding: utf-8 -*-

import os
from collections import OrderedDict
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
log = logging.getLogger("freckles")
from operator import itemgetter
import uuid

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

    def handle_task_output(self, task, output_details):

        skipped = True
        changed = False
        failed = False
        stderr = []
        stdout = []

        result = {}

        for details in output_details:
            if details[FRECKLES_STATE_KEY] != FRECKLES_STATE_SKIPPED:
                skipped = False

                if details[FRECKLES_STATE_KEY] == FRECKLES_STATE_FAILED:
                    failed = True
                if details["result"][FRECKLES_CHANGED_KEY]:
                    changed = True
                if details["result"].get("stderr", False):
                    stderr.append(details["result"]["stderr"])


        if skipped:
            result[FRECKLES_STATE_KEY] = FRECKLES_STATE_SKIPPED
        else:
            if failed:
                result[FRECKLES_STATE_KEY] = FRECKLES_STATE_FAILED
            elif changed:
                result[FRECKLES_STATE_KEY] = FRECKLES_STATE_CHANGED
            else:
                result[FRECKLES_STATE_KEY] = FRECKLES_STATE_NO_CHANGE

        result[FRECKLES_CHANGED_KEY] = changed
        result[FRECKLES_STDERR_KEY] = stderr
        result[FRECKLES_STDOUT_KEY] = stdout
        return result




class Freckles(object):

    def __init__(self, config):

        self.frecks = load_extensions()
        self.hosts = {}
        if not config.get("hosts", False):
            log.debug("Defaulting to 'localhost' for hosts value.")
            config["hosts"] = ["localhost"]

        for host in config["hosts"]:
            if host == "localhost" or host == "127.0.0.1":
                self.hosts[host] = {"ansible_connection": "local"}
            else:
                self.hosts[host] = {}

        if not config.get("frecks", False):
            logging.info("No frecks configured, doing nothing.")
            sys.exit(0)

        self.config = config

    # def list_all(self):
        # pprint.pprint(self.apps)

    # def list(self, package_managers="apt", tags=None):
        # print yaml.dump(self.apps, default_flow_style=False)

    # def create_inventory_yml(self):

        # groups = {self.group_name: {"vars": {"freckles": self.apps}, "hosts": [host for host in self.hosts.keys()]}}
        # hosts = self.hosts

        # inv = Inventory({"groups": groups, "hosts": hosts})
        # return inv.list()

    def handle_task_output(self, task_item, output_details):

        freck_type = task_item[FRECK_TYPE_KEY]
        freck = self.frecks.get(freck_type)

        result = freck.handle_task_output(task_item, output_details)

        return result

    def create_playbook_items(self):
        """Create a list of sorted playbook items that can be included in a playbook section"""

        log.info("Parsing configuration...")

        default_user_config = self.config["frecks"].get("default", {})

        playbook_items = []

        for freck_type, freck_config_item in self.config["frecks"].iteritems():

            if freck_type == "default":
                continue

            freck = self.frecks.get(freck_type, False)
            if not freck:
                logging.error("Can't find freckles plugin: {}".format(freck_type))
                sys.exit(2)

            log.info("\tAdding: {}".format(freck_type))
            freck_config = freck.calculate_freck_config(default_user_config, freck_config_item)

            freck_config_items = freck.create_playbook_items(freck_config)
            for item in freck_config_items:
                item[FRECK_TYPE_KEY] = freck_type

            playbook_items.extend(freck_config_items)

        sorted_playbook_items = sorted(playbook_items, key=itemgetter(FRECK_PRIORITY_KEY, ANSIBLE_ROLE_NAME_KEY))

        result = OrderedDict()
        # add uuids to every item
        id = 1

        for item in sorted_playbook_items:
            item_id = id
            item['freckles_id'] = str(item_id)
            result[id] = item
            id = id+1

        return result

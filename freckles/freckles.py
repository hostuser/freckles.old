# -*- coding: utf-8 -*-

import os
from collections import OrderedDict
import yaml
import pprint
import json
from freckles_runner import FrecklesRunner
from utils import get_pkg_mgr_from_path, load_extensions, dict_merge
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

    def calculate_freck_config(self, freck_vars):

        freck_config = copy.deepcopy(FRECK_DEFAULT_CONFIG)
        dict_merge(freck_config, copy.deepcopy(self.default_freck_config()))
        dict_merge(freck_config, copy.deepcopy(freck_vars))

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
        msg = []

        result = {}

        for details in output_details:
            if details[FRECKLES_STATE_KEY] != FRECKLES_STATE_SKIPPED:
                skipped = False

                if details[FRECKLES_STATE_KEY] == FRECKLES_STATE_FAILED:
                    failed = True
                if details["result"].get(FRECKLES_CHANGED_KEY, False):
                    changed = True
                if details["result"].get("stderr", False):
                    stderr.append(details["result"]["stderr"])
                if details["result"].get("msg", False):
                    msg.append(details["result"]["msg"])


        if skipped:
            result[FRECKLES_STATE_KEY] = FRECKLES_STATE_SKIPPED
        else:
            if failed:
                result[FRECKLES_STATE_KEY] = FRECKLES_STATE_FAILED
                stderr.extend(msg)
            elif changed:
                result[FRECKLES_STATE_KEY] = FRECKLES_STATE_CHANGED
                stdout.extend(msg)
            else:
                result[FRECKLES_STATE_KEY] = FRECKLES_STATE_NO_CHANGE
                stdout.extend(msg)

        result[FRECKLES_CHANGED_KEY] = changed
        result[FRECKLES_STDERR_KEY] = stderr
        result[FRECKLES_STDOUT_KEY] = stdout
        return result




class Freckles(object):

    def __init__(self):

        self.frecks = load_extensions()


    def handle_task_output(self, task_item, output_details):

        freck_type = task_item[FRECK_TYPE_KEY]
        freck = self.frecks.get(freck_type)

        result = freck.handle_task_output(task_item, output_details)

        return result

    def create_playbook_items(self, run):
        """Create a list of sorted playbook items that can be included in a playbook section"""

        log.debug("Parsing configuration...")

        playbook_items = []

        run_name = run["name"]
        frecks = run["frecks"]

        for freck in frecks:

            freck_type = freck["type"]
            freck_name = freck["name"]
            freck_vars = freck["vars"]

            freck = self.frecks.get(freck_type, False)
            if not freck:
                logging.error("Can't find freckles plugin: {}".format(freck_type))
                sys.exit(2)

            log.debug("\tAdding: {}".format(freck_type))
            freck_config = freck.calculate_freck_config(freck_vars)

            freck_config_items = freck.create_playbook_items(freck_config)
            i = 1
            # add item_name, if not provided by freck
            for item in freck_config_items:
                item[FRECK_TYPE_KEY] = freck_type
                if not item.get(ITEM_NAME_KEY, False):
                    item[ITEM_NAME_KEY] = "{}_{}".format(freck_type, i)
                i = i+1

            playbook_items.extend(freck_config_items)

        if not playbook_items:
            return []

        sorted_playbook_items = sorted(playbook_items, key=itemgetter(FRECK_PRIORITY_KEY))

        # add ids to every item, and ansible role
        id = 1
        result_items = OrderedDict()
        for item in sorted_playbook_items:
            if not item.get(ANSIBLE_ROLE_KEY, False):
                roles = item.get(ANSIBLE_ROLES_KEY, {})
                if len(roles) != 1:
                    log.error("Item '{}' does not have a role associated with it, and more than one role in freck config. This is probably a bug, please report to the freck developer.".format(item[ITEM_NAME_KEY]))
                    sys.exit(FRECKLES_BUG_EXIT_CODE)
                item[ANSIBLE_ROLE_KEY] = roles.keys().next()
            item['freckles_id'] = str(id)
            result_items[id] = item
            id = id+1

        return result_items

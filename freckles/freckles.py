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


@six.add_metaclass(abc.ABCMeta)
class Freck(object):
    """Base class for freckles plugins ("Frecks"). Used to create playbook items and handle the output in order to display meaningful messages to the user.

    The only method that needs to be overwritten is the 'create_playbook_items' one. It is recommended to overwrite most of the others too.
    """

    def __init__(self):
        pass

    def default_freck_config(self):
        """Returns the default config, can be overwritten by the user config.

        This is used, among other things to specify default roles that are used in a Freck, and the urls to download them from. It is also recommended to specify Freck priorities in this (so that, for example, you make sure that the 'install' tasks are run before the 'stow' tasks -- not that that really matters in that instance, but you get the idea)

        Returns:
            dict: dictionary with default values for an execution of a Freck of this type
        """
        return {}


    def pre_process_config(self, config):
        """(Optionally) pre-process or augment the config that will be injected in the 'create_playbook_itmes' method.

        This is used mostly for Frecks that create multiple Freck runs out of a single configuration, as is the case with most Frecks that use a dotfiles directory. In that case, usually one playbook item is created out of every sub-folder of a dotfile directory (one run per application), and this method will return a list of configs that is calculated from the single input config.

        Args:
            config (dict): the base config for a Freck run

        Returns:
            list: a list of dicts describing the Freck runs to execute subsequently. If a single dict is returned, it'll be wrapped into a list down the line, so that's also possible.
        """

        return config

    def calculate_freck_config(self, freck_vars):
        """Merges the default vars from the 'default_freck_config' method with the (potentially overlayed) vars that come from the user config.

        User vars will have precedence over the default_vars. This method should not be overwritten by a Freck.

        Args:
            freck_vars (dict): the user-provided config vars


        Returns:
            dict: the merged config vars
        """

        freck_config = copy.deepcopy(FRECK_DEFAULT_CONFIG)
        dict_merge(freck_config, copy.deepcopy(self.default_freck_config()))
        dict_merge(freck_config, copy.deepcopy(freck_vars))

        return freck_config

    def get_config_schema(self):
        """The schema for the configuration of this nect.

        Returns a schema that describes the expected input config vars. Useful to make sure required values are specified.
        Uses `voluptous <https://github.com/alecthomas/voluptuous>`_ schemas.
        """
        return False

    @abc.abstractmethod
    def create_playbook_items(self, config):
        """List of items to be included in the playbook.

        This is the main method in every Freck. In some cases all the work is already done in the 'pre_process_config' method, but most of the time you'll want to create a list of dicts here which describe the items to be executed.

        Args:
            config (dict): the user-provided and pre-processsed configuration for this run of the Freck

        Returns:
            dict: the processed configuration for this run
        """
        pass

    def handle_task_output(self, task, output_details):
        """Method to convert the output of a Freck run to something freckles can display nicely.

        For examples on how to implement this method, check out the 'install' and 'stow' implementations.
        """

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
    """The central class in this project. This calculates the items to execute out of the default values and overlayed user provided configuration.

    TODO: more doc
    """

    def __init__(self):

        self.frecks = load_extensions()


    def handle_task_output(self, task_item, output_details):
        """Converts ansible output into something human-readable.

        Internally, this forwards the output to the Freck that created the playbook item.

        Args:
            task_item (dict): details about the task that was executed
            output_details (dict): output as created by ansible

        Returns:
            dict: sanitized dictionary that freckles know how to display
        """

        freck_type = task_item[FRECK_TYPE_KEY]
        freck = self.frecks.get(freck_type)

        result = freck.handle_task_output(task_item, output_details)

        return result

    def create_playbook_items(self, run):
        """Create a list of sorted playbook items that can be included in a playbook section.

        Args:
            run (dict): the description of the run and associated configs that is about to be executed.

        Returns
            list: a sorted list of all playbook items that were calculated out of the input configs
        """

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

            log.debug("Calculated config for '{}': {}".format(freck_name, freck_config))

            config_schema = freck.get_config_schema()
            if config_schema:
                log.debug("Checking schema for freck '{}'...".format(freck_name))
                config_schema(freck_config)
                log.debug("Schema ok")
            else:
                log.debug("Omitting schama check for freck '{}': no schema provided.". format(freck_name))

            if freck_config.get("freck_preprocess", True):
                freck_config = freck.pre_process_config(freck_config)

            # if preprocessing returns a list, we add all those seperately.
            if isinstance(freck_config, dict):
                freck_config["freck_preprocess"] = False
                freck_config_items = freck.create_playbook_items(freck_config)
                if isinstance(freck_config_items, dict):
                        freck_config_items = [freck_config_items]
            else:
                freck_config_items = []
                for item in freck_config:
                    item["freck_preprocess"] = False
                    temp = freck.create_playbook_items(item)
                    if isinstance(temp, dict):
                        temp = [temp]
                    freck_config_items.extend(temp)


            i = 1
            # add item_name, if not provided by freck
            for item in freck_config_items:
                item[FRECK_TYPE_KEY] = freck_type
                item[FRECK_NAME_KEY] = freck_name
                if not item.get(FRECK_ITEM_NAME_KEY, False):
                    item[FRECK_ITEM_NAME_KEY] = "{}_{}".format(freck_type, i)
                i = i+1

            playbook_items.extend(freck_config_items)

        if not playbook_items:
            return []

        sorted_playbook_items = sorted(playbook_items, key=itemgetter(FRECK_PRIORITY_KEY))

        # add ids to every item, and ansible role
        id = 1
        result_items = OrderedDict()
        for item in sorted_playbook_items:
            if not item.get(FRECK_ANSIBLE_ROLE_KEY, False):
                roles = item.get(FRECK_ANSIBLE_ROLES_KEY, {})
                if len(roles) != 1:
                    log.error("Item '{}' does not have a role associated with it, and more than one role in freck config. This is probably a bug, please report to the freck developer.".format(item[FRECK_ITEM_NAME_KEY]))
                    sys.exit(FRECKLES_BUG_EXIT_CODE)
                item[FRECK_ANSIBLE_ROLE_KEY] = roles.keys().next()
            item['freckles_id'] = str(id)
            result_items[id] = item
            id = id+1

        return result_items

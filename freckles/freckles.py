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

from constants import *
from freckles_runner import FrecklesRunner
from runners.ansible_runner import AnsibleRunner
from sets import Set
from utils import (check_schema, dict_merge, expand_config_url,
                   get_pkg_mgr_from_path, load_extensions)
from voluptuous import ALLOW_EXTRA, Any, Schema

log = logging.getLogger("freckles")


FRECKLES_RUNNERS = {
    FRECKLES_ANSIBLE_RUNNER: AnsibleRunner
}

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


def get_and_load_configs(config_url, load_external=True):
    """ Retrieves and loads config from url, parses it and downloads 'load' configs if applicable.
    """

    log.debug("Loading config: {}".format(config_url))
    config_dict = get_config(config_url)
    result = [config_dict]

    load = config_dict.get(GLOBAL_LOAD_KEY, [])
    if load and load_external:
        if isinstance(load, basestring):
            new_configs = get_and_load_configs(load)
            result.extend(new_configs)
        elif isinstance(load, (tuple, list)):
            for config in load:
                new_configs = get_and_load_configs(config)
                result.extend(new_configs)
        else:
            raise FrecklesConfigError("Can't load external config, type not recognized: {}".format(load), GLOBAL_LOAD_KEY, load)

    return result


def create_runs(orig_configs, available_frecks, load_external=True):
    """Creates all runs using the list of provided configs.

    Configs will be overlayed (as described in XXX).

    Args:
        configs (list): a list of configs (paths, urls, etc.)
    """

    configs = []

    # load external configs if applicable
    for config in orig_configs:

        config_dicts = get_and_load_configs(config, load_external)
        configs.extend(config_dicts)

    result_runs = OrderedDict()

    current_default_vars = {}  # copy.deepcopy(seed_vars)

    i = 1
    # overlay configs and create runs if one is encountered
    for config_dict in configs:

        if current_default_vars:
            config_list = [copy.deepcopy(current_default_vars)]
        else:
            config_list = []

        runs = config_dict.get(GLOBAL_RUNS_KEY, {})
        vars = config_dict.get(GLOBAL_VARS_KEY, {})

        if vars:
            config_list.append(copy.deepcopy(vars))

        for run_item in runs:

            run_schema = Schema({RUN_META_KEY: dict, RUN_DESC_KEY: str, RUN_FRECKS_KEY: list, RUN_VARS_KEY: dict, RUN_NAME_KEY: str})
            check_schema(run_item, run_schema)

            run_config_list = copy.deepcopy(config_list)
            run_name = run_item.get(RUN_NAME_KEY, "run_{}.format(i)")
            run_desc = run_item.get(RUN_DESC_KEY, False)
            run_meta = run_item.get(RUN_META_KEY, {})
            run_meta.setdefault(RUN_RUNNER_NAME_KEY, FRECKLES_DEFAULT_RUNNER)
            runner_name = run_meta[RUN_RUNNER_NAME_KEY]
            if not runner_name in FRECKLES_RUNNERS.keys():
                raise FrecklesConfigError("Runner '{}' not supported.".format(runner_name), RUN_RUNNER_NAME_KEY, runner_name)
            runner_class = FRECKLES_RUNNERS.get(runner_name, False)
            if not runner_class:
                raise FrecklesConfigError("Can't find runner with name: {}".format(runner_name))
            runner_obj = runner_class(available_frecks)
            run_meta[INT_RUN_RUNNER_KEY] = runner_obj

            run_meta[RUN_NAME_KEY] = run_name
            if run_desc:
                run_meta[RUN_DESC_KEY] = run_desc
            run_meta[RUN_NUMBER_KEY] = i

            vars = run_item.get(RUN_VARS_KEY, {})
            frecks = run_item.get(RUN_FRECKS_KEY, [])  # 'tasks' in config
            if vars:
                run_config_list.append(copy.deepcopy(vars))
            run_frecks = []
            j = 1

            for freck in frecks:

                freck_config_list = copy.deepcopy(run_config_list)
                # if we have a dictionary, we have extra configuration to overlay
                if isinstance(freck, dict):
                    if len(freck) != 1:
                        raise FrecklesConfigError("Can't read freck configuration in run {}, not exactly one key in dict.".fromat(name), "config", freck)
                    freck_name = freck.keys()[0]
                    freck_all_metadata = freck[freck_name]
                    if not isinstance(freck_all_metadata, dict):
                        raise FrecklesConfigError("Freck configuration for type {} in run {} not a dict, don't know what to do with that...".format(freck_name, name), "config", freck_metadata)

                    freck_all_metadata_schema = Schema({FRECK_META_KEY: dict, FRECK_VARS_KEY: dict, FRECK_DESC_KEY: str, FRECK_PRIORITY_KEY: int})

                    check_schema(freck_all_metadata, freck_all_metadata_schema)

                    freck_meta = freck_all_metadata.get(FRECK_META_KEY, {})
                    freck_inner_vars = freck_all_metadata.get(FRECK_VARS_KEY)

                elif not isinstance(freck, basestring):
                     raise FrecklesConfigError("Can't parse config in run {}".format(name), "config", freck)
                else:
                     freck_name = freck
                     freck_meta = {}
                     freck_inner_vars = {}


                freck_meta.setdefault(FRECK_DESC_KEY, "--config-item {}-- {}".format(j, freck_name))
                #freck_meta.setdefault(FRECK_VARS_KEY, {})
                freck_meta[FRECK_NAME_KEY] = freck_name

                if freck_inner_vars:
                    freck_config_list.append(freck_inner_vars)

                freck_meta[FRECK_CONFIGS_KEY] = freck_config_list
                run_frecks.append(freck_meta)

                j = j + 1

            run_meta[RUN_FRECKS_KEY] = run_frecks
            result_runs[i] = run_meta

            i = i+1

    return result_runs


def create_run_items(run):
        """Create a list of sorted run items.

        Args:
            run (dict): the description of the run and associated configs that is about to be executed.

        Returns
            list: a sorted list of all run items that were calculated out of the input configs
        """

        log.debug("Parsing configuration...")


        playbook_items = []

        run_name = run[RUN_NAME_KEY]
        runner = run[INT_RUN_RUNNER_KEY]

        frecks = run[RUN_FRECKS_KEY]

        freck_nr = 1
        for freck_meta in frecks:

            freck_configs = freck_meta[FRECK_CONFIGS_KEY]

            # get the freck object that is responsible for this item
            freck = runner.get_freck(freck_meta)
            # freck_meta[INT_FRECK_KEY] = freck
            freck_name = freck_meta[FRECK_NAME_KEY]
            if not freck:
                logging.error("Can't find freck: {}".format(freck_name))
                sys.exit(2)

            # merging all the configs that have accumulated for this freck and merge it ontop of the freck default config
            log.debug("\tAdding: {}".format(freck_name))
            freck_config = freck.calculate_freck_config(freck_configs)
            log.debug("Calculated config for '{}': {}".format(freck_meta[FRECK_DESC_KEY], freck_config))

            # check whether the config is valid for this freck (TODO not implemented yet)
            config_schema = freck.get_config_schema()
            if config_schema:
                log.debug("Checking schema for freck '{}'...".format(freck_desc))
                config_schema(freck_config)
                log.debug("Schema ok")
            else:
                log.debug("Omitting schama check for freck '{}': no schema provided.". format(freck_meta[FRECK_DESC_KEY]))

            # preprocess config
            # this is useful because some frecks actually produce multiple 'sub'-tasks. For example the install one can parse the dotfile app directories
            # create one task per folder/app.
            if freck_meta.get("freck_preprocess", True):
                log.debug("Preprocessing '{}' ({}): {}".format(freck_meta[FRECK_NAME_KEY], freck_meta[FRECK_DESC_KEY], freck_config))
                freck_config = freck.pre_process_config(freck_meta, freck_config)
                log.debug("Preprocessing done, result: {}".format(freck_config))

            freck_meta["freck_preprocess"] = False

            # now we let the frecks create the actual config items. Sometimes all this does is return the same config dict, sometimes another list of sub-tasks is returned.
            # if preprocessing returns a list, we add all those seperately.
            if isinstance(freck_config, dict):
                log.debug("Creating run items '{}' ({}): {}".format(freck_meta[FRECK_DESC_KEY], freck_meta[FRECK_NAME_KEY], freck_config))
                new_task = copy.deepcopy(freck_meta)
                freck_run_items = freck.create_run_items(new_task, freck_config)
                log.debug("Run items created, result: {}".format(freck_config))
                if isinstance(freck_run_items, dict):
                        freck_run_items = [freck_run_items]
            else:
                freck_run_items = []
                for item in freck_config:
                    log.debug("Creating run items '{}' ({}): {}".format(freck_meta[FRECK_DESC_NAME], freck_meta[FRECK_NAME_KEY], item))
                    new_task = copy.deepcopy(freck_meta)
                    temp = freck.create_run_items(new_task, item)
                    log.debug("Run items created, result: {}".format(temp))
                    if isinstance(temp, dict):
                        temp = [temp]
                    freck_run_items.extend(temp)


            # print(freck_config_items)
            # add item_name, if not provided by freck
            item_nr = 1
            for item in freck_run_items:
                item[INT_FRECK_KEY] = freck
                if FRECK_ITEM_NAME_KEY not in item.keys():
                    item[FRECK_ITEM_NAME_KEY] = "{}_{}".format(freck_name, item_nr)
                if FRECK_PRIORITY_KEY not in item.keys():
                    freck_prio = freck_meta.get(FRECK_PRIORITY_KEY, -1)
                    if freck_prio >= 0:
                        item[FRECK_PRIORITY_KEY] = freck_prio
                    else:
                        item[FRECK_PRIORITY_KEY] = FRECK_DEFAULT_PRIORITY + (freck_nr * 1000) + (item_nr * 10)

                item_nr = item_nr + 1

            freck_nr = freck_nr + 1
            playbook_items.extend(freck_run_items)

        if not playbook_items:
            return {}

        sorted_playbook_items = sorted(playbook_items, key=itemgetter(FRECK_PRIORITY_KEY))

        # add ids to every item
        id = 1
        result_items = OrderedDict()
        for item in sorted_playbook_items:
            item[FRECK_ID_KEY] = str(id)
            result_items[id] = item
            id = id+1

        return result_items


@six.add_metaclass(abc.ABCMeta)
class Freck(object):
    """Base class for freckles plugins ("Frecks"). Used to create run items and handle the output in order to display meaningful messages to the user.

    The only method that needs to be overwritten is the 'create_run_items' one. It is recommended to overwrite most of the others too.
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


    def pre_process_config(self, freck_meta, config):
        """(Optionally) pre-process or augment the config that will be injected in the 'create_run_itmes' method.

        This is used mostly for Frecks that create multiple Freck runs out of a single configuration, as is the case with most Frecks that use a dotfiles directory. In that case, usually one run item is created out of every sub-folder of a dotfile directory (one run per application), and this method will return a list of configs that is calculated from the single input config.

        Args:
            freck_meta (dict): freck specific meta information
            config (dict): the base config for a Freck run

        Returns:
            list: a list of dicts describing the Freck runs to execute subsequently. If a single dict is returned, it'll be wrapped into a list down the line, so that's also possible.
        """

        return config

    def calculate_freck_config(self, freck_configs, freck_meta={}):
        """Merges the default vars from the 'default_freck_config' method with the (potentially overlayed) vars that come from the user config.

        User vars will have precedence over the default_vars. This method should not be overwritten by a Freck.

        Args:
            freck_configs (list): the user-provided config vars
            freck_meta (dict): freck specific meta information


        Returns:
            dict: the merged config vars
        """

        freck_vars = {}
        for config in freck_configs:
            dict_merge(freck_vars, config)

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
    def create_run_items(self, freck_meta, config):
        """List of items to be included in the run.

        This is the main method in every Freck. In some cases all the work is already done in the 'pre_process_config' method, but most of the time you'll want to create a list of dicts here which describe the items to be executed.
        This method gets a 'deep' copy of the overall freck_meta dict, so this method is allowed to change the input dictionary.

        Args:
            freck_meta (dict): the meta_information about a freck (name, runner-specific config, etc.)
            config (dict): the user-provided and pre-processsed configuration for this run of the freck

        Returns:
            dict: the task description for this task
        """
        pass

    def handle_task_output(self, task, output_details):
        """Method to convert the output of a Freck run to something freckles can display nicely.

        For examples on how to implement this method, check out the 'install' and 'stow' implementations.

        Args:
            task (dict): the task details
            output_details (list): all the information that was recorded during the execution of that task (list of dicts)

        Result:
            dict: information about whether the task succeeded, or not, and also other details
        """

        skipped = True
        changed = False
        failed = False
        stderr = []
        stdout = []
        msg = []

        result = {}

        for details in output_details:

            task_name = details[TASK_NAME_KEY]
            if TASK_IGNORE_STRING in task_name:
                log.debug("Ignoring detail for task: {}".format(task_name))
                continue

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


class FrecklesRunCallback(object):

    def __init__(self, frecks, items, details=False):
        self.frecks = frecks
        self.items = items
        self.task_result = {}
        self.total_tasks = -1
        self.current_freck_id = -1
        self.details = details
        self.success = True

    def set_total_tasks(self, total):
        self.total_tasks = total

    def log(self, freck_id, details):

        #log.debug("Details for freck '{}': {}".format(freck_id, details))

        if details == RUN_FINISHED:
            if self.current_freck_id < 0:
                self.current_freck_id = freck_id
            freck_success = self.log_freck_complete(freck_id)
            if not freck_success:
                self.success = False
            return

        self.task_result.setdefault(freck_id, []).append(details)


        if self.current_freck_id != freck_id:
            # means new task
            if self.current_freck_id > 0:
                freck_success = self.log_freck_complete(self.current_freck_id)
                if not freck_success:
                    self.success = False
            self.current_freck_id = freck_id
            self.print_task_title(self.current_freck_id)


    def handle_task_output(self, task_item, output_details):
        """Converts ansible output into something human-readable.

        Internally, this forwards the output to the Freck that created the run item.

        Args:
            task_item (dict): details about the task that was executed
            output_details (dict): output as created by ansible

        Returns:
            dict: sanitized dictionary that freckles know how to display
        """

        # freck_type = task_item[FRECK_TYPE_KEY]
        # freck = self.frecks.get(freck_type)
        freck = task_item[INT_FRECK_KEY]

        result = freck.handle_task_output(task_item, output_details)

        return result

    def print_task_title(self, freckles_id):

        task_item = self.items[freckles_id]
        item_name = task_item[INT_FRECK_ITEM_NAME_KEY]
        task_desc = task_item[INT_FRECK_DESC_KEY]

        task_title = "- task {:02d}/{:02d}: {} '{}'".format(freckles_id, len(self.items), task_desc, item_name)
        click.echo(task_title, nl=False)


    def log_freck_complete(self, freckles_id):

        failed = False
        task_item = self.items[freckles_id]
        output_details = self.task_result[freckles_id]

        output = self.handle_task_output(task_item, output_details)
        log.debug("Result of task: {}".format(output))

        state_string = output[FRECKLES_STATE_KEY]

        click.echo("\t=> {}".format(state_string))

        if not self.details and state_string != FRECKLES_STATE_FAILED:
            return True

        if state_string == FRECKLES_STATE_SKIPPED:
            return True
        elif state_string == FRECKLES_STATE_FAILED:
            failed = True
            if output.get("stderr", False):
                log.error("Error:")
                for line in output["stderr"]:
                    log.error("\t{}".format(line.encode('utf8')))
                if output.get("stdout", False):
                    log.info("Standard output:")
                    for line in output.get("stdout", []):
                        log.error("\t{}".format(line.encode('utf8')))
            else:
                for line in output.get("stdout", []):
                    log.error("\t{}".format(line.encode('utf8')))
        else:
            for line in output.get("stdout", []):
                log.info("\t{}".format(line.encode('utf8')))

        return not failed


class Freckles(object):
    """The central class in this project. This calculates the items to execute out of the default values and overlayed user provided configuration.

    TODO: more doc
    """

    def __init__(self, *config_items):
        self.frecks = load_extensions()
        self.configs = config_items
        self.runs = create_runs(config_items, self.frecks)
        self.run_items = {}

    def create_run_items(self, run_nr):
        """Prepares run with the provided index number."""

        items = create_run_items(self.runs[run_nr])

        if not items:
            log.debug("No run items created, doing nothing in this run...")
            self.run_items[run_nr] = {}
            return

        self.runs[run_nr][INT_RUN_RUNNER_KEY].set_items(items)
        callback = FrecklesRunCallback(self.frecks, items)
        self.runs[run_nr][INT_RUN_RUNNER_KEY].set_callback(callback)
        self.run_items[run_nr] = items

        log.debug("Run created, {} run items created.".format(len(items)))


    def run(self, run_nr=None, only_prepare=False):

        if not run_nr:
            for run_nr in self.runs.keys():
                self.run(run_nr, only_prepare)

        else:

            log.info("Reading configuration for run #{}".format(run_nr))
            self.create_run_items(run_nr)

            if not self.run_items[run_nr]:
                log.info("No config or run items found, doing nothing...\n")
                return

            log.info("Preparing run...")
            self.runs[run_nr][INT_RUN_RUNNER_KEY].prepare_run()
            if only_prepare:
                log.info("'Only prepare'-flag was set, not running anything...")
                return
            log.info("Starting run #{}...".format(run_nr))
            try:
                os.system('setterm -cursor off')
                self.runs[run_nr][INT_RUN_RUNNER_KEY].run()
                log.info("Run #{} finished.".format(run_nr))
            except:
                log.error("Run #{} error.") # TODO: better error message
            finally:
                os.system('setterm -cursor on')

            if not self.runs[run_nr][INT_RUN_RUNNER_KEY].callback.success:
                raise FrecklesRunError("At least one error for run #{}. Exiting...".format(run_nr), self.runs[run_nr])

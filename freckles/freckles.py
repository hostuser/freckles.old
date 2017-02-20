# -*- coding: utf-8 -*-

import os
import click
from collections import OrderedDict
from sets import Set
import yaml
import pprint
import json
from runners.ansible_runner import AnsibleRunner
from utils import get_pkg_mgr_from_path, load_extensions, dict_merge, expand_config_url
import urllib2
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
from exceptions import FrecklesConfigError, FrecklesRunError


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


def create_runs(orig_configs, load_external=True):
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

            run_config_list = copy.deepcopy(config_list)
            print(runs)
            name = run_item.get(RUN_DESC_KEY, False)
            run_type = run_item.get(RUN_RUNNER_KEY, FRECKLES_DEFAULT_RUNNER)
            number = i
            if not name:
                name = "run_{}".format(i)

            i = i+1

            vars = run_item.get(RUN_VARS_KEY, {})
            frecks = run_item.get(RUN_FRECKS_KEY, [])
            if vars:
                run_config_list.append(copy.deepcopy(vars))
            run_frecks = []
            j = 1
            for freck in frecks:
                freck_config_list = copy.deepcopy(run_config_list)
                if isinstance(freck, dict):
                    if len(freck) != 1:
                        raise FrecklesConfigError("Can't read freck configuration in run {}, not exactly one key in dict.".fromat(name), "config", freck)
                    freck_name = freck.keys()[0]
                    freck_metadata = freck[freck_name]
                    if not isinstance(freck_metadata, dict):
                        raise FrecklesConfigError("Freck configuration for type {} in run {} not a dict, don't know what to do with that...".format(freck_name, name), "config", freck_metadata)

                    freck_desc = freck_metadata.get(FRECK_DESC_KEY, "freck_{}_{}".format(j, freck_name))
                    freck_type = freck_metadata.get(FRECK_TYPE_KEY, FRECK_DEFAULT_TYPE)
                    freck_inner_vars = freck_metadata.get(FRECK_VARS_KEY, {})
                elif not isinstance(freck, basestring):
                     raise FrecklesConfigError("Can't parse config in run {}".format(name), "config", freck)
                else:
                     freck_name = freck
                     freck_type = FRECK_DEFAULT_TYPE
                     freck_inner_vars = {}
                     freck_desc = "freck_{}_{}".format(j, freck_type)

                if freck_inner_vars:
                    freck_config_list.append(freck_inner_vars)
                test = INT_FRECK_TYPE_KEY
                run_frecks.append({INT_FRECK_DESC_KEY: freck_desc, INT_FRECK_TYPE_KEY: freck_type, INT_FRECK_NAME_KEY: freck_name, INT_FRECK_CONFIGS_KEY: freck_config_list})
                j = j + 1
            run = {RUN_DESC_KEY: name, RUN_FRECKS_KEY: run_frecks, RUN_RUNNER_KEY: run_type}
            result_runs[number] = run



    return result_runs


def create_run_items(run, runner):
        """Create a list of sorted run items.

        Args:
            run (dict): the description of the run and associated configs that is about to be executed.

        Returns
            list: a sorted list of all run items that were calculated out of the input configs
        """

        log.debug("Parsing configuration...")

        playbook_items = []

        run_name = run[RUN_DESC_KEY]
        frecks = run[RUN_FRECKS_KEY]

        for freck in frecks:

            freck_type = freck.get(INT_FRECK_TYPE_KEY, FRECK_DEFAULT_TYPE)
            freck_name = freck[INT_FRECK_NAME_KEY]
            freck_desc = freck[INT_FRECK_DESC_KEY]
            freck_configs = freck[INT_FRECK_CONFIGS_KEY]
            freck_configs.append({INT_FRECK_TYPE_KEY: freck_type, INT_FRECK_NAME_KEY: freck_name, INT_FRECK_DESC_KEY: freck_desc})

            freck = runner.get_freck(freck_name, freck_type, freck_configs)
            if not freck:
                logging.error("Can't find freck: {}".format(freck_name))
                sys.exit(2)

            log.debug("\tAdding: {}".format(freck_name))
            freck_config = freck.calculate_freck_config(freck_configs)

            log.debug("Calculated config for '{}': {}".format(freck_desc, freck_config))

            config_schema = freck.get_config_schema()
            if config_schema:
                log.debug("Checking schema for freck '{}'...".format(freck_desc))
                config_schema(freck_config)
                log.debug("Schema ok")
            else:
                log.debug("Omitting schama check for freck '{}': no schema provided.". format(freck_desc))

            if freck_config.get("freck_preprocess", True):
                log.debug("Preprocessing '{}' ({}): {}".format(freck_desc, freck_name, freck_config))
                freck_config = freck.pre_process_config(freck_config)
                log.debug("Preprocessing done, result: {}".format(freck_config))

            # if preprocessing returns a list, we add all those seperately.
            if isinstance(freck_config, dict):
                freck_config["freck_preprocess"] = False
                log.debug("Creating run items '{}' ({}): {}".format(freck_desc, freck_name, freck_config))
                freck_config_items = freck.create_run_items(freck_name, freck_type, freck_desc, freck_config)
                log.debug("Run items created, result: {}".format(freck_config))
                if isinstance(freck_config_items, dict):
                        freck_config_items = [freck_config_items]
            else:
                freck_config_items = []
                for item in freck_config:
                    item["freck_preprocess"] = False
                    log.debug("Creating run items '{}' ({}): {}".format(freck_desc, freck_name, item))
                    temp = freck.create_run_items(freck_name, freck_type, freck_desc, item)
                    log.debug("Run items created, result: {}".format(temp))
                    if isinstance(temp, dict):
                        temp = [temp]
                    freck_config_items.extend(temp)

            i = 1
            # add item_name, if not provided by freck

            for item in freck_config_items:
                item[INT_FRECK_KEY] = freck
                item[INT_FRECK_NAME_KEY] = freck_name
                item[INT_FRECK_DESC_KEY] = freck_desc
                if not item.get(INT_FRECK_ITEM_NAME_KEY, False):
                    item[INT_FRECK_ITEM_NAME_KEY] = "{}_{}".format(freck_name, i)
                i = i+1
                if not item.get(FRECK_PRIORITY_KEY, False):
                    item[FRECK_PRIORITY_KEY] = FRECK_DEFAULT_PRIORITY

            playbook_items.extend(freck_config_items)

        if not playbook_items:
            return {}

        sorted_playbook_items = sorted(playbook_items, key=itemgetter(FRECK_PRIORITY_KEY))

        # add ids to every item
        id = 1
        result_items = OrderedDict()
        for item in sorted_playbook_items:
            item[INT_FRECK_ID_KEY] = str(id)
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


    def pre_process_config(self, config):
        """(Optionally) pre-process or augment the config that will be injected in the 'create_run_itmes' method.

        This is used mostly for Frecks that create multiple Freck runs out of a single configuration, as is the case with most Frecks that use a dotfiles directory. In that case, usually one run item is created out of every sub-folder of a dotfile directory (one run per application), and this method will return a list of configs that is calculated from the single input config.

        Args:
            config (dict): the base config for a Freck run

        Returns:
            list: a list of dicts describing the Freck runs to execute subsequently. If a single dict is returned, it'll be wrapped into a list down the line, so that's also possible.
        """

        return config

    def calculate_freck_config(self, freck_configs):
        """Merges the default vars from the 'default_freck_config' method with the (potentially overlayed) vars that come from the user config.

        User vars will have precedence over the default_vars. This method should not be overwritten by a Freck.

        Args:
            freck_vars (list): the user-provided config vars


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

    def get_custom_roles(self):
        """Returns any custom roles this Freck might need to create on-the-fly, using dictionaries for tasks and default values.

        Implementing this method is optional, and is mainly used for the 'task'-freck.
        """

        return []

    def get_config_schema(self):
        """The schema for the configuration of this nect.

        Returns a schema that describes the expected input config vars. Useful to make sure required values are specified.
        Uses `voluptous <https://github.com/alecthomas/voluptuous>`_ schemas.
        """
        return False

    @abc.abstractmethod
    def create_run_items(self, freck_name, freck_type, freck_desc, config):
        """List of items to be included in the run.

        This is the main method in every Freck. In some cases all the work is already done in the 'pre_process_config' method, but most of the time you'll want to create a list of dicts here which describe the items to be executed.

        Args:
            freck_name (str): the name of the freck
            freck_type (str): the type of the freck
            freck_desc (str): short description of the freck
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

        log.debug("Details for freck '{}': {}".format(freck_id, details))

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
        task_desc = task_item[FRECK_TASK_DESC]

        task_title = "- task {:02d}/{:02d}: {} '{}'".format(freckles_id, len(self.items), task_desc, item_name)
        click.echo(task_title, nl=False)


    def log_freck_complete(self, freckles_id):

        failed = False
        task_item = self.items[freckles_id]
        output_details = self.task_result[freckles_id]

        output = self.handle_task_output(task_item, output_details)

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
                    log.error("\t{}".format(line))
                if output.get("stdout", False):
                    log.info("Standard output:")
                    for line in output.get("stdout", []):
                        log.error("\t{}".format(line))
            else:
                for line in output.get("stdout", []):
                    log.error("\t{}".format(line))
        else:
            for line in output.get("stdout", []):
                log.info("\t{}".format(line))

        return not failed


class Freckles(object):
    """The central class in this project. This calculates the items to execute out of the default values and overlayed user provided configuration.

    TODO: more doc
    """

    def __init__(self, *config_items):
        self.frecks = load_extensions()
        self.configs = config_items
        self.runs = create_runs(config_items)
        self.run_items = {}
        self.runners = {}

    def create_runner_and_items(self, run_nr):
        """Prepares run with the provided index number."""

        runner_name = self.runs[run_nr][RUN_RUNNER_KEY]
        runner_class = FRECKLES_RUNNERS.get(runner_name, False)
        if not runner_class:
            raise FrecklesConfigError("Can't find runner with name: {}".format(runner_name))
        runner = runner_class(self.frecks)
        items = create_run_items(self.runs[run_nr], runner)

        if not items:
            log.debug("No run items created, doing nothing in this run...")
            self.runners[run_nr] = None
            self.run_items[run_nr] = {}
            return

        self.runners[run_nr] = runner
        self.runners[run_nr].set_items(items)
        callback = FrecklesRunCallback(self.frecks, items)
        self.runners[run_nr].set_callback(callback)
        self.run_items[run_nr] = items

        log.debug("Run created, {} run items created.".format(len(items)))

        # make sure we only have one runner type for a run
        runners = Set()
        for key, item in items.iteritems():
            if not item.get(RUN_RUNNER_KEY, False):
                item[RUN_RUNNER_KEY] = FRECKLES_DEFAULT_RUNNER
            runners.add(item[RUN_RUNNER_KEY])

        if len(runners) != 1:
            raise FrecklesConfigError("Config error in run nr. {}, more than one type of runner for the runs' frecks: {}".format(run_nr, items))

        runner_name_frecks = runners.pop()
        if not runner_name == runner_name_frecks:
            raise FrecklesConfigError("Config error in run nr. {}: run has different runner configured than frecks support ({} => {}).".format(run_nr, runner_name, runner_name_frecks))


    def run(self, run_nr=None, only_prepare=False):

        if not run_nr:
            for run_nr in self.runs.keys():
                self.run(run_nr, only_prepare)

        else:

            log.info("Reading configuration for run #{}".format(run_nr))
            self.create_runner_and_items(run_nr)

            if not self.runners[run_nr]:
                log.info("No config or run items found, doing nothing...\n")
                return

            log.info("Preparing run...")
            self.runners[run_nr].prepare_run()
            if only_prepare:
                log.info("'Only prepare'-flag was set, not running anything...")
                return
            log.info("Starting run #{}...".format(run_nr))
            self.runners[run_nr].run()
            log.info("Run #{} finished.".format(run_nr))

            if not self.runners[run_nr].callback.success:
                raise FrecklesRunError("At least one error for run #{}. Exiting...".format(run_nr), self.runs[run_nr])

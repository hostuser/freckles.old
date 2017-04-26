# -*- coding: utf-8 -*-

import abc
import copy
import errno
import glob
import json
import logging
import os
import pprint
import shutil
import sys
import urllib2
import uuid
from collections import OrderedDict
from datetime import datetime
from exceptions import FrecklesConfigError, FrecklesRunError
from operator import itemgetter

import click
import six
import yaml

from constants import *
from freckles_runner import FrecklesRunner
from frkl import FRKL_META_LEVEL_KEY, LEAF_DICT, Frkl, expand_config_url
from runners.ansible_runner import AnsibleRunner
from sets import Set
from utils import (CursorOff, check_schema, dict_merge, get_pkg_mgr_from_path,
                   load_extensions)
from voluptuous import ALLOW_EXTRA, Any, Required, Schema

log = logging.getLogger("freckles")


FRECKLES_RUNNERS = {
    FRECKLES_ANSIBLE_RUNNER: AnsibleRunner
}

FRECKLES_META_VAR_SCHEMA =  Schema({
    Required(TASK_NAME_KEY): basestring,
    FRKL_META_LEVEL_KEY: int,
    FRECK_NEW_RUN_AFTER_THIS_KEY: bool,
    FRECK_SUDO_KEY: bool,
}, extra=True)
FRECKLES_INPUT_CONFIG_SCHEMA = Schema({
    FRECK_META_KEY: FRECKLES_META_VAR_SCHEMA,
    FRECK_VARS_KEY: dict,
    LEAF_DICT: dict
})

FRECKLES_POST_PREPROCESS_SCHEMA = Schema({
    Required(FRECK_NAME_KEY): basestring,
    FRECK_ITEM_NAME_KEY: basestring,
    FRECK_SUDO_KEY: bool,
    FRKL_META_LEVEL_KEY: int,
    Required(TASK_NAME_KEY): basestring,
    FRECK_PRIORITY_KEY: int,
    FRECK_INDEX_KEY: int,
    FRECK_DESC_KEY: basestring,
    FRECK_VARS_KEY: dict,
    FRECK_NEW_RUN_AFTER_THIS_KEY: bool,
    FRECK_RUNNER_KEY: Any(*FRECKLES_RUNNERS.keys())
}, extra=True)

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

    def process_leaf(self, leaf, supoported_runners=[FRECKLES_DEFAULT_RUNNER], debug=False):
        """(Optionally) pre-process or augment the config that will be injected in the 'create_run_itmes' method.

        This is used mostly for Frecks that create multiple Freck runs out of a single configuration, as is the case with most Frecks that use a dotfiles directory. In that case, usually one run item is created out of every sub-folder of a dotfile directory (one run per application), and this method will return a list of configs that is calculated from the single input config.

        Args:
            leaf (dict): freck config
            supported_runners (list): a list of runners that freckles supports on this system

        Returns:
            tuple: tuple (with choosen runner as key) containing a list of dicts describing the Freck runs to execute subsequently. If a single dict is returned, it'll be wrapped into a list down the line, so that's also possible.
        """
        leaf[FRECK_META_KEY][FRECK_VARS_KEY] = leaf.get(FRECK_VARS_KEY, {})
        return (FRECKLES_DEFAULT_RUNNER, leaf[FRECK_META_KEY])

    def calculate_freck_config(self, freck_configs, freck_meta, develop=False):
        """Merges the default vars from the 'default_freck_config' method with the (potentially overlayed) vars that come from the user config.

        User vars will have precedence over the default_vars. This method should not be overwritten by a Freck.

        Args:
            freck_configs (list): the user-provided config vars
            freck_meta (dict): freck specific meta information
            develop (bool): development-mode, outputs debug information for when developing frecks

        Returns:
            dict: the merged config vars
        """

        freck_vars = {}
        for config in freck_configs:
            dict_merge(freck_vars, config)

        freck_config = copy.deepcopy(FRECK_DEFAULT_CONFIG)
        dict_merge(freck_config, copy.deepcopy(self.default_freck_config()))
        dict_merge(freck_config, copy.deepcopy(freck_vars))

        if develop:
            click.echo("===============================================")
            click.echo("Calculated config after merging:")
            click.echo(pprint.pformat(freck_config))
            click.echo("-----------")

        return freck_config

    def get_config_schema(self):
        """The schema for the configuration of this nect.

        Returns a schema that describes the expected input config vars. Useful to make sure required values are specified.
        Uses `voluptous <https://github.com/alecthomas/voluptuous>`_ schemas.
        """
        return False

    def can_be_used_for(self, freck_meta):
        """Returns whether this freck can be used for the provided configuration

        Args:
            freck_meta (dict): freck meta configuration

        Returns:
            bool: whether this freck handles this config item or not
        """

        return False

    @abc.abstractmethod
    def create_run_item(self, freck_meta, develop=False):
        """List of items to be included in the run.

        This is the main method in every Freck. In some cases all the work is already done in the 'pre_process_config' method, but most of the time you'll want to create a list of dicts here which describe the items to be executed.
        This method gets a 'deep' copy of the overall freck_meta dict, so this method is allowed to change the input dictionary.

        Args:
            freck_meta (dict): the meta_information about a freck (name, runner-specific config, etc.)
            config (dict): the user-provided and pre-processsed configuration for this run of the freck
            develop (bool): enables develop mode, for when developing frecks

        Returns:
            dict: the task description for this task
        """
        pass



class FrecklesRunCallback(object):

    def __init__(self, run_nr, frecks, items, details=False):
        self.frecks = frecks
        self.items = {}
        for item in items:
            self.items[item[FRECK_ID_KEY]] = item
        self.task_result = {}
        self.total_tasks = -1
        self.current_freck_id = -1
        self.detailed_output = details
        self.success = True

        self.log_file = os.path.join(FRECKLES_DEFAULT_EXECUTION_LOGS_DIR, "run_log")


    def set_total_tasks(self, total):
        self.total_tasks = total
        #self.log(1, RUN_STARTED)


    def log(self, freck_id, details):

        try:
            os.makedirs(FRECKLES_DEFAULT_EXECUTION_LOGS_DIR)
        except OSError as exc:  # Python >2.5
            if exc.errno == errno.EEXIST and os.path.isdir(FRECKLES_DEFAULT_EXECUTION_LOGS_DIR):
                pass
            else:
                raise
        with open(self.log_file, "a+") as myfile:
            myfile.write("{}\n".format(details))


        #log.debug("Details for freck '{}': {}".format(freck_id, details))
        if details == RUN_STARTED:
            self.print_task_title(freck_id)
            return

        if details == RUN_FINISHED:
            if self.current_freck_id < 0:
                self.current_freck_id = freck_id
            freck_success = self.log_freck_complete(freck_id)
            if not freck_success:
                self.success = False
            return

        if freck_id not in self.items.keys():
            log.debug("No task associated to reported freck_id '{}': {}".format(freck_id, details))
            return

        self.task_result.setdefault(freck_id, []).append(details)

        if self.current_freck_id != freck_id:
            if self.current_freck_id > 0:
                # means new task
                freck_success = self.log_freck_complete(self.current_freck_id)
                if not freck_success:
                    self.success = False

            self.current_freck_id = freck_id
            self.print_task_title(self.current_freck_id)

        else:
            if self.detailed_output:
                click.echo("\n  . {}".format(self.get_summary_string_from_detaila(details)), nl=False)


    def get_summary_string_from_detaila(self, details):
        """Produces a human readable string from the current details dict."""

        action = details["action"]
        freck_id = details["freck_id"]
        state = details["state"]
        task_name = details["task_name"]

        return "{}: {} -> {}".format(task_name, action, state)

    def handle_freck_task_output(self, task, output_details):
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

        freck = self.frecks[task[FRECK_NAME_KEY]]
        ignored_strings = [TASK_IGNORE_STRING]

        for details in output_details:

            task_name = details[TASK_NAME_KEY]
            ignore_changed = False
            for ignored_string in ignored_strings:
                if ignored_string in task_name:
                    log.debug("Ignoring detail for task: {}".format(task_name))
                    ignore_changed = True
                    break

            if details[FRECKLES_STATE_KEY] != FRECKLES_STATE_SKIPPED:
                skipped = False

                if details[FRECKLES_STATE_KEY] == FRECKLES_STATE_FAILED:
                    failed = True
                if not ignore_changed and details["result"].get(FRECKLES_CHANGED_KEY, False):
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

        result = self.handle_freck_task_output(task_item, output_details)

        return result

    def print_task_title(self, freckles_id):

        task_item = self.items[freckles_id]
        item_name = task_item[FRECK_ITEM_NAME_KEY]
        task_desc = task_item[FRECK_DESC_KEY]

        task_title = "- task {:02d}/{:02d}: {} '{}'".format(freckles_id, len(self.items), task_desc, item_name)
        nl = False
        if log.getEffectiveLevel() < 20:
            nl = True

        click.echo(task_title, nl=nl)


    def log_freck_complete(self, freckles_id):

        failed = False

        task_item = self.items[freckles_id]
        if freckles_id not in self.task_result.keys():
            log.debug("Unreckognized task_id for: {}".format(freckles_id))
            return
        output_details = self.task_result[freckles_id]

        output = self.handle_task_output(task_item, output_details)

        log.debug("Result of task: {}".format(output))

        state_string = output[FRECKLES_STATE_KEY]

        click.echo("\t=> {}".format(state_string))

        if  state_string != FRECKLES_STATE_FAILED:
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

        self.freck_plugins = load_extensions()
        self.supported_runners = [FRECKLES_DEFAULT_RUNNER]
        self.configs = config_items
        frkl = Frkl(self.configs, FRECK_TASKS_KEY, [FRECK_VARS_KEY, FRECK_META_KEY], FRECK_META_KEY, TASK_NAME_KEY, FRECK_VARS_KEY, DEFAULT_DOTFILE_REPO_NAME, FRECKLES_DEFAULT_FRECKLES_BOOTSTRAP_CONFIG_PATH, add_leaf_dicts=True)
        self.leafs = frkl.leafs
        self.debug_freck = False


    def set_debug(self, debug_freck):
        self.debug_freck = debug_freck


    def preprocess_configs(self):

        for leaf in self.leafs:
            check_schema(leaf, FRECKLES_INPUT_CONFIG_SCHEMA)
            if FRECK_META_KEY not in leaf.keys():
                continue
            if leaf[FRECK_META_KEY][TASK_NAME_KEY] in self.freck_plugins.keys():
                leaf[FRECK_META_KEY][FRECK_NAME_KEY] = leaf[FRECK_META_KEY][TASK_NAME_KEY]
                continue

            freck_to_use = False
            for freck_name, freck in self.freck_plugins.iteritems():
                if freck.can_be_used_for(copy.deepcopy(leaf[FRECK_META_KEY])):
                    freck_to_use = freck_name
                    break

            if not freck_to_use:
                raise FrecklesConfigError("Can't find freck that can execute task with name '{}' (full config: {})".format(leaf[FRECK_META_KEY][TASK_NAME_KEY], leaf[FRECK_META_KEY]), FRECK_META_KEY, leaf[FRECK_META_KEY])

            leaf[FRECK_META_KEY][FRECK_NAME_KEY] = freck_to_use


    def process_leafs(self):

        frecks = []
        for freck_nr, leaf in enumerate(self.leafs):
            if FRECK_META_KEY not in leaf.keys():
                continue
            freck_name = leaf[FRECK_META_KEY][FRECK_NAME_KEY]

            runner, processed = self.freck_plugins[freck_name].process_leaf(copy.deepcopy(leaf), self.supported_runners, self.debug_freck)


            if not processed:
                log.debug("No frecks created for freck_name '{}'.".format(freck_name))
                continue

            if self.debug_freck:
                click.echo("Processed leaf '{}'.".format(freck_name))
                click.echo("---")
                click.echo("Input:")
                click.echo(pprint.pformat(leaf))
                click.echo("---")
                click.echo("Result:")
                click.echo(pprint.pformat(processed))
                click.echo("===============================================")

            if isinstance(processed, dict):
                processed = [processed]

            # apply result on top of original configuration
            temp = []
            for p in processed:
                t = copy.deepcopy(leaf[FRECK_META_KEY])
                dict_merge(t, p)
                temp.append(t)

            processed = temp

            new_run = False
            for prep in processed:

                prep[FRECK_RUNNER_KEY] = runner
                prep[FRECK_INDEX_KEY] = freck_nr
                prep.setdefault(FRECK_ITEM_NAME_KEY, "{}".format(prep[FRECK_NAME_KEY]))
                prep.setdefault(FRECK_NEW_RUN_AFTER_THIS_KEY, False)
                if FRECK_PRIORITY_KEY not in prep.keys():
                    prep[FRECK_PRIORITY_KEY] = FRECK_DEFAULT_PRIORITY + (freck_nr * 1000)
                check_schema(prep, FRECKLES_POST_PREPROCESS_SCHEMA)

                if prep[FRECK_NEW_RUN_AFTER_THIS_KEY]:
                    new_run = True

            frecks.extend(processed)

            if new_run:
                frecks = self.sort_frecks(frecks)
                run_frecks = []

                for f in frecks:
                    run_frecks.append(f)
                    if f[FRECK_NEW_RUN_AFTER_THIS_KEY]:
                        yield self.sort_frecks(run_frecks)
                        run_frecks = []

                frecks = run_frecks

        yield self.sort_frecks(frecks)

    def sort_frecks(self, frecks):

        sorted_frecks = sorted(frecks, key=itemgetter(FRECK_PRIORITY_KEY, FRECK_ITEM_NAME_KEY))
        # fill default values if necessary
        sorted_result = []
        for freck in sorted_frecks:
            freck.setdefault(FRECK_DESC_KEY, "--config-item {}-- {}".format(freck[FRECK_INDEX_KEY], freck[FRECK_NAME_KEY]))
            freck.setdefault(FRECK_SUDO_KEY, FRECK_DEFAULT_SUDO)
            freck.setdefault(FRECK_VARS_KEY, {})
            sorted_result.append(freck)

        return sorted_result


    def run(self, details=False):

        start_date = datetime.now()
        date_string = start_date.strftime('%y%m%d_%H_%M_%S')
        archive_dirname = os.path.join(FRECKLES_DEFAULT_EXECUTION_ARCHIVE_DIR, date_string)
        os.makedirs(archive_dirname)

        for run_nr, frecks in enumerate(self.process_leafs(), start=1):

            click.echo("Preparing run #{}".format(run_nr))
            # check all frecks have the same runner
            runners = Set([ item[FRECK_RUNNER_KEY] for item in frecks ])
            if len(runners) > 1:
                raise Exception("Can't use multiple runners in the same run: {}".format(runners))

            runner_name = runners.pop()

            if runner_name not in FRECKLES_RUNNERS.keys():
                raise FrecklesConfigError("Runner '{}' not supported.".format(runner_name), RUN_RUNNER_NAME_KEY, runner_name)
            runner_class = FRECKLES_RUNNERS.get(runner_name, False)
            if not runner_class:
                raise FrecklesConfigError("Can't find runner with name: {}".format(runner_name))

            log.debug("Using runner: {}".format(runner_name))
            items = []
            i = 1
            unique_ids = []
            for freck in frecks:

                freck_plugin = self.freck_plugins[freck[FRECK_NAME_KEY]]

                run_item = freck_plugin.create_run_item(copy.deepcopy(freck), self.debug_freck)
                if not isinstance(run_item, dict):
                    raise Exception("Freck plugin returned non-dict value as run_item")

                if UNIQUE_TASK_ID_KEY in run_item.keys() and run_item[UNIQUE_TASK_ID_KEY] in unique_ids:
                    log.debug("Already got a task with id '{}', ignoring this one.".format(run_item[UNIQUE_TASK_ID_KEY]))
                    continue
                elif UNIQUE_TASK_ID_KEY in run_item.keys():
                    unique_ids.append(run_item[UNIQUE_TASK_ID_KEY])


                # make sure the id didn't change, everything else can be different
                run_item[FRECK_ID_KEY] = i
                run_item.setdefault(FRECK_SUDO_KEY, FRECK_DEFAULT_SUDO)
                run_item.setdefault(FRECK_VARS_KEY, {})
                items.append(run_item)
                i = i + 1

            callback = FrecklesRunCallback(run_nr, self.freck_plugins, items, details)
            runner_obj = runner_class(items, callback)

            click.echo("Starting run #{}".format(run_nr))
            success = runner_obj.run()
            click.echo("Run #{} finished: {}".format(run_nr, ("success" if success else "failed")))

            dest_dir = os.path.join(archive_dirname, "run_{}".format(run_nr))
            log.debug("Moving run directory to archive: {}".format(dest_dir))
            shutil.move(FRECKLES_DEFAULT_EXECUTION_DIR, dest_dir)

            if os.path.exists(FRECKLES_DEFAULT_LAST_EXECUTION_DIR):
                os.unlink(FRECKLES_DEFAULT_LAST_EXECUTION_DIR)
            log.debug("Creating archive directory to last run convenience link")
            os.symlink(dest_dir, FRECKLES_DEFAULT_LAST_EXECUTION_DIR)
            if not success:
                click.echo("\nRun failed, exiting...")
                sys.exit(1)

# -*- coding: utf-8 -*-

import json
import logging
import os
import pprint
import subprocess
import sys
import urllib
from copy import copy
from exceptions import FrecklesRunError

import click
import yaml

import click_log
import py
from constants import *
from freckles import Freckles

from . import __version__ as VERSION

log = logging.getLogger("freckles")

DEFAULT_INDENT = 2

class Config(object):
    """Freckles app config object, stores local configuration.

    The default Freckles configuration is located in $HOME/.freckles. If this directory does not exist, Freckles looks for a directory ``$HOME/dotfiles/freckles/.freckles`` and, if that exists, uses that as default. Reason is that there might already be a dotfiles repo checked out or copied to the local machine, but no 'stow' operation had been done on it yet.

    The default freckles file is called ``config.yml`` and is located in the default freckles config directory.

    Attributes:
        config_dir (str): the directory containing freckles configuration
        config_file (str): the path to the config file
        config (dict): other config values
    """

    def __init__(self, *args, **kwargs):
        self.config_dir = FRECKLES_DEFAULT_DIR
        if not os.path.isdir(self.config_dir):
            alt_dir = os.path.join(DEFAULT_DOTFILE_DIR, "freckles", ".freckles")
            if os.path.isdir(alt_dir):
                self.config_dir = alt_dir

        self.config_file = py.path.local(self.config_dir).join(FRECKLES_DEFAULT_CONFIG_FILE_NAME)
        self.config = dict(*args, **kwargs)

    def load(self):
        """load yaml config from disk"""

        try:
            yaml_string = self.config_file.read()
            self.config.update(yaml.load(yaml_string))
        except py.error.ENOENT:
            pass

    def save(self, initial_config=None):
        """save yaml config to disk"""

        if not self.config:
            if not initial_config:
                log.debug("No config defined, no point saving.")
                return
                # initial_config = create_default_config()
            self.config = initial_config

        self.config_file.ensure()
        with self.config_file.open('w') as f:
            yaml.safe_dump(self.config, f, default_flow_style=False)

    def get(self, key):
        """Returns the value for the specified key"""
        return self.config.get(key, None)


pass_freckles_config = click.make_pass_decorator(Config, ensure=True)

@click.group(invoke_without_command=True)
@pass_freckles_config
@click.pass_context
@click_log.simple_verbosity_option()
@click.option('--version', help='the version of freckles you are running', is_flag=True)
@click_log.init("freckles")
def cli(ctx, freckles_config, version):
    """Freckles manages your dotfiles (and other aspects of your local machine).

    The base options here are forwarded to all the sub-commands listed below. Not all of the sub-commands will use all of the options you can specify though.

    For information about how to use and configure Freckles, please visit: XXX
    """

    if version:
        click.echo(VERSION)
        sys.exit(0)

    freckles_config.load()
    augment_config(freckles_config)

    # if ctx.invoked_subcommand is None:
        # run(config)


def augment_config(freckles_config):
    """Helper method to make sure the configuration is complete."""

    pass

@cli.command()
@click.option('--run_nr', '-r', required=False, help='only kick off one run, using it\'s index', default=0)
@click.option('--details', help='whether to print details of the results of the  operations that are executed, or not', default=False, is_flag=True)
@click.option('--only-prepare', '-p', required=False, default=False, help='Only prepare the run(s), don\'t kick them off', is_flag=True)
@click.argument('config', required=False, nargs=-1)
@pass_freckles_config
def run(freckles_config, run_nr, details, only_prepare, config):
    """Executes one or multiple runs.

    A config can either be a local yaml file, a url to a remote yaml file, or a json string.

    Configurations are overlayed in the order they are provided. Read more about configuration files and format by visiting XXX``).
    """

    freckles = Freckles(*config)
    if run_nr > 0:
        freckles.run(run_nr, only_prepare=only_prepare)
    else:
        freckles.run(only_prepare=only_prepare)


@cli.command("print-config")
@click.argument('config', required=False, nargs=-1)
@pass_freckles_config
def print_config(freckles_config, config):
    """Flattens overlayed configs and prints result.

    This is useful mostly for debugging purposes, when creating the configuration.

    The output to this command could be piped into a yaml file, and then used with the ``run`` command. Although, in practice that doesn't make much sense of course. """

    freckles = Freckles(*config)
    result_runs = []
    for run, run_details in freckles.runs.iteritems():

        output_frecks = []
        run_name = run_details[RUN_DESC_KEY]
        run_nr = run
        frecks = run_details[RUN_FRECKS_KEY]

        freckles.create_runner_and_items(run_nr)
        run_items = freckles.run_items[run_nr]
        for run_item_nr, run_item in run_items.iteritems():
            freck_name = run_item.pop(INT_FRECK_NAME_KEY, None)
            freck_type = run_item.pop(INT_FRECK_TYPE_KEY, None)
            freck_desc = run_item.pop(INT_FRECK_DESC_KEY, None)
            freck_object = run_item.pop(INT_FRECK_KEY, None)

            output_frecks.append({freck_name: {FRECK_TYPE_KEY: freck_type, FRECK_DESC_KEY: freck_desc, FRECK_VARS_KEY: run_item}})

        result_runs.append({RUN_DESC_KEY: run_name, RUN_FRECKS_KEY: output_frecks})

    print(yaml.dump({"runs": result_runs}, default_flow_style=False))



    # runs = create_runs(config)

    # result_runs = []

    # for run in runs:
    #     run_name = run["name"]
    #     run_nr = run["nr"]
    #     playbook_items = freckles_config.freckles.create_playbook_items(run)
    #     frecks = []
    #     for item_nr, item in playbook_items.iteritems():
    #         freck_type = item.pop(FRECK_TYPE_KEY)
    #         freck_name = item.pop(FRECK_NAME_KEY)
    #         freckles_id = item.pop(FRECK_ID_KEY) # we don't need this id, still pulling it out

    #         frecks.append({freck_type: {"name": freck_name, "vars": item}})

    #     result_runs.append({"name": run_name, "frecks": frecks})






def start_runs(config):
    """Helper method to kick off all runs."""

    for run in config.runs:
        run_nr = run["nr"]
        log.info("Reading configuration for run #{}".format(run_nr))
        runner = FrecklesRunner(config.freckles, run, clear_build_dir=True, execution_base_dir=config.get("build_base_dir"), execution_dir_name=config.get("build_dir_name"), details=config.get("details"))
        if not runner.playbook_items:
            log.info("No config found, doing nothing...")
        else:
            log.info("Starting run #{}...".format(run_nr))
            success = runner.run()
            log.info("Run #{} finished.".format(run_nr))
            if not success:
                raise FrecklesRunError("At least one error for run #{}. Exiting...".format(run_nr), run)

        run_nr = run_nr + 1

if __name__ == "__main__":
    cli()

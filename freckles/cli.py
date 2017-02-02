# -*- coding: utf-8 -*-

import subprocess
import urllib
import click
import click_log
from freckles import Freckles
import pprint
import py
import yaml
import os
import json
from freckles_runner import FrecklesRunner
from constants import *
import sys
import logging
from utils import expand_repo_url, expand_config_url, expand_bootstrap_config_url, create_runs
from copy import copy

log = logging.getLogger("freckles")

DEFAULT_INDENT = 2



class Config(object):

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


pass_config = click.make_pass_decorator(Config, ensure=True)

@click.group(invoke_without_command=True)
@pass_config
@click.pass_context
@click_log.simple_verbosity_option()
@click_log.init("freckles")
@click.option('--details', help='whether to print details of the results of the  operations that are executed, or not', default=False, is_flag=True)
def cli(ctx, config, details):

    config.load()

    augment_config(config, details)

    # if ctx.invoked_subcommand is None:
        # run(config)


def augment_config(config, details=False):

    config.details = details


@cli.command()
@click.argument('config_file_urls', required=False, nargs=-1)
@pass_config
def run(config, config_file_urls):

    if config_file_urls:
        config.runs = create_runs(config_file_urls)
        config.freckles = Freckles()
    else:
        # TODO: auto-magic config creation
        pass

    start_runs(config)


@cli.command()
@pass_config
def config(config):

    print(yaml.dump(config.config, default_flow_style=False))

@cli.command()
@click.argument('config_file_urls', required=True, nargs=-1)
@pass_config
def test(config, config_file_urls):

    runs = create_runs(config_file_urls)

    print(yaml.dump(runs, default_flow_style=False))


def start_runs(config):

    run_nr = 1
    for run in config.runs:
        log.info("Reading configuration for run #{}".format(run_nr))
        runner = FrecklesRunner(config.freckles, run, clear_build_dir=True, execution_base_dir=config.get("build_base_dir"), execution_dir_name=config.get("build_dir_name"), details=config.get("details"))
        if not runner.playbook_items:
            log.info("No config found, doing nothing...")
        else:
            log.info("Starting run #{}...".format(run_nr))
            success = runner.run()
            log.info("Run #{} finished.".format(run_nr))
            if not success:
                log.error("\tAt least one error for run #{}. Exiting...".format(run_nr))
                sys.exit(FRECKLES_EXECUTION_ERROR_EXIT_CODE)

        run_nr = run_nr + 1

if __name__ == "__main__":
    cli()

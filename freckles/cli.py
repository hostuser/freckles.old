# -*- coding: utf-8 -*-

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
from utils import expand_repo_url
from copy import copy

log = logging.getLogger("freckles")

DEFAULT_INDENT = 2

def create_default_config(base_dir, paths, remote):

    if not base_dir:
        base_dir = DEFAULT_DOTFILE_DIR
    if not paths:
        paths = DEFAULT_DOTFILE_PATHS
    if not remote:
        remote = DEFAULT_DOTFILE_REMOTE

    result = {}
    result["default_vars"] = {
        DOTFILES_KEY: {
            DOTFILES_BASE_KEY: base_dir,
            DOTFILES_PATHS_KEY: paths,
            DOTFILES_REMOTE_KEY: remote
        }
    }
    result["runs"] = [
        {"frecks": {"checkout": {}}},
        {"frecks": {"install": {}, "stow": {}}}
    ]

    return result

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
                initial_config = create_default_config()
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
@click.option('--hosts', help='comma-separated list of hosts (default: \'localhost\'), overrides config', multiple=True)
@click.option('--details', help='whether to print details of the results of the  operations that are executed, or not', default=False, is_flag=True)
@click.option('--dotfile-remote', help='git repo url to use, can overwrite config file, mostly useful for initial checkout/bootstrapping')
@click.option('--dotfile-base', help='(dotfiles) base path, can overwrite config file, mostly useful for initial checkout/bootstrapping. Defaults to "$HOME/dotfiles"')
@click.option('--dotfile-paths', help='comman-separated (dotfiles) relative paths, can overwrite config file, mostly useful for initial checkout/bootstrapping. Will be left blank in most cases.')
# @click.option('--dotfiles', help='base-path(s) for dotfile directories (can be used multiple times), overrides config', type=click.Path(exists=True, dir_okay=True, readable=True, resolve_path=True), multiple=True)
def cli(ctx, config, hosts, details, dotfile_base, dotfile_paths, dotfile_remote):

    config.load()

    if not config.config:
        # config.save(initial_config=create_default_config(dotfile_base, dotfile_paths, dotfile_remote))
        config.config = create_default_config(dotfile_base, dotfile_paths, dotfile_remote)

    if hosts:
        config.config["hosts"] = hosts
    else:
        config.config["hosts"] = FRECKLES_DEFAULT_HOSTS

    config.config["details"] = details

    config.freckles = Freckles(hosts=config.config["hosts"], default_vars=config.config.get("default_vars", {}))
    config.runs = config.config.get("runs", {})

    if ctx.invoked_subcommand is None:
        run(config)


@cli.command()
@click.argument()
@pass_config
def init(config):

    config.save()
    click.echo("Saved config")

@cli.command()
@pass_config
def inventory(config):

    inv = config.freckles.create_inventory()
    inv_json = json.dumps(inv, sort_keys=True, indent=DEFAULT_INDENT)

    click.echo(inv_json)

def run(config):

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

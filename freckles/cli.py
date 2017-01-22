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
log = logging.getLogger("freckles")

# if not os.path.exists(FRECKLES_DEFAULT_LOG_DIR):
    # os.makedirs(FRECKLES_DEFAULT_LOG_DIR)
# logging.basicConfig(filename=FRECKLES_DEFAULT_LOG_FILE, level=logging.DEBUG)

DEFAULT_INDENT = 2

DEFAULT_CONFIG = {
    "frecks": {
        "default": {
            DOTFILES_KEY: DEFAULT_DOTFILES
        },
        "install": {},
        "stow": {}
    }
}

class Config(object):

    def __init__(self, *args, **kwargs):
        self.config_dir = FRECKLES_DEFAULT_DIR
        self.config_file = py.path.local(self.config_dir).join(FRECKLES_DEFAULT_CONFIG_FILE_NAME)
        self.config = dict(*args, **kwargs)

    def load(self):
        """load yaml config from disk"""

        try:
            yaml_string = self.config_file.read()
            self.config.update(yaml.load(yaml_string))
        except py.error.ENOENT:
            pass

    def save(self):
        """save yaml config to disk"""

        if not self.config:
            self.config = DEFAULT_CONFIG

        self.config_file.ensure()
        with self.config_file.open('w') as f:
            yaml.safe_dump(self.config, f, default_flow_style=False)

    def get(self, key):
        """Returns the value for the specified key"""
        return self.config.get(key, None)

    def get_execution_dir(self):
        """returns the execution directory"""

        return os.path.join(self.config.get("build_base_dir"), self.config.get("build_dir_name"))

    def get_dotfile_dirs(self):
        """returns default dotfile directories"""

        return self.config.get("dotfiles")

pass_config = click.make_pass_decorator(Config, ensure=True)

@click.group(invoke_without_command=True)
@pass_config
@click.pass_context
@click_log.simple_verbosity_option()
@click_log.init("freckles")
@click.option('--hosts', help='comma-separated list of hosts (default: \'localhost\'), overrides config', multiple=True)
@click.option('--details', help='whether to print details of the results of the  operations that are executed, or not', default=False, is_flag=True)
# @click.option('--dotfiles', help='base-path(s) for dotfile directories (can be used multiple times), overrides config', type=click.Path(exists=True, dir_okay=True, readable=True, resolve_path=True), multiple=True)
def cli(ctx, config, hosts, details):

    config.load()

    if not config.config:
        config.save()

    if hosts:
        config.config["hosts"] = hosts

    config.config["details"] = details

    config.freckles = Freckles(config.config)

    if ctx.invoked_subcommand is None:
        run(config)


@cli.command()
@pass_config
def playbook(config):

    play = config.freckles.create_playbook_string()
    click.echo(play)

@cli.command()
@pass_config
def inventory(config):

    inv = config.freckles.create_inventory()
    inv_json = json.dumps(inv, sort_keys=True, indent=DEFAULT_INDENT)

    click.echo(inv_json)

def run(config):

    runner = FrecklesRunner(config.freckles, clear_build_dir=True, execution_base_dir=config.get("build_base_dir"), execution_dir_name=config.get("build_dir_name"), details=config.get("details"))
    runner.run()


if __name__ == "__main__":
    cli()

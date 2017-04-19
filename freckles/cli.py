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
from frkl import Frkl
from utils import CursorOff

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

@cli.command("apply")
@click.option('--details', help='whether to print details of the results of the  operations that are executed, or not', default=False, is_flag=True)
@click.option('--debug', help='print debug information for each freck', default=False, is_flag=True)
# @click.option('--only-prepare', '-p', required=False, default=False, help='Only prepare the run(s), don\'t kick them off', is_flag=True)
@click.argument('config', required=False, nargs=-1)
@pass_freckles_config
def run(freckles_config, details, config, debug):
    """Executes one or multiple runs.

    A config can either be a local yaml file, a url to a remote yaml file, or a json string.

    Configurations are overlayed in the order they are provided. Read more about configuration files and format by visiting XXX``).
    """

    freckles = Freckles(*config)
    freckles.set_debug(debug)
    freckles.preprocess_configs()
    with CursorOff():
        freckles.run(details)


@cli.command("print-config")
@click.argument('config', required=False, nargs=-1)
@pass_freckles_config
def print_config(freckles_config, config):
    """Flattens overlayed configs and prints result.
       This is useful mostly for debugging purposes, when creating the configuration.

       The output to this command could be piped into a yaml file, and then used with the ``run`` command. Although, in practice that doesn't make much sense of course. """

    freckles = Freckles(*config)
    leafs = freckles.leafs

    print(yaml.dump(leafs, default_flow_style=False))

if __name__ == "__main__":
    cli()

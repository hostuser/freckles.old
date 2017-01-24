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
from utils import expand_repo_url, expand_config_url, expand_bootstrap_config_url
from copy import copy

log = logging.getLogger("freckles")

DEFAULT_INDENT = 2

def guess_local_default_config(base_dir=None, paths=None, remote=None):

    result = {}
    result["default_vars"] = {}
    result["default_vars"][DOTFILES_KEY] = {}

    if not base_dir:
        if os.path.isdir(DEFAULT_DOTFILE_DIR):
            result["default_vars"][DOTFILES_KEY][DOTFILES_BASE_KEY] = DEFAULT_DOTFILE_DIR
    else:
        if os.path.isdir(base_dir):
            result["default_vars"][DOTFILES_KEY][DOTFILES_BASE_KEY] = base_dir
        else:
            log.error("Directory '{}' does not exist. Exiting...".format(base_dir))
            sys.exit(FRECKLES_CONFIG_ERROR_EXIT_CODE)

    if not result["default_vars"][DOTFILES_KEY].get(DOTFILES_BASE_KEY, False):
        return False

    if paths:
        if not result["default_vars"][DOTFILES_KEY].get(DEFAULT_DOTFILE_DIR, False):
            log.error("Paths specified, but not base dir. Can't continue, exiting...")
            sys.exit(FRECKLES_CONFIG_ERROR_EXIT_CODE)
        for p in paths:
            path = os.path.join(result["default_vars"][DOTFILES_KEY][DEFAULT_DOTFILE_DIR], p)
            if not os.path.isdir(path):
                log.error("Combined dotfile path '{} does not exist, exiting...".format(path))
                sys.exit(FRECKLES_CONFIG_ERROR_EXIT_CODE)


    # check if base_dir is git repo
    remotes = []
    if result["default_vars"][DOTFILES_KEY].get(DOTFILES_BASE_KEY, False):
        git_config_file = os.path.join(result["default_vars"][DOTFILES_KEY][DOTFILES_BASE_KEY], ".git", "config")
        if os.path.isfile(git_config_file):
            with open(git_config_file) as f:
                content = f.readlines()
            in_remote = False
            for line in content:
                if not in_remote:
                    if "[remote " in line:
                        in_remote = True
                    continue
                else:
                    if "url = " in line:
                        remote = line.strip().split()[-1]
                        remotes.append(remote)
                        in_remote = False
                        continue

    # TODO: this all is a bit crude, should just use git exe to figure out remotes
    if not remote:
        if len(remotes) == 1:
            result["default_vars"][DOTFILES_KEY][DOTFILES_REMOTE_KEY] = remotes[0]
        elif len(remotes) > 1:
            log.error("Can't guess git remote, more than one configured. Exiting...")
            sys.exit(FRECKLES_CONFIG_ERROR_EXIT_CODE)
    else:
        if len(remotes) == 1:
            if remotes[0] == remote:
                result["default_vars"][DOTFILES_KEY][DOTFILES_REMOTE_KEY] = remote
            else:
                log.error("Provided git remote '{}' differs from local one '{}'. Exiting...".format(remote, remotes[0]))
                sys.exit(FRECKLES_CONFIG_ERROR_EXIT_CODE)
        elif len(remotes) == 0:
            log.error("git remote provided, but local repo is not configured to use it. Exiting...")
            sys.exit(FRECKLES_CONFIG_ERROR_EXIT_CODE)
        else:
            if remote in remotes:
                result["default_vars"][DOTFILES_KEY][DOTFILES_REMOTE_KEY] = remote
            else:
                log.error("Provided remote repo url does not match with locally available ones. Exiting...")
                sys.exit(FRECKLES_CONFIG_ERROR_EXIT_CODE)

    if result["default_vars"][DOTFILES_KEY].get(DOTFILES_REMOTE_KEY, False):
        result["runs"] = [
            {"frecks": {"checkout": {}}},
            {"frecks": {"install": {}, "stow": {}}}
        ]
    else:
        result["runs"] = [
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
@click.option('--hosts', help='comma-separated list of hosts (default: \'localhost\'), overrides config', multiple=True)
@click.option('--details', help='whether to print details of the results of the  operations that are executed, or not', default=False, is_flag=True)
def cli(ctx, config, hosts, details):

    config.load()

    if not config.config:
        config.config = {}

    augment_config(config, hosts, details)

    if ctx.invoked_subcommand is None:
        run(config)


def augment_config(config, hosts=None, details=False):

    if hosts:
        config.hosts = hosts
    else:
        config.hosts = FRECKLES_DEFAULT_HOSTS

    config.details = details

    config.freckles = Freckles(hosts=config.hosts, default_vars=config.config.get("default_vars", {}))
    config.runs = config.config.get("runs", {})


@cli.command()
@click.argument('config_file_url', required=False)
@pass_config
def run(config, config_file_url):

    if  config_file_url:

        url = expand_bootstrap_config_url(config_file_url)
        log.debug("Trying to download bootstrap config file: {}".format(url))
        txt = urllib.urlopen(url).read()

        if "404" in txt:
            url2 = expand_config_url(config_file_url)
            log.debug("Trying to download default config file: {}".format(url2))

            txt = urllib.urlopen(url2).read()
            if "404" in txt:
                log.error("Could not download config from '{}' or '{}'. Exiting...".format(url, url2))
                sys.exit(FRECKLES_CONFIG_ERROR_EXIT_CODE)
            else:
                url = url2

        temp_config = Config()
        temp_config.config.update(yaml.load(txt))

        log.info("Using configuration from: {}".format(url))

    else:
        temp_config = Config()
        if not config.config:
            temp = guess_local_default_config()
            if temp:
                temp_config.config = temp
                log.info("No configuration found or specified, using default values.")
            else:
                temp_config.config = {}
        else:
            temp_config.config = config.config
            log.info("Using local configuration: {}".format(config.config_file))

    if not temp_config.config:
        log.error("Empty configuration. Exiting...")
        sys.exit(FRECKLES_CONFIG_ERROR_EXIT_CODE)

    augment_config(temp_config, hosts=config.hosts, details=config.details)

    log.debug("Running initial freckles run with temporary config...")
    run(temp_config)


@cli.command()
@pass_config
def config(config):

    print(yaml.dump(config.config, default_flow_style=False))

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

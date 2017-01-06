# -*- coding: utf-8 -*-

import click
from freckles import Freckles, FRECKLES_DEFAULT_EXECUTION_BASE_DIR, FRECKLES_DEFAULT_EXECUTION_DIR_NAME
import pprint
import py
import yaml
import os
import json
from freckles_runner import FrecklesRunner

DEFAULT_INDENT = 2

class Config(object):

    def __init__(self, *args, **kwargs):
        self.config_dir = click.get_app_dir('freckles')
        self.config_file = py.path.local(self.config_dir).join('config.yml')
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
            self.config = {"build_base_dir": FRECKLES_DEFAULT_EXECUTION_BASE_DIR, "build_dir_name": FRECKLES_DEFAULT_EXECUTION_DIR_NAME, "dotfiles": [], "hosts": ['localhost']}

        self.config_file.ensure()
        with self.config_file.open('w') as f:
            yaml.dump(self.config, f, default_flow_style=False)

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
@click.option('--hosts', help='comma-separated list of hosts (default: \'localhost\'), overrides config', multiple=True)
@click.option('--dotfiles', help='base-path(s) for dotfile directories (can be used multiple times), overrides config', type=click.Path(exists=True, dir_okay=True, readable=True, resolve_path=True), multiple=True)
def cli(ctx, config, hosts, dotfiles):
    config.load()

    if not config.config:
        config.save()

    config.cli_hosts = hosts
    config.cli_dotfiles = dotfiles

    if config.cli_dotfiles:
        dotfiles = config.cli_dotfiles
    else:
        dotfiles = config.config["dotfiles"]

    if config.cli_hosts:
        hosts = config.cli_hosts
    else:
        hosts = config.config["hosts"]

    config.freckles = create_freckles(dotfiles, hosts)

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

def create_freckles(dotfile_dirs, hosts):

    inv_hosts = {}
    for host in hosts:
        if host == "localhost" or host == "127.0.0.1":
            inv_hosts[host] = {"ansible_connection": "local"}
        else:
            inv_hosts[host] = {}

    freckles = Freckles(dotfile_dirs, hosts=inv_hosts)
    return freckles


def run(config):

    runner = FrecklesRunner(config.freckles, config.get("build_base_dir"), config.get("build_dir_name"))


if __name__ == "__main__":
    cli()

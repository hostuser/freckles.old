#!/usr/bin/env python
# -*- coding: utf-8 -*-

import inspect
import os
import json
import yaml
import shutil
from collections import namedtuple
from tempfile import NamedTemporaryFile
from cookiecutter.main import cookiecutter
from constants import *
import subprocess
from utils import playbook_needs_sudo, create_playbook_dict, extract_roles, can_passwordless_sudo
import logging
import click
log = logging.getLogger("freckles")
DEFAULT_COOKIECUTTER_FRECKLES_PLAY_URL = "https://github.com/makkus/cookiecutter-freckles-play.git"

FRECKLES_DEVELOP_ROLE_PATH = os.environ.get("FRECKLES_DEVELOP", "")
FRECKLES_LOG_TOKEN = "FRECKLES: "

class FrecklesRunner(object):

    def __init__(self, freckles, current_run, clear_build_dir=False, update_roles=False, execution_base_dir=None, execution_dir_name=None, cookiecutter_freckles_play_url=DEFAULT_COOKIECUTTER_FRECKLES_PLAY_URL, details=False, hosts=None):

        self.task_result = {}

        if not hosts:
            hosts = FRECKLES_DEFAULT_HOSTS

        self.hosts = {}
        for host in hosts:
            if host == "localhost" or host == "127.0.0.1":
                self.hosts[host] = {"ansible_connection": "local"}
            else:
                self.hosts[host] = {}


        if not execution_base_dir:
            execution_base_dir = FRECKLES_DEFAULT_EXECUTION_BASE_DIR
        if not execution_dir_name:
            execution_dir_name = FRECKLES_DEFAULT_EXECUTION_DIR_NAME

        self.details = details
        self.execution_base_dir = execution_base_dir
        self.execution_dir_name = execution_dir_name
        self.execution_dir = os.path.join(execution_base_dir, execution_dir_name)

        log.debug("Build dir: {}".format(self.execution_dir))

        #TODO: exception handling
        if not os.path.exists(self.execution_base_dir):
            os.makedirs(self.execution_base_dir)
        if clear_build_dir and os.path.exists(self.execution_dir):
            log.debug("Clearing previous build dir...")
            shutil.rmtree(self.execution_dir)

        os.chdir(self.execution_base_dir)

        self.freckles = freckles
        self.current_run = current_run
        self.freckles_group_name = FRECKLES_DEFAULT_GROUP_NAME
        self.playbook_dir = os.path.join(self.execution_dir, FRECKLES_PLAYBOOK_DIR)
        self.playbook_file = os.path.join(self.playbook_dir, FRECKLES_PLAYBOOK_NAME)
        self.inventory_dir = os.path.join(self.execution_dir, FRECKLES_INVENTORY_DIR)
        self.execution_script_file = os.path.join(self.execution_dir, FRECKLES_EXECUTION_SCRIPT)
        runner_file = inspect.stack()[0][1]
        runner_folder = os.path.abspath(os.path.join(runner_file, os.pardir))
        self.callback_plugins_folder = os.path.join(runner_folder, "ansible", "callback_plugins")
        log.debug("Creating playbook items...")
        self.playbook_items = self.freckles.create_playbook_items(self.current_run)
        if not self.playbook_items:
            log.debug("No playbook items created, doing nothing in this run...")
            return
        log.debug("Playbooks created, {} playbook items created.".format(len(self.playbook_items)))

        passwordless_sudo = can_passwordless_sudo()
        if not passwordless_sudo and playbook_needs_sudo(self.playbook_items):
            log.debug("Some playbook items will need sudo, adding parameter execution pipeline...")
            self.freckles_ask_sudo = "--ask-become-pass"
        else:
            self.freckles_ask_sudo = ""

        self.roles = extract_roles(self.playbook_items)
        log.debug("Roles in use: {}".format(self.roles))
        if not os.path.exists(os.path.join(self.execution_dir)):
            cookiecutter_details = {
                "execution_dir": self.execution_dir_name,
                "freckles_group_name": self.freckles_group_name,
                "freckles_role_name": "ansible-freckles",
                "freckles_playbook_dir": self.playbook_dir,
                "freckles_playbook": self.playbook_file,
                "freckles_ask_sudo": self.freckles_ask_sudo,
                "freckles_develop_roles_path": FRECKLES_DEVELOP_ROLE_PATH,
                "freckles_ansible_roles": self.roles,
                "freckles_callback_plugins": self.callback_plugins_folder,
                "freckles_callback_plugin_name": FRECKLES_CALLBACK_PLUGIN_NAME
            }
            log.debug("Creating build environment from template...")
            log.debug("Using cookiecutter details: {}".format(cookiecutter_details))

            cookiecutter(cookiecutter_freckles_play_url, extra_context=cookiecutter_details, no_input=True)

        log.debug("Creating and writing inventory...")
        self.create_inventory_dir()

        log.debug("Creating and writing playbook...")
        playbook_dict = create_playbook_dict(self.playbook_items, self.freckles_group_name)
        with open(self.playbook_file, 'w') as f:
            f.write(yaml.safe_dump([playbook_dict], default_flow_style=False))

        # check if roles are already installed
        ext_role_path = os.path.join(self.execution_dir, "roles", "external")
        if update_roles or not os.path.exists(os.path.join(ext_role_path)):
            log.debug("Installing or updating roles in use...")
            res = subprocess.check_output([os.path.join(self.execution_dir, "extensions", "setup", "role_update.sh")])
            for line in res.splitlines():
                log.debug("Installing role: {}".format(line))

    def run(self):

        success = True
        if self.freckles_ask_sudo:
            log.info("Freckles needs sudo password for certain parts of the pipeline, please provide below:")
        proc = subprocess.Popen(self.execution_script_file, stdout=subprocess.PIPE, shell=True)

        total_tasks = (len(self.playbook_items))
        latest_id = 0
        for line in iter(proc.stdout.readline, ''):
            # log.debug(line)

            details = json.loads(line)
            freckles_id = int(details[FRECKLES_ID_KEY])
            changed = not freckles_id == latest_id

            if changed:
                if latest_id != 0:
                    if not self.log(freckles_id-1):
                        success = False

                latest_id = freckles_id
                # log title of task
                self.print_task_title(freckles_id)

            self.append_log(freckles_id, details)

        if latest_id != 0:
            if not self.log(latest_id):
                success = False

        return success

    def append_log(self, freckles_id, details):
        if not self.task_result.get(freckles_id, False):
            self.task_result[freckles_id] = []

        self.task_result[freckles_id].append(details)
        log.debug(details)

    def print_task_title(self, freckles_id):

        task_item = self.playbook_items[freckles_id]
        item_name = task_item[ITEM_NAME_KEY]
        role_name = task_item[ANSIBLE_ROLE_KEY]

        task_title = "- task {:02d}/{:02d}: {} '{}'".format(freckles_id, len(self.playbook_items), role_name, item_name)
        click.echo(task_title, nl=False)

    def log(self, freckles_id):

        failed = False
        task_item = self.playbook_items[freckles_id]
        output_details = self.task_result[freckles_id]

        output = self.freckles.handle_task_output(task_item, output_details)

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

    def create_inventory_dir(self):

        group_base_dir = os.path.join(self.inventory_dir, "group_vars")
        os.makedirs(group_base_dir)

        for host in self.hosts.keys():
            host_dir = os.path.join(self.inventory_dir, "host_vars", host)
            os.makedirs(host_dir)

            freckles_host_file = os.path.join(host_dir, "freckles.yml")
            with open(freckles_host_file, 'w') as f:
                f.write(yaml.safe_dump(self.hosts.get(host, {}), default_flow_style=False))

        inventory_file = os.path.join(self.inventory_dir, "inventory.ini")
        with open(inventory_file, 'w') as f:
            f.write("""[{}]

{}

""".format(self.freckles_group_name, "\n".join(self.hosts.keys())))

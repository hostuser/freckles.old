#!/usr/bin/env python
# -*- coding: utf-8 -*-

import inspect
import os
import json
import yaml
import copy
import shutil
from collections import namedtuple
from tempfile import NamedTemporaryFile
from cookiecutter.main import cookiecutter
from constants import *
import subprocess
from collections import OrderedDict
from utils import playbook_needs_sudo, create_playbook_dict, can_passwordless_sudo
import logging
import click
import pprint
from exceptions import FrecklesConfigError
log = logging.getLogger("freckles")
DEFAULT_COOKIECUTTER_FRECKLES_PLAY_URL = "https://github.com/makkus/cookiecutter-freckles-play.git"

FRECKLES_DEVELOP_ROLE_PATH = os.environ.get("FRECKLES_DEVELOP", "")
FRECKLES_LOG_TOKEN = "FRECKLES: "

FRECKLES_ANSIBLE_ROLE_TEMPLATE_URL = "https://github.com/makkus/ansible-role-template.git"


def extract_ansible_roles(playbook_items):
    """Extracts all ansible roles that will be used in a run.

    The result is used to download the roles automatically before the run starts.
    """

    roles = {}
    for item in playbook_items.values():
        item_roles = item.get(FRECK_RUNNER_KEY, {}).get(FRECK_ANSIBLE_RUNNER, {}).get(FRECK_ANSIBLE_ROLES_KEY, {})
        for role_name, role_url_or_dict in item_roles.iteritems():
            if isinstance(role_url_or_dict, basestring):
                roles[role_name] = role_url_or_dict

    return roles

def create_custom_roles(playbook_items, role_base_path):
    """Creates all custom ansible roles that are needed in a run.

    If one of the roles in one of the playbook items is a list instead of a string, it is assumed that it is a list of task descriptions (see: XXX) and a custom role is generated dynamically.

    If that is the case, the role_name will not be included in the result, since that role doesn't need to be downloaded, and the internal role path that contains the role is already included in the ansible path.
    """

    for item in playbook_items.values():
        item_roles = item.get(FRECK_RUNNER_KEY, {}).get(FRECK_ANSIBLE_RUNNER, {}).get(FRECK_ANSIBLE_ROLES_KEY, {})
        for role_name, role_url_or_dict in item_roles.iteritems():
            if not isinstance(role_url_or_dict, basestring) and isinstance(role_url_or_dict, (list, tuple)):
                create_custom_role(role_base_path, role_name, role_url_or_dict)


def create_custom_role(role_base_path, role_name, tasks, defaults={}):
    """Creates a ansible role in the specified location.

    Args:
        role_path (str): the base path where the role will be created
        role_name (str): the name of the role
        tasks (list): a list of dicts that describe each of the tasks that should go into the role
        defaults (dict): a dictionary of the default variables for this role
    """

    # need to convert tasks dictionary so that it works with the template
    tasks_dict = OrderedDict()
    for task in tasks:
        task_id_element = task["task"]
        if len(task_id_element) != 1:
            raise FrecklesConfigError("Task element in task description has more than one entries, not valid: {}".format(task_id_element))

        task_id = task_id_element.keys()[0]
        task_vars = task_id_element[task_id]
        name = task["name"]
        type = task["type"]

        tasks_dict[task_id] = { type: task_vars }

    current_dir = os.getcwd()
    os.chdir(role_base_path)
    role_dict = { "role_name": role_name, "tasks": tasks_dict, "defaults": defaults }
    pprint.pprint(role_dict)
    cookiecutter(FRECKLES_ANSIBLE_ROLE_TEMPLATE_URL, extra_context=role_dict, no_input=True)
    os.chdir(current_dir)

class FrecklesRunner(object):
    """ Runner that takes a freckles object, creates an ansible playbook and associated environment, then executes it.
    """

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

        # check that every item has a role specified. Also apply tags if necessary
        for item in self.playbook_items.values():
            if not item.get(FRECK_RUNNER_KEY, {}).get(FRECK_ANSIBLE_RUNNER, {}).get(FRECK_ANSIBLE_ROLE_KEY, False):
                roles = item.get(FRECK_RUNNER_KEY, {}).get(FRECK_ANSIBLE_RUNNER, {}).get(FRECK_ANSIBLE_ROLES_KEY, {})
                if len(roles) != 1:
                    raise FrecklesConfigError("Item '{}' does not have a role associated with it, and more than one role in freck config. This is probably a bug, please report to the freck developer.".format(item[FRECK_ITEM_NAME_KEY]), FRECK_ANSIBLE_ROLE_KEY, roles)
                item[FRECK_ANSIBLE_ROLE_KEY] = roles.keys()[0]
            else:
                item[FRECK_ANSIBLE_ROLE_KEY] = item[FRECK_RUNNER_KEY][FRECK_ANSIBLE_RUNNER][FRECK_ANSIBLE_ROLE_KEY]


        if not self.playbook_items:
            log.debug("No playbook items created, doing nothing in this run...")
            return
        log.debug("Playbooks created, {} playbook items created.".format(len(self.playbook_items)))

        needs_sudo = playbook_needs_sudo(self.playbook_items)
        passwordless_sudo = can_passwordless_sudo()
        if not passwordless_sudo and needs_sudo:
            log.debug("Some playbook items will need sudo, adding parameter execution pipeline...")
            self.freckles_ask_sudo = "--ask-become-pass"
        else:
            self.freckles_ask_sudo = ""

        self.roles = extract_ansible_roles(self.playbook_items)

        log.debug("Roles in use: {}".format(self.roles))
        if not os.path.exists(os.path.join(self.execution_dir)):
            cookiecutter_details = {
                "execution_dir": self.execution_dir_name,
                "freckles_group_name": self.freckles_group_name,
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

        create_custom_roles(self.playbook_items, os.path.join(self.execution_dir, "roles", "internal"))

        # create custom roles

        log.debug("Creating and writing inventory...")
        self.create_inventory_dir()

        log.debug("Creating and writing playbook...")
        playbook_dict = create_playbook_dict(self.playbook_items, self.freckles_group_name)
        with open(self.playbook_file, 'w') as f:
            f.write(yaml.safe_dump([playbook_dict], default_flow_style=False))

        # check if roles are already installed
        ext_role_path = os.path.join(self.execution_dir, "roles", "external")
        if self.roles and (update_roles or not os.path.exists(os.path.join(ext_role_path))):
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
            freckles_id = int(details.get(FRECK_ID_KEY, latest_id))
            if freckles_id <= 0:
                if latest_id == 0:
                    freckles_id = 1
                else:
                    freckles_id = latest_id
            changed = not freckles_id == latest_id

            if changed:
                if latest_id != 0:
                    if not self.log(freckles_id-1):
                        success = False

                latest_id = freckles_id
                # log title of task
                self.print_task_title(freckles_id)

            # print(freckles_id)
            # print(details)
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
        item_name = task_item[FRECK_ITEM_NAME_KEY]
        role_name = task_item[FRECK_ANSIBLE_ROLE_KEY]

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

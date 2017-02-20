#!/usr/bin/env python
# -*- coding: utf-8 -*-

from sets import Set
import inspect
import os
import json
import yaml
import copy
import shutil
from collections import namedtuple
from tempfile import NamedTemporaryFile
from cookiecutter.main import cookiecutter
from freckles.constants import *
import subprocess
from collections import OrderedDict
from freckles.utils import playbook_needs_sudo, can_passwordless_sudo
import logging
import click
import pprint
from freckles.exceptions import FrecklesConfigError
import shutil
log = logging.getLogger("freckles")

FRECKLES_ANSIBLE_ROLE_TEMPLATE_URL = "https://github.com/makkus/ansible-role-template.git"

ANSIBLE_RUNNER_PREFIX = "ANSIBLE"
FRECK_ANSIBLE_ROLES_KEY = "{}_ROLES".format(ANSIBLE_RUNNER_PREFIX)
FRECK_ANSIBLE_ROLE_KEY = "{}_ROLE".format(ANSIBLE_RUNNER_PREFIX)

ROLE_TO_USE_KEY = "role_to_use"
ROLE_ROLES_KEY = "roles"

ANSIBLE_TASK_TYPE = "ansible_task"
ANSIBLE_ROLE_TYPE = "ansible_role"

FRECKLES_DEFAULT_GROUP_NAME = "freckles"

FRECKLES_DEVELOP_ROLE_PATH = os.environ.get("FRECKLES_DEVELOP", "")
FRECKLES_LOG_TOKEN = "FRECKLES: "

def create_inventory_dir(hosts, inventory_dir, group_name=FRECKLES_DEFAULT_GROUP_NAME):

        group_base_dir = os.path.join(inventory_dir, "group_vars")
        os.makedirs(group_base_dir)

        for host in hosts.keys():
            host_dir = os.path.join(inventory_dir, "host_vars", host)
            os.makedirs(host_dir)

            freckles_host_file = os.path.join(host_dir, "freckles.yml")
            with open(freckles_host_file, 'w') as f:
                f.write(yaml.safe_dump(hosts.get(host, {}), default_flow_style=False))

        inventory_file = os.path.join(inventory_dir, "inventory.ini")
        with open(inventory_file, 'w') as f:
            f.write("""[{}]

{}

""".format(group_name, "\n".join(hosts.keys())))

def cleanup_playbook_items(playbook_items):

    result = OrderedDict()
    for item_nr, item in playbook_items.iteritems():
        i = {}
        for key, value in item.iteritems():
            if key.startswith(ANSIBLE_RUNNER_PREFIX):
                continue
            elif key != INT_FRECK_ID_KEY and key.startswith("freck_"):
                continue

            i[key] = value

        result[item_nr] = i

    return result

def create_playbook_dict(playbook_items, host_group=FRECKLES_DEFAULT_GROUP_NAME):
    """Assembles the dictionary to create the playbook from."""
    temp_root = {}
    temp_root["hosts"] = host_group
    temp_root["gather_facts"] = True

    cleaned = cleanup_playbook_items(playbook_items)
    # cleaned = playbook_items

    temp_root["roles"] = cleaned.values()

    return temp_root

def extract_ansible_roles(playbook_items):
    """Extracts all ansible roles that will be used in a run.

    The result is used to download the roles automatically before the run starts.
    """

    roles = {}
    for item in playbook_items.values():
        item_roles = item.get(FRECK_ANSIBLE_ROLES_KEY, {})
        for role_name, role_url_or_dict in item_roles.iteritems():
            if isinstance(role_url_or_dict, basestring):
                if not role_url_or_dict.startswith("frkl:"):
                    roles[role_name] = role_url_or_dict

    return roles

def copy_internal_roles(playbook_items, role_base_path):
    """Copies included roles to playbook environment.

    If the url of the role starts with 'frkl:', it is assumed it is an internally supported role, and will be copied to the 'internal' role path in the playbook environment.
    """

    role_urls = Set()
    for item in playbook_items.values():
        item_roles = item.get(FRECK_ANSIBLE_ROLES_KEY, {})
        for role_name, role_url_or_dict in item_roles.iteritems():
            if isinstance(role_url_or_dict, basestring):
                if role_url_or_dict.startswith("frkl:"):
                    role_urls.add((role_name, role_url_or_dict))

    for role_internal_name in role_urls:
        frkl_role_name = role_internal_name[1][5:]
        role_path = os.path.join(os.path.dirname(__file__), "..", "ansible", "external_roles", frkl_role_name)
        dest = os.path.join(role_base_path, role_internal_name[0])
        log.debug("Copying internal roles: {} -> {}".format(role_path, dest))
        shutil.copytree(role_path, dest)


def create_custom_roles(playbook_items, role_base_path):
    """Creates all custom ansible roles that are needed in a run.

    If one of the roles in one of the playbook items is a list instead of a string, it is assumed that it is a list of task descriptions (see: XXX) and a custom role is generated dynamically.

    If that is the case, the role_name will not be included in the result, since that role doesn't need to be downloaded, and the internal role path that contains the role is already included in the ansible path.
    """

    for item in playbook_items.values():
        item_roles = item.get(FRECK_ANSIBLE_ROLES_KEY, {})
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
    # tasks_dict = OrderedDict()
    tasks_dict = {}
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
    role_local_path = os.path.join(os.path.dirname(__file__), "..", "cookiecutter", "external_templates", "ansible-role-template")

    cookiecutter(role_local_path, extra_context=role_dict, no_input=True)
    os.chdir(current_dir)


class AnsibleRunner(object):
    """ Runner that executes a series of frecks that use ansible as a backend execution engine.

    This is the default runner, and there might never be a different type. Just abstracted it because it was easy to do at this stage, and it might prove useful later on.
    """

    def __init__(self, frecks):
        self.frecks = frecks

    def set_items(self, items):
        self.items = items

    def set_callback(self, callback):
        self.callback = callback

    def get_freck(self, freck_name, freck_type, freck_configs):

        if not freck_type == FRECK_DEFAULT_TYPE:
            if freck_type == ANSIBLE_TASK_TYPE:
                return self.frecks.get("task")
            elif freck_type == ANSIBLE_ROLE_TYPE:
                return self.frecks.get("role")
            else:
                raise FrecklesConfigError("Freck type '{}' not supported for ansible runner.".format(freck_type), FRECK_TYPE_KEY, freck_type)
        else:
            freck = self.frecks.get(freck_name, False)
            if not freck:
                last_config = freck_configs[-1]
                if last_config.get(ROLE_ROLES_KEY, False):
                        roles = last_config[ROLE_ROLES_KEY].keys()
                        if freck_name in roles:
                                return self.frecks.get("role")

                        return False

            return freck

    def prepare_run(self):

        self.create_playbook_environment()


    def create_playbook_environment(self, execution_base_dir=None, execution_dir_name=None, hosts=None):
        """
        Creates a directory containing the playbook to execute, all the required roles (downloaded if necessary), and a script to kick of the run.
        """

        # for now, only localhost is supported. haven't thought about how easy/hard it'd be to also support remote hosts
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

        self.execution_base_dir = execution_base_dir
        self.execution_dir_name = execution_dir_name
        self.execution_dir = os.path.join(execution_base_dir, execution_dir_name)

        log.debug("Run directory: {}".format(self.execution_dir))

        #TODO: exception handling
        if not os.path.exists(self.execution_base_dir):
            os.makedirs(self.execution_base_dir)
        if os.path.exists(self.execution_dir):
            log.debug("Clearing previous build dir...")
            shutil.rmtree(self.execution_dir)

        os.chdir(self.execution_base_dir)

        self.freckles_group_name = FRECKLES_DEFAULT_GROUP_NAME
        self.playbook_dir = os.path.join(self.execution_dir, FRECKLES_PLAYBOOK_DIR)
        self.playbook_file = os.path.join(self.playbook_dir, FRECKLES_PLAYBOOK_NAME)
        self.inventory_dir = os.path.join(self.execution_dir, FRECKLES_INVENTORY_DIR)
        self.execution_script_file = os.path.join(self.execution_dir, FRECKLES_EXECUTION_SCRIPT)
        runner_file = inspect.stack()[0][1]
        runner_folder = os.path.abspath(os.path.join(runner_file, os.pardir))
        self.callback_plugins_folder = os.path.join(runner_folder, "..",  "ansible", "callback_plugins")

        # check that every item has a role specified. Also apply tags if necessary
        for item in self.items.values():
            if not item.get(FRECK_ANSIBLE_ROLE_KEY, False):
                roles = item.get(FRECK_ANSIBLE_ROLES_KEY, {})
                if len(roles) != 1:
                    raise FrecklesConfigError("Item '{}' does not have a role associated with it, and more than one role in freck config. This is probably a bug, please report to the freck developer.".format(item[INT_FRECK_ITEM_NAME_KEY]), FRECK_ANSIBLE_ROLE_KEY, roles)

                item[FRECK_ANSIBLE_ROLE_KEY] = roles.keys()[0]

            # copy role key to ansible-usable 'role' variable
            item["role"] = item[FRECK_ANSIBLE_ROLE_KEY]
            item[FRECK_TASK_DESC] = item[FRECK_ANSIBLE_ROLE_KEY]

        needs_sudo = playbook_needs_sudo(self.items)
        passwordless_sudo = can_passwordless_sudo()
        if not passwordless_sudo and needs_sudo:
            log.debug("Some playbook items will need sudo, adding parameter to execution pipeline...")
            self.freckles_ask_sudo = "--ask-become-pass"
        else:
            self.freckles_ask_sudo = ""

        self.roles = extract_ansible_roles(self.items)
        log.debug("Roles in use: {}".format(self.roles))

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

        play_template_path = os.path.join(os.path.dirname(__file__), "..", "cookiecutter", "external_templates", "cookiecutter-freckles-play")

        cookiecutter(play_template_path, extra_context=cookiecutter_details, no_input=True)

        # create custom & internal roles
        create_custom_roles(self.items, os.path.join(self.execution_dir, "roles", "internal"))
        copy_internal_roles(self.items, os.path.join(self.execution_dir, "roles", "internal"))

        log.debug("Creating and writing inventory...")
        create_inventory_dir(self.hosts, self.inventory_dir)

        log.debug("Creating and writing playbook...")
        playbook_dict = create_playbook_dict(self.items, self.freckles_group_name)
        with open(self.playbook_file, 'w') as f:
            f.write(yaml.safe_dump([playbook_dict], default_flow_style=False))

        # ext_role_path = os.path.join(self.execution_dir, "roles", "external")
        if self.roles:
            click.echo("Downloading and installing external roles...")
            res = subprocess.check_output([os.path.join(self.execution_dir, "extensions", "setup", "role_update.sh")])
            for line in res.splitlines():
                log.debug("Installing role: {}".format(line))


    def run(self):

        success = True
        if self.freckles_ask_sudo:
            log.info("Freckles needs sudo password for certain parts of the pipeline, please provide below:")
        proc = subprocess.Popen(self.execution_script_file, stdout=subprocess.PIPE, shell=True)

        total_tasks = (len(self.items))
        self.callback.set_total_tasks(total_tasks)
        for line in iter(proc.stdout.readline, ''):
            details = json.loads(line)
            freck_id = int(details.get(INT_FRECK_ID_KEY))
            self.callback.log(freck_id, details)

        self.callback.log(freck_id, RUN_FINISHED)

        # TODO: check success?
        return success



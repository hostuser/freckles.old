#!/usr/bin/env python
# -*- coding: utf-8 -*-

import copy
import inspect
import json
import logging
import os
import pprint
import shutil
import subprocess
import sys
from collections import OrderedDict, namedtuple
from tempfile import NamedTemporaryFile

import click
import yaml

from cookiecutter.main import cookiecutter
from freckles.constants import *
from freckles.exceptions import FrecklesConfigError
from freckles.freckles_runner import FrecklesRunner
from freckles.utils import (can_passwordless_sudo, check_schema, dict_merge,
                            playbook_needs_sudo)
from sets import Set
from voluptuous import Any, Schema

log = logging.getLogger("freckles")

FRECKLES_ANSIBLE_ROLE_TEMPLATE_URL = "https://github.com/makkus/ansible-role-template.git"



ROLE_TO_USE_KEY = "role_to_use"
ROLE_ROLES_KEY = "roles"

ANSIBLE_TASK_TYPE = "ansible-task"
ANSIBLE_ROLE_TYPE = "ansible-role"
ANSIBLE_FRECK_TYPE = "ansible-freck"
ANSIBLE_ROLE_PROCESSED = "role_processed"
TASK_FREE_FORM_KEY = "free_form"

TASK_BECOME_KEY = "become"
TASK_DEFAULT_BECOME = False
TASK_TEMPLATE_KEYS = "task_template_keys"

FRECKLES_DEFAULT_GROUP_NAME = "freckles"

FRECKLES_DEVELOP_ROLE_PATH = os.environ.get("FRECKLES_DEVELOP", "")
FRECKLES_LOG_TOKEN = "FRECKLES: "

FRECK_META_TYPE_KEY = "type"
FRECK_META_ROLE_NAME_KEY = "role_name"
FRECK_META_ROLES_KEY = "roles"
FRECK_META_ROLE_KEY = "role"

FRECK_META_TASKS_KEY = "tasks"
FRECK_META_ROLE_DICT_KEY = "role_dict"

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

""".format(group_name, "\n".join("{}     {}".format(hosts.keys(), ansible_python_interpreter='/usr/bin/env python')))

def create_playbook_dict(playbook_items, host_group=FRECKLES_DEFAULT_GROUP_NAME):
    """Assembles the dictionary to create the playbook from."""

    temp_root = {}
    temp_root["hosts"] = host_group
    temp_root["gather_facts"] = True

    roles = []
    for p in playbook_items:
            role_dict = copy.deepcopy(p[FRECK_META_ROLE_DICT_KEY])
            id = p[FRECK_ID_KEY]
            role_dict[FRECK_ID_KEY] = id
            become = p.get(FRECK_SUDO_KEY, FRECK_DEFAULT_SUDO)
            role_dict[FRECK_SUDO_KEY] = become
            vars = p[FRECK_VARS_KEY]
            dict_merge(role_dict, vars)
            roles.append(role_dict)

    temp_root["roles"] = roles

    return temp_root

def get_roles_library_paths(playbook_items):
        """Extracs all roles that are copied or downloaded, and returns a list of paths to their library folders.

        This is useful to use modules included in roles directly."""

        result = []
        for item in playbook_items:
                item_roles = item.get(FRECK_META_ROLES_KEY, {})
                for role_name, role_url_or_dict in item_roles.iteritems():
                        if isinstance(role_url_or_dict, basestring):
                                if role_url_or_dict.startswith("frkl:"):
                                        # means internal
                                        result.append("../roles/internal/{}/library".format(role_name))
                                else:
                                        result.append("../roles/external/{}/library".format(role_name))

        return result



def extract_ansible_roles(playbook_items):
    """Extracts all ansible roles that will be used in a run.

    The result is used to download the roles automatically before the run starts.
    """

    roles = {}
    for item in playbook_items:
        item_roles = item.get(FRECK_META_ROLES_KEY, {})
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
    for item in playbook_items:
        item_roles = item.get(FRECK_META_ROLES_KEY, {})
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

def internal_role_exists():

        role_base_path = os.path.join(os.path.dirname(__file__), "..", "ansible", "external_roles")


def create_custom_roles(playbook_items, role_base_path):
    """Creates all custom ansible roles that are needed in a run.

    If one of the roles in one of the playbook items is a list instead of a string, it is assumed that it is a list of task descriptions (see: XXX) and a custom role is generated dynamically.

    If that is the case, the role_name will not be included in the result, since that role doesn't need to be downloaded, and the internal role path that contains the role is already included in the ansible path.

    Args:
        playbook_items (list): all the items that are to be executed
        role_base_path (str): base directory where the role should be created
    """

    for item in playbook_items:
        item_roles = item.get(FRECK_META_ROLES_KEY, {})
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
    # tasks_dict = {}
    for task in tasks:
        task_id_element = task["task"]
        if len(task_id_element["vars"]) != 1:
            raise FrecklesConfigError("Task element in task description has more than one entries, not valid: {}".format(task_id_element), "task", task)

        task_id = task_id_element["vars"].keys()[0]
        task_vars = task_id_element["vars"][task_id]
        become = task_id_element["become"]

        name = task["name"]
        task_type = task["type"]

        tasks_dict[task_id] = {task_type: {"vars": task_vars, "become": become}}

    current_dir = os.getcwd()
    os.chdir(role_base_path)

    rearranged_tasks = {}
    for task, task_detail in tasks_dict.iteritems():
            ansible_module = task_detail.keys()[0]
            become = task_detail[ansible_module][TASK_BECOME_KEY]
            if TASK_FREE_FORM_KEY in task_detail[ansible_module]["vars"]:
                task_detail[ansible_module]["vars"].remove(TASK_FREE_FORM_KEY)
                new_dict = {"module_name": ansible_module, "args": task_detail[ansible_module]["vars"], "become": become, "free_form": True}
                rearranged_tasks[task] = new_dict
            else:
                ansible_module = task_detail.keys()[0]
                rearranged_tasks[task] = {"module_name": ansible_module, "args": task_detail[ansible_module]["vars"], "become": become, "free_form": False}

    role_dict = {"role_name": role_name, "tasks": rearranged_tasks, "defaults": defaults}
    role_local_path = os.path.join(os.path.dirname(__file__), "..", "cookiecutter", "external_templates", "ansible-role-template")

    cookiecutter(role_local_path, extra_context=role_dict, no_input=True)
    os.chdir(current_dir)

ANSIBLE_FRECK_SCHEMA = Schema({
        FRECK_NAME_KEY: basestring,
        FRECK_DESC_KEY: basestring,
        TASK_NAME_KEY: basestring,
        FRECK_SUDO_KEY: bool,
        FRECK_VARS_KEY: dict,
        FRECK_ITEM_NAME_KEY: basestring,
        FRECK_META_ROLE_DICT_KEY: dict,
        FRECK_META_TASKS_KEY: dict,
        FRECK_INDEX_KEY: int,
        FRECK_RUNNER_KEY: basestring,
        FRECK_NEW_RUN_AFTER_THIS_KEY: bool,
        FRECK_PRIORITY_KEY: int,
        FRECK_ID_KEY: int,
        TASK_TEMPLATE_KEYS: Any(Set, list),
        FRECK_META_ROLES_KEY: dict,
        FRECK_META_ROLE_KEY: basestring,
        ANSIBLE_ROLE_PROCESSED: bool,
        UNIQUE_TASK_ID_KEY: basestring
})

class AnsibleRunner(FrecklesRunner):
    """ Runner that executes a series of frecks that use ansible as a backend execution engine.

    This is the default runner, and there might never be a different type. Just abstracted it because it was easy to do at this stage, and it might prove useful later on.
    """

    def __init__(self, items, callback):
        # TODO: validate items
        for item in items:
                check_schema(item, ANSIBLE_FRECK_SCHEMA)

        self.items = items

        self.callback = callback
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

        # CHECK TASKS AND CREATE ROLES freck_type == ANSIBLE_TASK_TYPE:
        for item in self.items:
                if item.get(FRECK_META_TASKS_KEY, False):
                        item.setdefault(FRECK_META_ROLES_KEY, {}).update(item[FRECK_META_TASKS_KEY])

        needs_sudo = playbook_needs_sudo(self.items)
        passwordless_sudo = can_passwordless_sudo()
        if not passwordless_sudo and needs_sudo:
            log.debug("Some playbook items will need sudo, adding parameter to execution pipeline...")
            self.freckles_ask_sudo = "--ask-become-pass"
        else:
            self.freckles_ask_sudo = ""

        self.roles = extract_ansible_roles(self.items)

        self.freckles_library_paths = get_roles_library_paths(self.items)
        self.freckles_library_path_string = "./library:" + ":".join(self.freckles_library_paths)
        log.debug("Roles in use: {}".format(self.roles))

        cookiecutter_details = {
                "execution_dir": self.execution_dir_name,
                "freckles_group_name": self.freckles_group_name,
                "freckles_playbook_dir": self.playbook_dir,
                "freckles_playbook": self.playbook_file,
                "freckles_ask_sudo": self.freckles_ask_sudo,
                "freckles_library_path": self.freckles_library_path_string,
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
                log.debug("Installing role: {}".format(line.encode('utf8')))


    def run(self):

        success = True
        if self.freckles_ask_sudo:
            click.echo("\nLooks like we need a sudo password for some parts of the pipeline, this might interrupt the execution process, depending on how sudo is configured on this machine. Please provide your password below if necessary.\n")
        proc = subprocess.Popen(self.execution_script_file, stdout=subprocess.PIPE, shell=True)

        total_tasks = (len(self.items))
        self.callback.set_total_tasks(total_tasks)

        for line in iter(proc.stdout.readline, ''):
            details = json.loads(line)
            freck_id = int(details.get(FRECK_ID_KEY))
            self.callback.log(freck_id, details)

        self.callback.log(freck_id, RUN_FINISHED)

        # TODO: check success?
        return success

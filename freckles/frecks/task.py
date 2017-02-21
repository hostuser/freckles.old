# -*- coding: utf-8 -*-
import logging
import sys
import copy
from voluptuous import Schema, ALLOW_EXTRA, Any, Required
from freckles.exceptions import FrecklesConfigError
from freckles import Freck
from freckles.constants import *
from freckles.runners.ansible_runner import FRECK_ANSIBLE_ROLE_KEY, FRECK_ANSIBLE_ROLES_KEY
from freckles.utils import parse_dotfiles_item, get_pkg_mgr_from_path, create_dotfiles_dict, get_pkg_mgr_from_marker_file, get_pkg_mgr_sudo, dict_merge, create_apps_dict
import copy
from freckles.runners.ansible_runner import ANSIBLE_TASK_TYPE

log = logging.getLogger("freckles")

TASKS_NAME_KEY = "tasks"

GENERATED_ROLE_ID_COUNTER = 0
GENERATED_ROLE_PREFIX = "freckles_custom_role_"

def create_run_using_freck_name(freck_name, freck_desc, task_vars):

    global GENERATED_ROLE_ID_COUNTER

    task = {"name": freck_desc, "type": freck_name, "task": {"run_{0:04d}_task_{1:06d}".format(GENERATED_ROLE_ID_COUNTER, 1): copy.deepcopy(task_vars)}}
    GENERATED_ROLE_ID_COUNTER = GENERATED_ROLE_ID_COUNTER + 1

    return [task]

def create_run_generic(config):

    global GENERATED_ROLE_ID_COUNTER

    tasks = config.get(TASKS_NAME_KEY)
    if isinstance(tasks, dict):
        raise FrecklesConfigError("Value for 'tasks' key is dict, needs list: {}".format(tasks), "tasks", tasks)
    elif isinstance(tasks, (list, tuple)):
        # means we'll create a bunch of frecks
        role_tasks = []
        task_number = 1
        for task in tasks:
            if len(task) > 2:
                raise FrecklesConfigError("Value for tasks key has more than 2 keys, can only have 'name' and the name of the task: {}".format(task), "tasks", task)
            name = task["name"]
            task_type = next(key for key in task.keys() if key != "name")
            task_vars = task[task_type]
            task = {"name": name, "type": task_type, "task": {"run_{0:04d}_task_{1:06d}".format(GENERATED_ROLE_ID_COUNTER, task_number): task_vars}}
            GENERATED_ROLE_ID_COUNTER = GENERATED_ROLE_ID_COUNTER + 1
            task_number = task_number + 1
            role_tasks.append(task)
        return role_tasks
    else:
        raise FrecklesConfigError("Can't figure out type of 'tasks' value: {}". format(tasks))

class Task(Freck):

    def calculate_freck_config(self, freck_configs):
        """Overwriting the parent class method because we need access to the 'pure' task vars."""

        self.task_vars = freck_configs[-1]
        freck_vars = {}
        for config in freck_configs:
            dict_merge(freck_vars, config)

        freck_config = copy.deepcopy(FRECK_DEFAULT_CONFIG)
        dict_merge(freck_config, copy.deepcopy(self.default_freck_config()))
        dict_merge(freck_config, copy.deepcopy(freck_vars))

        return freck_config


    def create_run_items(self, freck_name, freck_type, freck_desc, config):

        if freck_type == ANSIBLE_TASK_TYPE and config.get(TASKS_NAME_KEY, False):
            raise FrecklesConfigError("Task freck has both type and {} variable set, this is invalid".format(TASKS_NAME_KEY), TASKS_NAME_KEY, config[TASKS_NAME_KEY])
        elif freck_type == ANSIBLE_TASK_TYPE:
            role_tasks = create_run_using_freck_name(freck_name, freck_desc, self.task_vars)
        elif config.get(TASKS_NAME_KEY, False):
            role_tasks = create_run_generic(config)
        else:
            raise FrecklesConfigError("Can't determine which task to run, neither {} nor {} defined".format(ANSIBLE_TASK_TYPE, TASKS_NAME_KEY), TASKS_NAME_KEY, None)

        generated_role_name = "{}{}".format(GENERATED_ROLE_PREFIX, GENERATED_ROLE_ID_COUNTER)
        config[FRECK_ANSIBLE_ROLE_KEY] = generated_role_name
        config[FRECK_ANSIBLE_ROLES_KEY][generated_role_name] = role_tasks

        return [config]


    def default_freck_config(self):
        return {
            FRECK_SUDO_KEY: False,
            FRECK_RUNNER_KEY: FRECKLES_ANSIBLE_RUNNER,
            FRECK_ANSIBLE_ROLES_KEY: {}
        }

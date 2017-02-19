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

log = logging.getLogger("freckles")

TASKS_NAME_KEY = "tasks"

GENERATED_ROLE_ID_COUNTER = 1
GENERATED_ROLE_PREFIX = "freckles_custom_role_"

class Task(Freck):

    def create_run_items(self, config):

        global GENERATED_ROLE_ID_COUNTER

        tasks = config[TASKS_NAME_KEY]

        if isinstance(tasks, dict):
            raise FrecklesConfigError("Value for 'tasks' key is dict, needs list: {}".format(tasks))
        elif isinstance(tasks, (list, tuple)):
            # means we'll create a bunch of frecks
            role_tasks = []
            task_number = 1
            for task in tasks:
                if len(task) > 2:
                    raise FrecklesConfigError("Value for tasks key has more than 2 keys, can only have 'name' and the name of the task: {}".format(task))

                name = task["name"]

                task_type = next(key for key in task.keys() if key != "name")
                task_vars = task[task_type]

                task = {"name": name, "type": task_type, "task": {"run_{0:04d}_task_{1:06d}".format(GENERATED_ROLE_ID_COUNTER, task_number): task_vars}}
                task_number = task_number + 1
                role_tasks.append(task)

            generated_role_name = "{}{}".format(GENERATED_ROLE_PREFIX, GENERATED_ROLE_ID_COUNTER)
            GENERATED_ROLE_ID_COUNTER = GENERATED_ROLE_ID_COUNTER + 1
            config[FRECK_RUNNER_KEY][FRECK_ANSIBLE_RUNNER][FRECK_ANSIBLE_ROLE_KEY] = generated_role_name
            config[FRECK_RUNNER_KEY][FRECK_ANSIBLE_RUNNER][FRECK_ANSIBLE_ROLES_KEY][generated_role_name] = role_tasks

            return [config]
        else:
            raise FrecklesConfigError("Can't figure out type of 'tasks' value: {}". format(tasks))

    def default_freck_config(self):
        return {
            FRECK_SUDO_KEY: False,
            FRECK_RUNNER_KEY: FRECKLES_ANSIBLE_RUNNER,
        }

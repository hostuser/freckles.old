# -*- coding: utf-8 -*-
import logging

from voluptuous import Schema, ALLOW_EXTRA, Required

from freckles import Freck
from freckles.constants import *
from freckles.runners.ansible_runner import FRECK_ANSIBLE_ROLE_KEY, FRECK_ANSIBLE_ROLES_KEY
from freckles.utils import parse_dotfiles_item, create_dotfiles_dict

log = logging.getLogger("freckles")

PRECENDENCE_ERROR_STRING = "Possible precedence issue with control flow operator at"
DEFAULT_STOW_SUDO = False
DEFAULT_STOW_TARGET_BASE_DIR = os.path.expanduser("~/")
STOW_TARGET_BASE_DIR_KEY = "stow_target_dir"
FRECKLES_DEFAULT_STOW_ROLE_NAME = "stow-pkg"
FRECKLES_DEFAULT_STOW_ROLE_URL = "frkl:ansible-stow"

class Stow(Freck):

    def get_config_schema(self):
        s = Schema({
            Required(DOTFILES_KEY): list
        }, extra=ALLOW_EXTRA)

        return s

    def pre_process_config(self, config):

        dotfiles = parse_dotfiles_item(config[DOTFILES_KEY])
        # existing_dotfiles = check_dotfile_items(dotfiles)
        # if not existing_dotfiles:
            # return []

        apps = create_dotfiles_dict(dotfiles, default_details=config)
        for app, value in apps.iteritems():
            value["item_name"] = value[INT_FRECK_ITEM_NAME_KEY]

        return apps.values()

    def create_run_items(self, freck_name, freck_type, freck_desc, config):

        return [config]

    def handle_task_output(self, task, output_details):

        output = super(Stow, self).handle_task_output(task, output_details)
        stdout = []
        stderr = []

        if output["state"] == FRECKLES_STATE_FAILED:
            for output in output_details:
                for line in output["result"]["msg"].split("\n"):
                    stderr.append(line)
        else:
            # flatten stderr sublist
            lines = [item for sublist in [entry.split("\n") for entry in output["stderr"]] for item in sublist]

            for line in lines:
                if not line or line.startswith(PRECENDENCE_ERROR_STRING):
                    continue
                elif line.startswith("LINK") or line.startswith("UNLINK"):
                    stdout.append(line)
                else:
                    stderr.append(line)

        output[FRECKLES_STDOUT_KEY] = stdout
        output[FRECKLES_STDERR_KEY] = stderr

        return output

    def default_freck_config(self):

        return {
            DOTFILES_KEY: [DEFAULT_DOTFILE_DIR],
            FRECK_SUDO_KEY: DEFAULT_STOW_SUDO,
            STOW_TARGET_BASE_DIR_KEY: DEFAULT_STOW_TARGET_BASE_DIR,
            FRECK_PRIORITY_KEY: FRECK_DEFAULT_PRIORITY+100,
            FRECK_RUNNER_KEY: FRECKLES_ANSIBLE_RUNNER,
            FRECK_ANSIBLE_ROLES_KEY: {FRECKLES_DEFAULT_STOW_ROLE_NAME: FRECKLES_DEFAULT_STOW_ROLE_URL},
            FRECK_ANSIBLE_ROLE_KEY: FRECKLES_DEFAULT_STOW_ROLE_NAME
        }

# -*- coding: utf-8 -*-
from freckles import Freck
from freckles.utils import parse_dotfiles_item, get_pkg_mgr_from_path, create_dotfiles_dict
import os
from freckles.constants import *
import sys

import logging
log = logging.getLogger(__name__)

PRECENDENCE_ERROR_STRING = "Possible precedence issue with control flow operator at"

class Stow(Freck):

    def create_playbook_items(self, config):

        dotfiles = parse_dotfiles_item(config[DOTFILES_KEY])

        apps = create_dotfiles_dict(dotfiles, default_details=config)

        return apps.values()

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
            FRECK_SUDO_KEY: DEFAULT_STOW_SUDO,
            ANSIBLE_ROLE_NAME_KEY: FRECKLES_DEFAULT_STOW_ROLE_NAME,
            ANSIBLE_ROLE_URL_KEY: FRECKLES_DEFAULT_STOW_ROLE_URL,
            DOTFILES_KEY: DEFAULT_DOTFILES,
            STOW_TARGET_BASE_DIR_KEY: DEFAULT_STOW_TARGET_BASE_DIR
        }

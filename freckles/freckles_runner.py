#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import yaml
import shutil
from collections import namedtuple
from tempfile import NamedTemporaryFile
from cookiecutter.main import cookiecutter
from constants import FRECKLES_PLAYBOOK_DIR, FRECKLES_INSTALL_PLAYBOOK_NAME, FRECKLES_STOW_PLAYBOOK_NAME, FRECKLES_INVENTORY_DIR, FRECKLES_EXECUTION_SCRIPT, FRECKLES_DEFAULT_INSTALL_ROLE_NAME, FRECKLES_DEFAULT_STOW_ROLE_NAME, FRECKLES_DEFAULT_EXECUTION_BASE_DIR, FRECKLES_DEFAULT_EXECUTION_DIR_NAME, FRECKLES_DEFAULT_ANSIBLE_FRECKLES_ROLE_URL, FRECKLES_DEFAULT_ANSIBLE_STOW_ROLE_URL

DEFAULT_COOKIECUTTER_FRECKLES_PLAY_URL = "https://github.com/makkus/cookiecutter-freckles-play.git"

FRECKLES_DEVELOP_ROLE_PATH = os.environ.get("FRECKLES_DEVELOP", "")

class FrecklesRunner(object):

    def __init__(self, freckles, execution_base_dir=None, execution_dir_name=None, cookiecutter_freckles_play_url=DEFAULT_COOKIECUTTER_FRECKLES_PLAY_URL, freckles_ansible_freckles_role_url=FRECKLES_DEFAULT_ANSIBLE_FRECKLES_ROLE_URL, freckles_ansible_stow_role_url=FRECKLES_DEFAULT_ANSIBLE_STOW_ROLE_URL):

        if not execution_base_dir:
            execution_base_dir = FRECKLES_DEFAULT_EXECUTION_BASE_DIR
        if not execution_dir_name:
            execution_dir_name = FRECKLES_DEFAULT_EXECUTION_DIR_NAME

        self.execution_base_dir = execution_base_dir
        self.execution_dir_name = execution_dir_name
        self.execution_dir = os.path.join(execution_base_dir, execution_dir_name)

        #TODO: exception handling
        if not os.path.exists(self.execution_base_dir):
            os.makedirs(self.execution_base_dir)
        if os.path.exists(self.execution_dir):
            shutil.rmtree(self.execution_dir)

        os.chdir(self.execution_base_dir)

        self.freckles = freckles
        self.playbook_dir = os.path.join(self.execution_dir, FRECKLES_PLAYBOOK_DIR)
        self.install_playbook_file = os.path.join(self.playbook_dir, FRECKLES_INSTALL_PLAYBOOK_NAME)
        self.stow_playbook_file = os.path.join(self.playbook_dir, FRECKLES_STOW_PLAYBOOK_NAME)
        self.inventory_dir = os.path.join(self.execution_dir, FRECKLES_INVENTORY_DIR)
        self.execution_script_file = os.path.join(self.execution_dir, FRECKLES_PLAYBOOK_DIR, FRECKLES_EXECUTION_SCRIPT)

        if self.freckles.needs_sudo():
            freckles_ask_sudo = "--ask-become-pass"
        else:
            freckles_ask_sudo = ""

        cookiecutter_details = {
            "execution_dir": self.execution_dir_name,
            "freckles_group_name": "freckles",
            "freckles_role_name": "ansible-freckles",
            "freckles_playbook_dir": self.playbook_dir,
            "freckles_install_playbook": self.install_playbook_file,
            "freckles_stow_playbook": self.stow_playbook_file,
            "freckles_ansible_freckles_role": freckles_ansible_freckles_role_url,
            "freckles_ansible_stow_role": freckles_ansible_stow_role_url,
            "freckles_ask_sudo": freckles_ask_sudo,
            "freckles_develop_roles_path": FRECKLES_DEVELOP_ROLE_PATH
        }
        cookiecutter(cookiecutter_freckles_play_url, extra_context=cookiecutter_details, no_input=True)


        self.freckles.create_playbook(self.playbook_dir, FRECKLES_INSTALL_PLAYBOOK_NAME, FRECKLES_DEFAULT_INSTALL_ROLE_NAME)
        self.freckles.create_playbook(self.playbook_dir, FRECKLES_STOW_PLAYBOOK_NAME, FRECKLES_DEFAULT_STOW_ROLE_NAME)
        self.freckles.create_inventory_dir(self.inventory_dir)

    def run(self):
        pass

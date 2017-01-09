#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import yaml
import shutil
from collections import namedtuple
from tempfile import NamedTemporaryFile
from cookiecutter.main import cookiecutter
from constants import *
import subprocess
from utils import playbook_needs_sudo, create_playbook_dict, extract_roles

DEFAULT_COOKIECUTTER_FRECKLES_PLAY_URL = "https://github.com/makkus/cookiecutter-freckles-play.git"

FRECKLES_DEVELOP_ROLE_PATH = os.environ.get("FRECKLES_DEVELOP", "")

class FrecklesRunner(object):

    def __init__(self, freckles, clear_build_dir=False, update_roles=False, execution_base_dir=None, execution_dir_name=None, cookiecutter_freckles_play_url=DEFAULT_COOKIECUTTER_FRECKLES_PLAY_URL):

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
        if clear_build_dir and os.path.exists(self.execution_dir):
            shutil.rmtree(self.execution_dir)

        os.chdir(self.execution_base_dir)

        self.freckles = freckles
        self.freckles_group_name = FRECKLES_DEFAULT_GROUP_NAME
        self.playbook_dir = os.path.join(self.execution_dir, FRECKLES_PLAYBOOK_DIR)
        self.playbook_file = os.path.join(self.playbook_dir, FRECKLES_PLAYBOOK_NAME)
        self.inventory_dir = os.path.join(self.execution_dir, FRECKLES_INVENTORY_DIR)
        self.execution_script_file = os.path.join(self.execution_dir, FRECKLES_EXECUTION_SCRIPT)

        playbook_items = self.freckles.create_playbook_items()

        if playbook_needs_sudo(playbook_items):
            freckles_ask_sudo = "--ask-become-pass"
        else:
            freckles_ask_sudo = ""

        self.roles = extract_roles(playbook_items)
        if not os.path.exists(os.path.join(self.execution_dir)):
            cookiecutter_details = {
                "execution_dir": self.execution_dir_name,
                "freckles_group_name": self.freckles_group_name,
                "freckles_role_name": "ansible-freckles",
                "freckles_playbook_dir": self.playbook_dir,
                "freckles_playbook": self.playbook_file,
                "freckles_ask_sudo": freckles_ask_sudo,
                "freckles_develop_roles_path": FRECKLES_DEVELOP_ROLE_PATH,
                "freckles_ansible_roles": self.roles
            }
            cookiecutter(cookiecutter_freckles_play_url, extra_context=cookiecutter_details, no_input=True)

        # needs_sudo = playbook_needs_sudo(playbook_items)
        playbook_dict = create_playbook_dict(playbook_items, self.freckles_group_name)

        self.create_inventory_dir()
        with open(self.playbook_file, 'w') as f:
            f.write(yaml.safe_dump([playbook_dict], default_flow_style=False))

        # check if roles are already installed
        ext_role_path = os.path.join(self.execution_dir, "roles", "external")
        if update_roles or not os.path.exists(os.path.join(ext_role_path)):
            res = subprocess.check_output([os.path.join(self.execution_dir, "extensions", "setup", "role_update.sh")])
            for line in res.splitlines():
                print line

    def run(self):

        res = subprocess.check_output(self.execution_script_file)
        for line in res.splitlines():
            print line


    def create_inventory_dir(self):

        group_base_dir = os.path.join(self.inventory_dir, "group_vars")

        os.makedirs(group_base_dir)

        for host in self.freckles.hosts.keys():
            host_dir = os.path.join(self.inventory_dir, "host_vars", host)
            os.makedirs(host_dir)

            freckles_host_file = os.path.join(host_dir, "freckles.yml")
            with open(freckles_host_file, 'w') as f:
                f.write(yaml.safe_dump(self.freckles.hosts.get(host, {}), default_flow_style=False))

        inventory_file = os.path.join(self.inventory_dir, "inventory.ini")
        with open(inventory_file, 'w') as f:
            f.write("""[{}]

{}

""".format(self.freckles_group_name, "\n".join(self.freckles.hosts.keys())))

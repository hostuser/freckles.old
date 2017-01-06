# -*- coding: utf-8 -*-

import os
import yaml
import pprint
import json
from freckles_runner import FrecklesRunner
from utils import get_pkg_mgr_from_path

KEYWORDS = ["pkgs", "dotfiles"]

from constants import *

class Freckles(object):

    def __init__(self, base_dirs, group_name=FRECKLES_DEFAULT_GROUP_NAME, default_pkg_state=FRECKLES_DEFAULT_PACKAGE_STATE, default_pkg_sudo=FRECKLES_DEFAULT_PACKAGE_SUDO, default_stow_target_base_dir=FRECKLES_DEFAULT_STOW_TARGET_BASE_DIR, hosts={u"localhost": {u"ansible_connection": u"local"}}):

        self.group_name = group_name
        if isinstance(base_dirs, str):
            self.base_dirs = [base_dirs]
        else:
            self.base_dirs = base_dirs

        self.hosts = hosts

        self.apps = {}

        for dir in self.base_dirs:
            for item in os.listdir(dir):
                if not item.startswith(".") and os.path.isdir(os.path.join(dir, item)):
                    # defaults
                    dotfile_dir = os.path.join(dir, item)
                    self.apps[item] = {"app_name": item, "dotfiles": dotfile_dir, "pkgs": {"default": [item]}, "pkg_state": default_pkg_state, "pkg_sudo": default_pkg_sudo, "stow": True, "dotfiles_base_dir": dir, "target_base_dir": default_stow_target_base_dir}
                    # if the path of the dotfile dir contains either 'deb', 'rpm', or 'nix', use this as the default package manager. Can still be overwritten by metadata file
                    pkg_mgr = get_pkg_mgr_from_path(dotfile_dir)
                    if pkg_mgr:
                        self.apps[item]["pkg_mgr"] = pkg_mgr

                    freckles_metadata_file = os.path.join(dotfile_dir, FRECKLES_METADATA_FILENAME)
                    if os.path.exists(freckles_metadata_file):
                        stream = open(freckles_metadata_file, 'r')
                        temp = yaml.load(stream)
                        self.apps[item].update(temp)

                    # check if 'pkgs' key is a dict, if not, use its value and put it into the 'default' key
                    if not type(self.apps[item]["pkgs"]) == dict:
                        temp = self.apps[item]["pkgs"]
                        self.apps[item]["pkgs"] = {}
                        self.apps[item]["pkgs"]["default"] = temp

                    # check if an 'default' pkgs key exists, if not, use the package name
                    if not self.apps[item].get("pkgs").get("default", False):
                        self.apps[item]["pkgs"]["default"] = [item]


    def list_all(self):
        pprint.pprint(self.apps)

    def list(self, package_managers="apt", tags=None):
        print yaml.dump(self.apps, default_flow_style=False)

    def create_inventory_yml(self):

        groups = {self.group_name: {"vars": {"freckles": self.apps}, "hosts": [host for host in self.hosts.keys()]}}
        hosts = self.hosts

        inv = Inventory({"groups": groups, "hosts": hosts})
        return inv.list()

    def create_inventory_dir(self, base_dir):

        group_base_dir = os.path.join(base_dir, "group_vars")

        os.makedirs(group_base_dir)

        # for group, details in self.apps.iteritems():

            # group_dir = os.path.join(group_base_dir, group)
            # os.makedirs(group_dir)
            # freckles_group_yml_file = os.path.join(group_dir, "{}.yml".format(FRECKLES_GROUP_DETAILS_FILENAME))

            # with open(freckles_group_yml_file, 'w') as f:
                # f.write(yaml.safe_dump({"freckles_{}_{}".format(group, key): value for (key, value) in details.iteritems()}, default_flow_style=False))

        for host in self.hosts.keys():
            host_dir = os.path.join(base_dir, "host_vars", host)
            os.makedirs(host_dir)

            freckles_host_file = os.path.join(host_dir, "freckles.yml")
            with open(freckles_host_file, 'w') as f:
                f.write(yaml.safe_dump(self.hosts.get(host, {}), default_flow_style=False))

        inventory_file = os.path.join(base_dir, "inventory.ini")
        with open(inventory_file, 'w') as f:
            f.write("""[{}]
{}

""".format(FRECKLES_DEFAULT_GROUP_NAME, "\n".join(self.hosts.keys())))

    def needs_sudo(self):

        for group, details in self.apps.iteritems():
            if details["pkg_sudo"]:
                return True

        return False

    def create_playbook(self, playbook_dir, playbook_file_name, ansible_role_name):

        playbook_file = os.path.join(playbook_dir, playbook_file_name)

        temp_root = {}
        temp_root["hosts"] = FRECKLES_DEFAULT_GROUP_NAME
        temp_root["gather_facts"] = True
        temp_roles = []
        for group, details in self.apps.iteritems():
            temp_details = {}
            temp_details["role"] = ansible_role_name
            temp_details.update({"{}_{}".format(self.group_name, key): value for (key, value) in details.iteritems()})

            temp_roles.append(temp_details)

        temp_root["roles"] = temp_roles

        with open(playbook_file, 'w') as f:
            f.write(yaml.safe_dump([temp_root], default_flow_style=False))

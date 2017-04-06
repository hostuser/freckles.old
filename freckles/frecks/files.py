
# -*- coding: utf-8 -*-
import copy
import logging
import os

from freckles import Freck
from freckles.constants import *
from freckles.frkl import DEFAULT_FRKL_KEY_MARKER
from freckles.runners.ansible_runner import (FRECK_META_ROLE_KEY,
                                             FRECK_META_ROLES_KEY)
from task import AbstractTask

log = logging.getLogger("freckles")
FILES_TO_DELETE_KEY = "files-to-delete"

DIRECTORY_TO_ENSURE_KEY = "folders"

FRECKLES_DEFAULT_DELETE_ROLE_NAME = "delete"
FRECKLES_DEFAULT_DELETE_ROLE_URL = "frkl:ansible-delete"


class EnsureDirectory(AbstractTask):

    def get_config_schema(self):
        return False

    def process_leaf(self, leaf, supported_runners=[FRECKLES_DEFAULT_RUNNER], debug=False):

        config = leaf[FRECK_VARS_KEY]
        meta = leaf[FRECK_META_KEY]

        create_dir_key = DIRECTORY_TO_ENSURE_KEY
        if DIRECTORY_TO_ENSURE_KEY not in config.keys():
            create_dir_key = DEFAULT_FRKL_KEY_MARKER

        if create_dir_key not in config.keys():
            return

        if isinstance(config[create_dir_key], basestring):
            config[create_dir_key] = [config[create_dir_key]]

        result = []
        for f in config.pop(create_dir_key, []):
            if f.startswith("~"):
                file = os.path.expanduser(f)
            elif os.path.isabs(f):
                file = f
            else:
                file = os.path.join(os.path.expanduser("~"), f)

            new_meta = {}
            new_meta[FRECK_VARS_KEY] = {"path": file, "state": "directory"}
            new_meta[FRECK_DESC_KEY] = "ensure folder exists"
            new_meta[FRECK_ITEM_NAME_KEY] = file
            new_meta[FRECK_SUDO_KEY] = False
            new_meta[TASK_NAME_KEY] = "file"

            result.append(new_meta)

        return (FRECKLES_ANSIBLE_RUNNER, result)

    def get_task_config(self, freck_meta, config):

        task_name = "file"
        task_desc = "ensure folder exists"
        task_item = config["path"]

        return {
            TASK_MODULE_NAME_KEY: task_name,
            TASK_DESC_KEY: task_desc,
            TASK_ITEM_NAME_KEY: task_item
        }


    def default_freck_config(self):

        return {
        }


class Delete(AbstractTask):

    def get_config_schema(self):
        return False


    def process_leaf(self, leaf, supported_runners=[FRECKLES_DEFAULT_RUNNER], debug=False):

        config = leaf[FRECK_VARS_KEY]
        meta = leaf[FRECK_META_KEY]

        delete_key = FILES_TO_DELETE_KEY
        if FILES_TO_DELETE_KEY not in config.keys():
            delete_key = DEFAULT_FRKL_KEY_MARKER

        if delete_key not in config.keys():
            return

        if isinstance(config[delete_key], basestring):
            config[delete_key] = [config[delete_key]]


        result = []
        for f in config.pop(delete_key, []):
            if f.startswith("~"):
                file = os.path.expanduser(f)
            elif os.path.isabs(f):
                file = f
            else:
                file = os.path.join(os.path.expanduser("~"), f)

            new_meta = {}
            new_meta[FRECK_VARS_KEY] = {"path": file, "state": "absent"}
            new_meta[FRECK_DESC_KEY] = "delete file"
            new_meta[FRECK_ITEM_NAME_KEY] = file
            new_meta[FRECK_SUDO_KEY] = False
            new_meta[TASK_NAME_KEY] = "file"

            result.append(new_meta)

        return (FRECKLES_ANSIBLE_RUNNER, result)


    def get_task_config(self, freck_meta, config):

        task_name = "file"
        task_desc = "delete"
        task_item = config["path"]

        return {
            TASK_MODULE_NAME_KEY: task_name,
            TASK_DESC_KEY: task_desc,
            TASK_ITEM_NAME_KEY: task_item
        }


    def default_freck_config(self):

        return {
        }

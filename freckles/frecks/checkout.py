# -*- coding: utf-8 -*-
import copy
import logging
import os
import pprint
import sys

from freckles import Freck
from freckles.constants import *
from freckles.exceptions import FrecklesConfigError
from freckles.runners.ansible_runner import (FRECK_META_ROLE_KEY,
                                             FRECK_META_ROLES_KEY,
                                             TASK_FREE_FORM_KEY,
                                             TASK_TEMPLATE_KEYS)
from freckles.utils import (create_dotfiles_dict, get_pkg_mgr_from_path,
                            parse_dotfiles_item)
from role import AbstractRole
from task import AbstractTask
from voluptuous import ALLOW_EXTRA, Any, Schema

log = logging.getLogger("freckles")

FRECKLES_DEFAULT_CHECKOUT_ROLE_NAME = "checkout"
FRECKLES_DEFAULT_CHECKOUT_ROLE_URL = "frkl:ansible-checkout"

GIT_VALID_KEYS = ["accept_hostkey", "bare", "clone", "depth", "executable", "force", "key_file", "recursive", "reference", "refspec", "repo", "ssh_opts", "track_submodules", "umask", "update", "verify_commit", "version"]

REPO_KEY = "repo"
TARGET_KEY = "target"

class CheckoutGitRepo(AbstractRole):

    UNIQUE_TASK_ID_PREFIX = "sync_git_repo"

    def get_config_schema(self):

        s = Schema({
            Required(REPO_KEY): basestring,
            Required(TARGET_KEY): basestring
        })

        return s

    def get_unique_task_id(self, freck_meta):

        return "{}_{}_{}".format(CheckoutGitRepo.UNIQUE_TASK_ID_PREFIX, freck_meta[FRECK_VARS_KEY][REPO_KEY], freck_meta[FRECK_VARS_KEY][TARGET_KEY])

    def get_role(self, freck_meta):
        return "git_sync_repo"

    def get_desc(self, freck_meta):
        return "sync git repo"

    def get_item_name(self, freck_meta):
        return freck_meta[FRECK_VARS_KEY][REPO_KEY]

    def get_sudo(self, freck_meta):
        return False

    def get_additional_roles(self, freck_meta):
        return {"git_sync_repo": "frkl:ansible-git-sync-repo"}

class CheckoutDotfiles(AbstractTask):

    def get_config_schema(self):
        return False

    def process_leaf(self, leaf, supported_runners=[FRECKLES_DEFAULT_RUNNER], debug=False):

        config = leaf[FRECK_VARS_KEY]
        meta = leaf[FRECK_META_KEY]

        dotfiles = parse_dotfiles_item(config[DOTFILES_KEY])

        if len(dotfiles) == 0:
            return (FRECKLES_DEFAULT_RUNNER, [])

        dirs_used = []
        result = []
        for df in dotfiles:
            base_dir = df.get(DOTFILES_BASE_KEY, DEFAULT_DOTFILE_DIR)
            if base_dir in dirs_used:
                log.error("Basedir '{}' used more than once, this is not possible. Exiting...")
                sys.exit(FRECKLES_CONFIG_ERROR_EXIT_CODE)

            paths = df.get(DOTFILES_PATHS_KEY, [""])
            remote = df.get(DOTFILES_REMOTE_KEY, "")

            if not remote:
                continue

            meta_new = {}
            meta_new[FRECK_DESC_KEY] = "checkout dotfiles"
            meta_new[FRECK_ITEM_NAME_KEY] = "{} -> {}".format(remote, base_dir)
            meta_new[FRECK_VARS_KEY] = {"repo": remote, "dest": base_dir}
            meta_new[FRECK_SUDO_KEY] = False
            meta_new[TASK_NAME_KEY] = "git"
            meta_new[TASK_TEMPLATE_KEYS] = GIT_VALID_KEYS
            meta_new[FRECK_NEW_RUN_AFTER_THIS_KEY] = True
            result.append(meta_new)

        return (FRECKLES_ANSIBLE_RUNNER, result)

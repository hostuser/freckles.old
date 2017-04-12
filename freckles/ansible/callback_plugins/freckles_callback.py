from __future__ import absolute_import, division, print_function

import datetime
import decimal
import json
import pprint
import uuid

import ansible
from ansible.executor.task_result import TaskResult
from ansible.plugins.callback import CallbackBase

__metaclass__ = type

class CallbackModule(CallbackBase):
    """
    Forward task, play and result objects to freckles.
    """
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'stdout'
    CALLBACK_NAME = 'freckles_callback'
    CALLBACK_NEEDS_WHITELIST = False

    def __init__(self, *args, **kwargs):
        super(CallbackModule, self).__init__(*args, **kwargs)
        self.task = None
        self.play = None

    def get_task_detail(self, detail_key):

        if not self.task:
            return False
        temp = self.task.serialize()
        for level in detail_key.split("."):
            temp = temp.get(level, {})

        return temp

    def get_freck_id(self):

        # pprint.pprint(self.task.serialize())

        id = self.get_task_detail("role._role_params.freck_id")
        if id:
            return id

        parents = self.get_task_detail("role._parents")
        if  parents:
            for p in parents:
                if "freck_id" in p["_role_params"].keys():

                    return p["_role_params"]["freck_id"]

        return -1

    def print_output(self, category, result):


        output = {}
        output["state"] = category
        output["freck_id"] = self.get_freck_id()

        # if output["freck_id"] == -1 and not category == "failed":
            # return

        action = self.get_task_detail("action")
        if not action:
            action = "n/a"
        output["action"] = action
        output["ignore_errors"] = self.get_task_detail("ignore_errors")
        task_name = self.get_task_detail("name")
        if not task_name:
            task_name = "n/a"
        output["task_name"] = task_name
        # output["task"] = self.task.serialize()
        # output["play"] = self.play.serialize()
        if category == "play_start" or category == "task_start":
            output["result"] = {}
        else:
            output["result"] = result._result

        print(json.dumps(output))

    def v2_runner_on_ok(self, result, **kwargs):

        self.print_output("ok", result)

    def v2_runner_on_failed(self, result, **kwargs):

        self.print_output("failed", result)

    def v2_runner_on_unreachable(self, result, **kwargs):

        self.print_output("unreachable", result)

    def v2_runner_on_skipped(self, result, **kwargs):

        self.print_output("skipped", result)

    def v2_playbook_on_play_start(self, play):
        self.play = play
        self.print_output("play_start", None)

    def v2_playbook_on_task_start(self, task, is_conditional):
        self.task = task
        self.print_output("task_start", None)

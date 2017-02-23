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

        temp = self.task.serialize()
        for level in detail_key.split("."):
            temp = temp.get(level, {})

        return temp

    def print_output(self, category, result):

        output = {}
        output["state"] = category
        output["freck_id"] = self.get_task_detail("role._role_params.freck_id")
        if  not output["freck_id"]:
            output["freck_id"] = -1
        if not output.get("freck_id", False) and not category == "failed":
            return

        output["action"] = self.task.serialize().get("action", "n/a")
        output["task_name"] = self.get_task_detail("name")
        # output["task"] = self.task.serialize()
        # output["play"] = self.play.serialize()
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

    def v2_playbook_on_task_start(self, task, is_conditional):
        self.task = task

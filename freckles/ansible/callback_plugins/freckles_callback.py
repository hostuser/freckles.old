from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.plugins.callback import CallbackBase
from ansible.executor.task_result import TaskResult
import pprint
import json
import datetime
import uuid
import decimal
import ansible


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
        output["freckles_id"] = self.get_task_detail("role._role_params.freckles_id")
        if not output.get("freckles_id", False):
            return

        output["action"] = self.task.serialize().get("action", "n/a")
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

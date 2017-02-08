# -*- coding: utf-8 -*-

from click.exceptions import ClickException
from constants import *
from click._compat import PY2, filename_to_ui, get_text_stderr

class FrecklesRunError(ClickException):
    """An Error signaling a run has failed. This usually aborts all further processing.

    Args:
        message (str): Message to be printed to the user.
        run (dict): Dict containing run configuration.

    Attributes:
        message (str): Message to be printed to the user.
        run (dict): Dict containing run configuration.

    """
    exit_code = FRECKLES_EXECUTION_ERROR_EXIT_CODE

    def __init__(self, message, run):
        ClickException.__init__(self, message)
        self.run = run


class FrecklesConfigError(ClickException):
    """An Error signaling a configuration issue.

    Args:
        message (str): Message to be printed to the user
        config_key: the config option that was misconfigured
        config_value: the config value that is invalid
    """
    exit_code = FRECKLES_CONFIG_ERROR_EXIT_CODE

    def __init__(self, message, config_key, config_value):
        ClickException.__init__(self, message)
        self.config_key = config_key
        self.config_value = config_value

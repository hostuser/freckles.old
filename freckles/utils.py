# -*- coding: utf-8 -*-
from os import sep

DEB_MATCH = "{}{}{}".format(sep, 'deb', sep)
RPM_MATCH = "{}{}{}".format(sep, 'rpm', sep)
NIX_MATCH = "{}{}{}".format(sep, 'nix', sep)
NO_INSTALL_MATCH = "{}{}{}".format(sep, "no_install", sep)

def get_pkg_mgr_from_path(path):

    if NIX_MATCH in path:
        return 'nix'
    elif DEB_MATCH in path:
        return 'deb'
    elif RPM_MATCH in path:
        return 'rpm'
    elif NO_INSTALL_MATCH in path:
        return 'no_install'
    else:
        return False

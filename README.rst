===============================
Freckles
===============================


.. image:: https://img.shields.io/pypi/v/freckles.svg
        :target: https://pypi.python.org/pypi/freckles

.. image:: https://img.shields.io/travis/makkus/freckles.svg
        :target: https://travis-ci.org/makkus/freckles

.. image:: https://readthedocs.org/projects/freckles/badge/?version=latest
        :target: https://freckles.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status

.. image:: https://pyup.io/repos/github/makkus/freckles/shield.svg
     :target: https://pyup.io/repos/github/makkus/freckles/
     :alt: Updates

A dotfile manager

Quickstart
----------

Freckles needs 2 things:

 - *a dotfile repository* -> to have something to work on
 - *curl* -> for bootstrapping (well, technically it also needs *bash*)

At the moment (and it'd be super-cool if that changed sometime in the future), the easiest way to install *freckles* is to bootstrap it (`more details <XXX>`_) using curl and bash:

.. code-block:: console

   $ curl -L https://get.frkl.io | bash -s -- run gh:makkus/dotfiles-example



Documentation: https://freckles.readthedocs.io.

Features
--------

* bootstrap & first run wrapped in one command
* simple, opinionated default configuration, but extensible if necessary
* optional support for (Linux) systems where you don't have root/sudo access via the `nix package manager <https://nixos.org/nix/>`_ or `conda <https://conda.io/docs>`_.


Freckles is free software under the GNU General Public License v3





Credits
---------

This package was created using, amongst others:

- _Cookiecutter
- _ansible-nix

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _ansible-nix: from: https://github.com/AdamFrey/nix-ansible

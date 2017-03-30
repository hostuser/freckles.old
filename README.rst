===================================================
freckles
===================================================

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


*a cute dotfile manager, all over the place*

*freckles* tries to make it easy to record and replicate the configuration and setup of your working environment (or parts thereof). It's built on top of ansible_, and is meant to be used on your local machine, not as much for configuring remote machines. It can be easily used to setup an environment in VMs (for example using Vagrant), or containers.

Documentation: https://freckles.readthedocs.io.

Quickstart
----------

For its most basic usecase, *freckles* needs 2 things:

 - *a dotfile repository* -> to have something to work on
 - *curl* (or *wget*) -> for bootstrapping (well, technically it also needs *bash*)

At the moment (and that might change in the future), the easiest way to install *freckles* is to bootstrap it (`more details <XXX>`_) using curl and bash:

.. code-block:: console

   $ curl -L https://get.frkl.io | bash -s -- run gh:makkus/freckles-quickstart/freckles/frkl.yml



Features
--------

* bootstrap & first run wrapped in one command
* simple, opinionated default configuration, but extensible if necessary
* optional support for (Linux) systems where you don't have root/sudo access via the `nix package manager <https://nixos.org/nix/>`_ or `conda <https://conda.io/docs>`_.


Freckles is free software under the GNU General Public License v3





Credits
---------

This package was created using, amongst others:

- Cookiecutter_
- ansible-nix_

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _ansible-nix: from: https://github.com/AdamFrey/nix-ansible
.. _ansible: https://ansible.com

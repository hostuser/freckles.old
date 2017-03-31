===================================================
Overview
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

*freckles* tries to make it easy to record and replicate the configuration and setup of your working environment (or parts thereof). It's built on top of ansible_, and is meant to be used on your local machine, not as much for configuring remote machines. It can also be used to easily setup an environment in VMs (for example using Vagrant), or containers, potentially sharing the configuration you use on your workstation.

*freckles* is written in Python, and built on top of ansible_.

Documentation: https://freckles.readthedocs.io.

Features
--------

* one-line setup of a new environment, including freckles bootstrap
* supports Linux & MacOS X
* share the same configuration for your Linux and MacOS workstation as well as Vagrant machines, containers, etc.
* support for systems where you don't have root/sudo access via the nix_ package manager or conda_ (or if you just think it's a good idea to use one/any of them)
* direct support for ansible_ modules and roles

Quickstart
----------

For its most basic use-case -- which is installing and configuring packages --, *freckles* needs 3 things:

 - a *configuration file*
 - a *dotfile repository* -> to have something to work on
 - *curl* (or *wget*) -> for bootstrapping (well, technically it also needs *bash*)

At the moment (and that might change in the future), the easiest way to install *freckles* is to bootstrap it (`more details <XXX>`_) using curl and bash. The bootstrap process can also already execute the first *freckles* run, which makes it possible to setup a machine with one line in your shell:

.. code-block:: console

   $ curl -L https://get.frkl.io | bash -s -- run gh:makkus/freckles/examples/quickstart.yml

This executes a simple config that looks like:

.. code-block:: yaml

  vars:
    dotfiles:
      - base_dir: ~/dotfiles-quickstart
        remote: https://github.com/makkus/freckles-quickstart.git

  tasks:
    - checkout-dotfiles
    - install:
        use_dotfiles: true
        packages:
          - htop
          - fortunes:
              pkgs:
                apt:
                  - fortunes
                  - fortunes-off
                  - fortunes-mario
                yum:
                  - fortune-mod
                homebrew:
                  - fortune
    - stow
    - file:
        path: ~/.backups/zile
        state: directory


What this does:

 - checks out the repository of dotfile(s) at `https://github.com/makkus/freckles-quickstart.git <https://github.com/makkus/freckles-quickstart>`_
 - installs all the applications/packages that are configured in that repo (only the emacs-like editor ``zile`` in this case)
 - also installs a few other packages that don't require configuration (``htop``, ``fortunes``, ``fortunes-off``, ``fortunes-mario``)
 - `stows <https://www.gnu.org/software/stow/>`_ all the dotfiles in the above repository into the users home directory (again, only for *zile* in this case)
 - creates a folder ``$HOME/.backups/zile`` if it doesn't exist already (needed because it is configured in the .zile file in the repo we checked out)

To read how all that works in more detail, please read the full documentation at XXX

You don't like executing random scripts on the internet? Yeah, me neither. Read here: XXX.

Supported platforms
-------------------

Currently tested and supported
++++++++++++++++++++++++++++++

- Debian

  - Jessie
  - TBD

- Ubuntu

  - 16.04
  - 16.10


Planned / Partially supported
+++++++++++++++++++++++++++++

- MacOS X
- Windows 10 (Ubuntu on Windows)


License
-------

Freckles is free software under the GNU General Public License v3.


Credits
---------

This package was created using, amongst others:

- ansible_
- Cookiecutter_
- nix_
- conda_
- ansible-nix_

.. _ansible: https://ansible.com
.. _nix: https://nixos.org/nix/
.. _conda: https://conda.io
.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _ansible-nix: from: https://github.com/AdamFrey/nix-ansible

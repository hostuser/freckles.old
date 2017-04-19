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


*a cute dotfile manager; all over the place*

At its heart, *freckles* is a dotfile manager. You point it to the configuration files of the applications you use, and it makes sure to replicate those configurations across your machines, virtual or not. It also can, if you want it to, do more than that. For example, it can install all the packages you generally use and/or ensure certain folders exists.


*freckles* tries to make it easy to record and replicate the configuration and setup of your working environment (or parts thereof). It's built on top of ansible_, and is meant to be used on your local machine, not as much for configuring remote machines.

It can also be used to easily setup an environment in VMs (for example using Vagrant), or containers, potentially sharing the configuration you use on your workstation, or a configuration for a setup to develop on a project, or whatever else you can think of.

*freckles* is written in Python, and GPL v3 licensed

Documentation: https://freckles.readthedocs.io.

Features
--------

* one-line setup of a new environment, including freckles bootstrap
* minimal and (hopefully) intuitive config file format, using ``yaml`` syntax
* supports Linux & MacOS X (and probably the Ubuntu subsystem on Windows 10)
* share the same configuration for your Linux and MacOS workstation as well as Vagrant machines, containers, etc.
* support for systems where you don't have root/sudo access via the nix_ package manager or conda_ (or if you just think it's a good idea to use any of them)
* direct support for all ansible_ modules and roles

What, ...why?
-------------

I re-installed a new (or recently bricked) laptop or VM or container this one time too often, and I was annoyed that there is no real easy and quick way to re-create my working environment in those fresh environments, without having to write shell-scripts that sooner or later turn out unmaintainable and are fairly unflexible to begin with. Now, of course, that's what configuration management tools are for, and I do quite like ansible_ and have a bit of experience with it. What I don't like is how one usually needs a set of configuration files to describe a setup, even for simple use-cases like setting up a single, local machine. And I didn't want to install `ansible` itself manually every time before I can run my playbooks and roles. Basically, I wanted a thing that allows me to run one line of code, pointing to one configuration file, and after a while I have the same setup as I have on my other machines.

This is what `freckles` now is, sorta. As a result of my tendency to over-engineer everything in my way along with me having a bit of time on my hands -- it now can do a few other things which I didn't consider before I started working on it, and which may or may not be useful to somebody else. Either way. If you want a simple and lightweight script to manage your machine, better run. Fast. If you don't mind a bit of what angry old IT folk and minimalism-hipsters would probably call 'bloat', and you think that a bit of harddrive-space is a good trade-off for saving a few minutes/hours every once in a while, give this here a go and tell me what you think.

Quickstart
----------

For its most basic use-case -- which is installing and configuring packages -- *freckles* needs:

 - one or more *configuration file(s)*
 - *curl* (or *wget*) -> for bootstrapping (well, technically it also needs *bash*)
  - optionally, a *dotfile repository* -> if some of the applications you want *freckles* to install have configuration files

At the moment (and that might change in the future), the easiest way to install *freckles* is to bootstrap it (more details: :ref:`Bootstrap`) using curl and bash. The bootstrap process can optionally also execute the first *freckles* run, which makes it possible to setup a machine with one line in your shell. Like:

.. code-block:: console

   $ curl -L https://get.frkl.io | bash -s -- apply gh:makkus/freckles/examples/quickstart.yml

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
          - epel-release:
              pkgs:
                yum:
                  - epel-release
          - htop
          - fortune:
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
    - create-folder: ~/.backups/zile



What this does:

 - checks out the repository of dotfile(s) at `https://github.com/makkus/freckles-quickstart.git <https://github.com/makkus/freckles-quickstart>`_
 - installs all the applications/packages that are configured in this repo (only the emacs-like editor ``zile`` in this case)
 - installs the ``epel`` repo if on a RPM-based platform
 - also installs a few other packages that don't require configuration which is the reason they are not included in the dotfiles repo (``htop`` and, depending on which platform this is run on one or some more packages for the `fortune` tool)
 - `stows <https://www.gnu.org/software/stow/>`_ all the dotfiles in the above repository into the users home directory (again, only for *zile* in this case)
 - creates a folder ``$HOME/.backups/zile`` if it doesn't exist already (needed because it is configured in the ``.zile`` config-file in the repo we checked out to be used as backup directory. *zile* does not create that dir itself and errors out if it doesn't exist)

To read how all that works in more detail, please read the full documentation at: :ref:`Usage`

You don't like executing random scripts on the internet? Yeah, me neither. Read here: :ref:`Trust`

Supported platforms
-------------------

Currently tested and supported
++++++++++++++++++++++++++++++

- Debian

  - Jessie

- Ubuntu

  - 16.04
  - 16.10


Planned / Partially supported
+++++++++++++++++++++++++++++

- MacOS X (should mostly work)
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

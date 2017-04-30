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


*managing dotfiles? and more? cute!*

At its heart, *freckles* is configuration management for your local machine(s). If you are familiar with ansible_, puppet_, or chef_ you know what configuration management is, and why it's a good idea. If not: in short, configuration management gives you a way to describe the configuration of a machine and the services and applications it runs in some way and format (e.g. in code, json, yml, ...) and apply this recorded configuration onto a vanilla (virtual or not) machine.

Depending on the configuration management framework you choose, the learning curve for them is quite steep, and require quite a bit of initial investment in terms of time to learn how they work, and to prepare the configuration that works for your infrastructure. Even the (arguably) easiest to pickup system, *ansible*, needs you to prepare and edit several files and folders, even for simple use-cases. This makes sense, since all of those solutions are quite powerful, and have to be able to deal with quite a lot of complexity.

*freckles*' goal is to simplify this configuration for use-cases that are less involved, like setting up your local workstation and development VMs with the tools of your choice, and the configuration needed to get started quickly. Without having to do a lot of manual bootstrapping, setup and preparation. Ideally, issuing one command, involving a pre-created configuration should be enough.

*freckles* is implemented as a layer on top off *ansible*. Instead of describing your infrastructure, as you do in *ansible*, in *freckles* you describe your working environment (in general, or for a specific project). This is only a subtle difference, and I'm still not sure whether its worth developing a project like *freckles*. The idea got me curious enough to try and find out though :-).

*freckles* is written in Python, and GPL v3 licensed.

Documentation: https://freckles.readthedocs.io.

Features
--------

* one-line setup of a new environment, including freckles bootstrap
* minimal and (hopefully) intuitive config file format, using ``yaml`` syntax
* supports Linux & MacOS X (and probably the Ubuntu subsystem on Windows 10)
* share the same configuration for your Linux and MacOS workstation as well as Vagrant machines, containers, etc.
* support for systems where you don't have root/sudo access via the nix_ package manager or conda_ (or if you just think it's a good idea to use any of them)
* direct support for all ansible_ modules and roles

Really quick-start
-----------------

.. code-block:: console

   curl -sL https://get.frkl.io | bash -s -- --help

This bootstraps *freckles*, runs it, and displays help information. All files that are installed live under the ``$HOME/.freckles`` folder, which can be deleted without affecting anything else. This also adds a line to your ``$HOME/.profile`` file to add `freckles` to your path.

Quickstart
----------

**Warning: run this only after you read what it does, as it installs some packages onto your computer you might not want. Should not do any real harm though.**

For its most basic use-case -- which is installing and configuring packages -- *freckles* needs:

 - one or more *configuration file(s)*
 - *curl* (or *wget*) -> for bootstrapping (well, technically it also needs *bash*)
 - optionally, a *dotfile repository* -> if some of the applications you want *freckles* to install have configuration files

At the moment (and that might change in the future), the easiest way to install *freckles* is to bootstrap it (more details: :ref:`Bootstrap`) using curl and bash. The bootstrap process can optionally also execute the first *freckles* run, which makes it possible to setup a machine with one line in your shell. Like:

.. code-block:: console

   curl -sL https://get.frkl.io | bash -s -- apply gh:makkus/freckles/examples/quickstart.yml

The config file I've choosen as an example is a bit more complicated than it'd need to be, but I wanted to show off how *freckles* can use the same config file for different platforms. If you only work on one platform, the same config would look quite a bit tidier. Check out the same example for (only) Debian/Ubuntu: `quickstart-debian.yml <https://github.com/makkus/freckles/blob/master/examples/quickstart-debian.yml>`_.

Either, way, the above command applies the following (fairly) simple configuration to your machine:

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
 - on Mac OS X, installs homebrew_ if it is not installed already (this does not need to be specified, *freckles* figures that out on its own)
 - installs the ``epel-release`` repo if on a RPM-based platform
 - installs all the applications/packages that are configured in the repo we checked out earlier (only the emacs-like editor ``zile`` in this case) -- this is done by setting the ``use_dotfiles`` variable of the ``install`` task to true
 - also installs a few other packages that don't require configuration which is the reason they are not included in the dotfiles repo (``htop`` and, depending on which platform this is run on one or some more packages for the `fortune` tool)
 - `stows <https://www.gnu.org/software/stow/>`_ all the dotfiles in the above repository into the users home directory (again, only for *zile* in this case)
 - creates a folder ``$HOME/.backups/zile`` if it doesn't exist already (needed because it is configured in the ``.zile`` config-file -- contained in the repo we checked out and 'stowed' (means symbolic-linked) to the user home directory -- to be used as backup directory. *zile* does not create that dir itself and errors out if it doesn't exist)

To read how all that works in more detail, please read the full documentation at: :ref:`Usage`

You don't like executing random scripts on the internet? Yeah, me neither. Read here: :ref:`Trust`

What, ...why?
-------------

I re-installed a new (or recently bricked) laptop or VM or container this one time too often, and I was annoyed that there is no real easy and quick way to re-create my working environment in those fresh environments, without having to write shell-scripts that sooner or later turn out unmaintainable and are fairly unflexible to begin with. Now, of course, that's what configuration management tools are for, and I do quite like ansible_ and have a bit of experience with it. What I don't like is how one usually needs a set of configuration files to describe a setup, even for simple use-cases like setting up a single, local machine. And I didn't want to install `ansible` itself manually every time before I can run my playbooks and roles. Basically, I wanted a thing that allows me to run one line of code, pointing to one configuration file, and after a while I have the same setup as I have on my other machines.

This is what `freckles` now is, sorta. As a result of my tendency to over-engineer everything in my way along with me having a bit of time on my hands -- it now can do a few other things which I didn't consider before I started working on it, and which may or may not be useful to somebody else. Either way. If you want a simple and lightweight script to manage your machine, you better run, fast. But if you don't mind a bit of what angry oldish IT folk and/or minimalism-hipsters would probably call 'bloat', and you think that a bit of harddrive-space is a good trade-off for saving a few minutes/hours every once in a while, give this here a go and tell me what you think.


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
.. _puppet: https://puppet.com
.. _chef: https://www.chef.io/chef
.. _nix: https://nixos.org/nix/
.. _conda: https://conda.io
.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _ansible-nix: https://github.com/AdamFrey/nix-ansible
.. _homebrew: https://brew.sh/

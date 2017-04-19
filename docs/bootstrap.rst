.. highlight:: shell

============
Bootstrap
============


There are a few different ways to bootstrap `freckles`. Depending on the state of your box, your proficiency and your general trust in random people on the internet, you can choose one of the methods below.

**Bootstrap & execution in one go:**

Below I only describe bootstrapping `freckles` itself. You can, however, execute `freckles` itself in the same go. If you want to do that, replace ``bash`` with ``bash -s -- <freckles_command>``. For example:

.. code-block:: console

    curl -sL https://get.frkl.io | bash -s -- apply gh:makkus/freckles/examples/quickstart.yml


Bootstrap via script (without elevated permissions)
---------------------------------------------------

This is the default way of bootstrapping `freckles`. It will create a self-contained installation (in ``$HOME/.freckles``), using conda_ to install requirements.

Supported
+++++++++

Those are the platforms I have tested so far, others might very well work too:

- Linux
- Debian

  - Jessie

- Ubuntu

  - 16.04
  - 16.10

- CentOS

  - 7

- Mac OS X

  - El Capitan

- Windows

  - Windows 10 (Ubuntu subsystem) -- not tested yet


Using `curl`:

.. code-block:: console

   curl -sL https://get.frkl.io | bash

Using `wget`:

.. code-block:: console

   wget -O - https://get.frkl.io | bash


If a ``$HOME/.profile`` file exists, the bootstrapping process adds a line to add ``$HOME/.freckles/bin`` to the users PATH, so `freckles` can be started directly in the future. To use `freckles` right after bootstrapping without having to logout and login again, do:

.. code-block:: console

   source $HOME/.profile

Or, if that doesn't apply to your machine because you don't have a ``.profile`` file, do something like this (how-/wherever you see fit):

.. code-block:: console

   export PATH=$PATH:$HOME/.freckles/bin


What does this do?
++++++++++++++++++

This installs the conda_ package manager (miniconda_ actually). Then it creates a `conda environment`_ called 'freckles', into which `freckles` along with its dependencies is installed.

Everything that is installed (about 450mb of stuff) is put into the ``$HOME/.freckles`` folder, which can be deleted without affecting anything else.

If a ``$HOME/.profile`` file exists, a line will be added to add ``$HOME/.freckles/bin`` to the users ``$PATH`` environment variable. If no such file exists, it's the users responsibility to either add that path, or start `freckles` directly using its path (``~/.freckles/bin/freckles``).


Bootstrap via script (with elevated permissions)
------------------------------------------------

This is a quicker way to bootstrap `freckles`, as 'normal' distribution packages are used to install dependencies. Also, the size of the ``$HOME/.freckles`` folder will be smaller, ~70mb -- systems packages are adding to that though). The `freckles` install itself is done in a virtualenv using `pip`. Root permissions are required.


Supported
+++++++++

Those are the platforms I have tested so far, others might very well work too:

   - Linux

     - Debian

       - Jessie

     - Ubuntu

       - 16.10
       - 16.04

     - CentOS

       - 7

   - Mac OS X

     - El Capitan

   - Windows

     - Windows 10 (Ubuntu subsystem) -- not tested yet

Using `curl`:

.. code-block:: console

   curl -sL https://get.frkl.io | sudo bash

Using `wget`:

.. code-block:: console

   wget -O - https://get.frkl.io | sudo bash


What does this do?
++++++++++++++++++

This installs all the requirements that are needed to create a Python virtualenv for `freckles`. What exactly those requirements are differs depending on the OS/Distribution that is used (check the :ref:`Install manually via pip` section for details). Then a Python virtual environment is created in ``$HOME/.freckles/opt/venv_freckles`` into which `freckles` and all its requirements are installed (~70mb).

If a ``$HOME/.profile`` file exists, a line will be added to add ``$HOME/.freckles/bin`` to the users ``$PATH`` environment variable. If no such file exists, it's the users responsibility to either add that path, or start `freckles` directly using its path.


Install manually via ``pip``
----------------------------

If you prefer to install `freckles` from pypi_ yourself, you'll have to install a few system packages, mostly to be able to install ``pycrypto`` when doing the ``pip install``.

Requirements
++++++++++++

Ubuntu/Debian
.............

.. code-block:: console

   apt install build-essential git python-dev python-virtualenv libssl-dev libffi-dev stow

RedHat/CentOS
.............

.. code-block:: console

   yum install epel-release wget git python-virtualenv stow openssl-devel stow gcc libffi-devel python-devel openssl-devel

MacOS X
.......

We need Xcode. Either install it from the app store, or do something like:

.. code-block:: console

    touch /tmp/.com.apple.dt.CommandLineTools.installondemand.in-progress;
    PROD=$(softwareupdate -l |
           grep "\*.*Command Line" |
           head -n 1 | awk -F"*" '{print $2}' |
           sed -e 's/^ *//' |
           tr -d '\n');
    softwareupdate -i "$PROD" -v;


We also need to manually install pip:

.. code-block:: console

    sudo easy_install pip

And freckles also depends on stow_ (if you want to be able to use that functionality within `freckles`). Either install it via homebrew or ports or whatever. Or from source (check out the `stow part of the bootstrap script`_ for an example).


Install `freckles`
++++++++++++++++++

Ideally, you'll install `freckles` into its own virtualenv. But if you read this you'll (hopefully) know how to do that. Here's how to install it system-wide (which I haven't tested, to be honest, so let me know if that doesn't work)

.. code-block:: console

   sudo pip install --upgrade pip   # just to make sure
   sudo pip install freckles

Optionally, if necessary add *freckles* to your PATH. for example, add something like the following to your ``.profile`` file (obviously, use the location you installed *freckles* into, not the one I show here):

.. code-block:: console

   if [ -e "$HOME/.freckles/opt/venv_freckles/bin/conda" ]; then export PATH="$HOME/.freckles/opt/venv_freckles/bin:$PATH"; fi


Bootstrapped files/layout
-------------------------

The bootstrap process will install `freckles` as well as its requirements. `freckles` (and depending on the bootstrap process choosen, also its dependencies) is installed into ``$HOME/.freckles/opt``. Symbolic links  ``freckles`` executable as well as some helper applications (``ansible-playbook``, ``conda``, etc.) are created in ``$HOME/.freckles/bin`` and a line is added to ``$HOME/.profile`` which adds this folder to the ``PATH`` variable, which means that after the next login (or after issuing ``source ~/.profile``) `freckles` can be run directly from then on.


.. _conda: https://conda.io
.. _miniconda: https://conda.io/miniconda.html
.. _`conda environment`: https://conda.io/docs/using/envs.html
.. _pypi: https://pypi.python.org
.. _stow: https://www.gnu.org/software/stow
.. _`stow part of the bootstrap script`: https://github.com/makkus/freckles/blob/master/bootstrap/freckles#L218

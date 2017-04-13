.. highlight:: shell

============
Bootstrap
============


There are a few different ways to bootstrap `freckles`. Depending on the state of your box, your proficiency and your general trust in random people on the internet, you can choose one of the methods below.

*Note*:

Below I only describe bootstrapping `freckles` itself. You can, though, execute `freckles` itself in the same go. If you want to do that, replace `bash` with `bash -s -- <freckles_command>`. For example:

.. code-block:: console

    curl -sL https://get.frkl.io | bash -s -- apply gh:makkus/freckles/examples/quickstart.yml


Run the bootstrap script directly (without elevated permissions)
----------------------------------------------------------------

- supported (and tested -- other distributions/version might very well work too):

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


This is the default way of bootstrapping `freckles`. It will create a self-contained installation (in ``$HOME/.freckles``), using conda_ to install requirements.

Using `curl`:

.. code-block:: console

   curl -sL https://get.frkl.io | bash

Using `wget`:

.. code-block:: console

   wget -O - https://get.frkl.io | bash


If a ``$HOME/.profile`` file exists, the bootstrapping process adds a line to add ``$HOME/.freckles/bin`` to the users PATH, so `freckles` can be started directly in the future. To use `freckles` right after bootstrapping without having to logout and login again, do:

.. code-block:: console

   source $HOME/.profile

Or, if that doesn't apply to your machine because you don't have a ``.profile`` file, do something like this (wherever you see fit):

.. code-block:: console

   export PATH=$PATH:$HOME/.freckles/bin


What does this do?
++++++++++++++++++

This installe conda_ (miniconda_ actually). Then it creates a `conda environment`_ called 'freckles', into which `freckles` along with its dependencies are installed.

Everything that is installed (about 450mb of stuff) is put into the ``$HOME/.freckles`` folder, which can be deleted without any problems.

If a ``$HOME/.profile`` file exists, a line will be added to add ``$HOME/.freckles/bin`` to the users ``$PATH`` environment variable. If no such file exists, it's the users responsibility to either add that path, or start `freckles` directly using its path.


Run the bootstrap script directly (with elevated permissions)
-------------------------------------------------------------

- supported (and tested -- other distributions/version might very well work too):

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


This is a quicker way to bootstrap `freckles`, as 'normal' distribution packages are used to install dependencies. Also, the size of the ``$HOME/.freckles`` folder will be smaller, ~70mb). The `freckles` install itself is done in a virtualenv using `pip`. Root permissions are required though.

Using `curl`:

.. code-block:: console

   curl -sL https://get.frkl.io | sudo bash

Using `wget`:

.. code-block:: console

   wget -O - https://get.frkl.io | sudo bash


What does this do?
++++++++++++++++++

This installs all the requirements that are needed to create a Python virtualenv for `freckles`. What exactly those requirements are differs depending on the OS/Distribution that is used. Then a Python virtual environment is created in ``$HOME/.freckles/opt/venv_freckles`` into which `freckles` and all its requirements are installed (~70mb).

If a ``$HOME/.profile`` file exists, a line will be added to add ``$HOME/.freckles/bin`` to the users ``$PATH`` environment variable. If no such file exists, it's the users responsibility to either add that path, or start `freckles` directly using its path.


Install manually via ``pip``
----------------------------

Requirements
++++++++++++

Ubuntu/Debian
.............

RedHat/CentOS
.............

MacOS X
.......

Install
+++++++


Bootstrapped files/layout
-------------------------

The bootstrap process will install `freckles` as well as its requirements. `freckles` (and depending on the bootstrap process choosen, also its dependencies) is installed into ``$HOME/.freckles/opt``. Symbolic links  ``freckles`` executable as well as some helper applications (``ansible-playbook``, ``conda``, etc.) are created in ``$HOME/.freckles/bin`` and a line is added to ``$HOME/.profile`` which adds this folder to the ``PATH`` variable, which means that after the next login (or after issuing ``source ~/.profile``) `freckles` can be run directly from then on:


.. _conda: https://conda.io
.. _miniconda: https://conda.io/miniconda.html
.. _`conda environments`: https://conda.io/docs/using/envs.html

.. highlight:: shell

============
Bootstrap
============


There are a few different ways to bootstrap `freckles`. Depending on the state of your box, your proficiency and your general trust in random people on the internet, you can choose one of the methods below.



Run the bootstrap script directly (without elevated permissions)
----------------------------------------------------------------

This is the default way of bootstrapping `freckles`. It will create a self-contained installation (in $HOME/.freckles), using conda_ to install requirements.

Using `curl`:

.. code-block:: console

   $ curl -sL https://get.frkl.io | bash

Using `wget`:

.. code-block:: console

   $ wget -O - https://get.frkl.io | bash


Run the bootstrap script directly (with elevated permissions)
-------------------------------------------------------------

This is a quicker way to bootstrap `freckles`, as 'normal' distribution packages are used to install dependencies. The `freckles` install itself is done in a virtualenv using `pip`.

Using `curl`:

.. code-block:: console

   $ curl -sL https://get.frkl.io | sudo bash

Using `wget`:

.. code-block:: console

   $ wget -O - https://get.frkl.io | sudo bash


.. _conda: https://conda.io

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

.. code-block:: console

   $ freckles --help

=====
Usage
=====
*freckles* is used using sub-commands, like for example *git*. To see a list of all available sub-commands, use the internal help system:

The internal ``help``
---------------------

.. code-block:: console

   freckles --help

To see the options for each sub-command, use:

.. code-block:: console

   freckles <subcommand> --help

``apply``-ing configurations
----------------------------

``apply`` is the main command to be used with *freckles*. It takes one or more configuration files or urls to configuration files, and applies the environment that is described in those onto the machine where *freckles* is running.

*freckles* configuration files are designed to be as simple to create as possible, while maintaining the ability to describe more complex setups by optionally supporting a more complex format. On this page we will only use the simple format, for more details on how to get the most out of it please check out the :ref:`configuration` section, as well as the usage :ref:`examples`.

Installing a few packages
+++++++++++++++++++++++++

For most simple use-cases, a single configuration file will be sufficient. *freckles* configurations are basically a list of tasks, and each task is of a certain type, and has it's own configuration. *freckles* supports several frequently used task types out of the box, but can be extended to use custom task types if necessary.

The most commonly used task type would probably be the ``install`` one. Let's assume we only want to use *freckles* to install a few packages using the default package manager. The default package manager for Debian/Ubuntu is ``apt``, for RedHat/CentOS its ``yum``, and for Mac OS X we use ``homebrew``. If we only use one platform, and intend to use the default package manager of this platform, we don't need to specify anything, which makes the configuration file simpler to create, and easier to read.

Here is a config that will install the packages ``htop``, ``fortunes``, and ``zile`` on a Debian/Ubuntu system:

.. code-block:: console

   tasks:
     - install:
         packages:
            - htop
            - fortunes
            - zile

In this example, we have one task (of the ``install` type), the configuration for the task being a list of package names.

This configuration file (as well as all the following ones) can be found in the `main freckles git repository <https://github.com/makkus/freckles>`_, in the `examples <https://github.com/makkus/freckles/tree/master/examples>`_ folder: `https://github.com/makkus/freckles/examples/usage-simple-debian.yml <https://github.com/makkus/freckles/blob/master/examples/usage-simple-debian.yml>`_

Because *freckles* is designed to be run as the first command on a fresh install, it can directly download configuration files, without them having to be present locally. It can also use local files though.

Here are a few examples on how to run freckles to apply this configuration, using either a local file, or a remote one:

Local configuration file
........................

Assuming you downloaded the config file into your 'Downloads' folder, you can run *freckles* like so:

.. code-block:: console

   freckles apply ~/Downloads/usage-simple-debian.yml

Remote configuration file, full url
...................................

Alternatively, we can just provide the full url to the file:

.. code-block:: console

   freckles apply https://github.com/makkus/freckles/raw/master/examples/usage-simple-debian.yml

Remote configuration file, short github url
...........................................

Because it's convenient, and easier to remember, *freckles* also supports shortcut urls for files that live on github (other services will be supported in the future):

.. code-block:: console

   freckles apply gh:makkus/freckles/examples/usage-simple-debian.yml


Either of those commands will do the same, and the output will look something like this:

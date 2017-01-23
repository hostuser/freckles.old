.. highlight:: shell

============
Bootstrap
============


There are a few different ways to bootstrap `freckles`. Depending on the state of your box, your proficiency and your general trust in random people on the internet, you can choose one of the methods below.



Run the bootstrap script directly (without elevated permissions)
----------------------------------------------------------------

This is the default way of bootstrapping `freckles`. It will create a self-contained installation (in $HOME/.freckles) using the


Using `curl`:

.. code-block:: console

   $ curl https://raw.githubusercontent.com/makkus/freckles/master/bootstrap/freckles | bash

Using `wget`:

.. code-block:: console

   $ wget -O - https://raw.githubusercontent.com/makkus/freckles/master/bootstrap/freckles | bash

Run the bootstrap script directly (with elevated permissions)
-------------------------------------------------------------

Using `curl`:

.. code-block:: console

   $ curl https://raw.githubusercontent.com/makkus/freckles/master/bootstrap/freckles | sudo bash

Using `wget`:

.. code-block:: console

   $ wget -O - https://raw.githubusercontent.com/makkus/freckles/master/bootstrap/freckles | sudo bash


To install freckles, run this command in your terminal:

.. code-block:: console

    $ pip install freckles

This is the preferred method to install freckles, as it will always install the most recent stable release. 

If you don't have `pip`_ installed, this `Python installation guide`_ can guide
you through the process.

.. _pip: https://pip.pypa.io
.. _Python installation guide: http://docs.python-guide.org/en/latest/starting/installation/


From sources
------------

The sources for freckles can be downloaded from the `Github repo`_.

You can either clone the public repository:

.. code-block:: console

    $ git clone git://github.com/makkus/freckles

Or download the `tarball`_:

.. code-block:: console

    $ curl  -OL https://github.com/makkus/freckles/tarball/master

Once you have a copy of the source, you can install it with:

.. code-block:: console

    $ python setup.py install


.. _Github repo: https://github.com/makkus/freckles
.. _tarball: https://github.com/makkus/freckles/tarball/master

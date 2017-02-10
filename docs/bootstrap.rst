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



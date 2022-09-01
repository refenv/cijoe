.. _sec-prerequisites:

Prerequisites
=============

**cijoe** seeks to be minimally intrusive, however, it does require the
following to operate.

On your **dev box**, ensure that you have:

* `Python 3`_ (>= 3.9)
* `pip3` (matching Python >= 3.9)
* The location emitted by ``python3 -m site --user-base`` in your ``$PATH``
  environment variable
* An **SSH** client, and **key-based** **authorization** providing unprompted login
  from your **dev box** into your **test-target**.

Check that you have the required versions by running the following on your
**dev box**:

.. code-block:: bash

  python3 --version
  pip3 --version

On your **test-target(s)** you need:

* An **account** to log into
* A running **SSH** server; providing remote login using your **account** from
  your **dev box**
* The **SSH** server configured to allow **key-based** **authorization** for
  your **account** and keys setup to provide unprompted login

**cijoe** relies on **SSH** in order to use a remote **test-target**. To assist
with the **SSH** setup then :ref:`sec-ssh` provides a setup guide for
unprompted login and verifying that the setup is ready to use with **cijoe**.

.. note:: **cjioe** can run "locally", that is, your **dev box** and
   **test-target** is the same machine. However, since most system
   development involves fiddling with the OS kernel, drivers, running
   destructive tests, and in general affect the **test-target** in ways
   that cause system panics and data-loss then the default assumption is that
   the **test-target** is another box accessible remotely via **SSH**.

.. _sec-ssh:

SSH Setup (required)
--------------------

**cijoe** uses ``SSH`` to run commands remotely. This section provides a couple
of setup notes which makes it a pleasant experience. Start with setting up
:ref:`sec-ssh-login`, without it then each command executed will prompt you for
login which is counter-productive. In case you need to execute commands as
``root`` on your **test-target** then you need to change your SSH daemon
configuration, see :ref:`sec-ssh-root` for that.

Lastly, if you want to have remote access to your **test-target** file-system,
then :ref:`sec-ssh-sshfs` provides an easy way of doing that using the ``SSH``
setup. You can of course also use it the other way around, e.g. have your
**test-target** mount your **dev box**.

.. note:: The setup instructions provided here is primarily aimed at
   Linux/FreeBSD/MacOSX like systems. For an equivalent setup-guide and
   description of using OpenSSH client/server on Windows then see `Microsoft
   Docs - OpenSSH in Windows
   <https://docs.microsoft.com/en-us/windows-server/administration/openssh/openssh_overview>`_.

.. _sec-ssh-login:

Unprompted Login
~~~~~~~~~~~~~~~~

Here is what we will do:

* Generate a ``SSH`` key-pair (private and public keys)
* Add the private-key to your SSH-agent
* Deploy the public-key to the target
* Create a target configuration
* Check the target configuration

Generate a Key-Pair
~~~~~~~~~~~~~~~~~~~

Run::

  ssh-keygen -P "" -f $HOME/.ssh/cijoe.key

This will produce the following key-pair::

  cijoe.key       # This is your private key
  cijoe.key.pub   # This is your public

Located in ``$HOME/.ssh/``.

SSH Agent
~~~~~~~~~

Add the key to the ssh-agent::

  ssh-add $HOME/.ssh/cijoe.key

Using an SSH-agent is convenient for keys that have passphrases, as you only
have to provide the passphrase once, when you add the key to the agent, instead
of each time they key is utilized.

Deploy the public-key
~~~~~~~~~~~~~~~~~~~~~

Deploy the public-key to remote host ``hostname``::

  ssh-copy-id -i $HOME/.ssh/cijoe.key.pub hostname

This is the last time you will be prompted for login information when
connecting to ``hostname`` as your user.

.. _sec-ssh-root:

SSH as root
~~~~~~~~~~~

The default configuration of ``sshd`` does **not** permit login using the
``root`` user. Thus, in case you need to **ssh** into the remote target using
``root`` then you need to change the ``ssh`` daemon configuration.

On the target, edit: ``/etc/ssh/sshd_config``, changing the ``PermitRootLogin``
option to::

  PermitRootLogin yes

Then reload the ``ssh`` daemon::

  sudo service ssh restart

It should now be ready for running ``ssh-copy-id`` as described above.

.. _sec-ssh-sshfs:

sshfs (optional)
----------------

The Secure-SHell File-System is a libfuse-based user space file-system which
provides a very easy way to mount a remote file-system via SSH. Install it
using your package-manager, e.g.::

  # Install sshfs
  sudo apt install sshfs

  # Change fuse-configuration; enable user_allow_other
  echo 'user_allow_other' | sudo tee -a /etc/fuse.conf

  # Create a directory for mountpoints
  mkdir $HOME/sshfs

For the specific host that you have deployed keys to, create a mountpoint::

  mkdir $HOME/sshfs/testbox

Mount it using::

  sudo sshfs \
    -o allow_other,default_permissions,IdentityFile=$HOME/.ssh/cijoe.key \
    user@hostname:/ $HOME/sshfs/testbox

And unmount using::

  sudo umount $HOME/sshfs/testbox

.. _SshKeys: https://www.digitalocean.com/community/tutorials/how-to-configure-ssh-key-based-authentication-on-a-linux-server

.. _Bash: https://www.gnu.org/software/bash/
.. _Python 3: https://www.python.org/

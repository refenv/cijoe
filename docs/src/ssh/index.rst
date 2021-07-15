.. _sec-ssh:

==========================
 Secure SHell (SSH) Setup
==========================

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
================

Here is what we will do:

* Generate a ``SSH`` key-pair (private and public keys)
* Add the private-key to your SSH-agent
* Deploy the public-key to the target
* Create a target configuration
* Check the target configuration

Generate a Key-Pair
-------------------

Run::

  ssh-keygen -P "" -f $HOME/.ssh/cijoe.key

This will produce the following key-pair::

  cijoe.key       # This is your private key
  cijoe.key.pub   # This is your public

Located in ``$HOME/.ssh/``.

SSH Agent
---------

Add the key to the ssh-agent::

  ssh-add $HOME/.ssh/cijoe.key

Using an SSH-agent is convenient for keys that have passphrases, as you only
have to provide the passphrase once, when you add the key to the agent, instead
of each time they key is utilized.

Deploy the public-key
---------------------

Deploy the public-key to remote host ``hostname``::

  ssh-copy-id -i $HOME/.ssh/cijoe.key.pub hostname

This is the last time you will be prompted for login information when
connecting to ``hostname`` as your user.

Create a target config
----------------------

Create a file named e.g. ``box01_env.sh``, with the content::

  #!/usr/bin/env bash
  export SSH_HOST=box01
  export SSH_USER=odus

In this example ``box01`` is the hostname of the target machine, and ``odus``
is the user to login as.

Check the target config
-----------------------

Verify that the **ssh** setup, and the **cijoe** target configuration works by
running **cijoe** interactively using the target configuration::

  cijoe box01_env.sh
  cij::cmd "hostname"

This should run the ``hostname`` command on the host ``box01``.

.. _sec-ssh-root:

SSH as root
===========

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

sshfs
=====

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

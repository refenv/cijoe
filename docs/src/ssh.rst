.. _sec-ssh:

====================
 Secure SHell (ssh)
====================

CIJOE utilizes ``SSH`` to run commands remotely. This section provides a couple
of setup notes which makes it a pleasant experience.

Generating Key-Pairs
====================

Run::

  ssh-keygen -P "" -f $HOME/.ssh/cijoe.key

This will produce the following key-pair::

  cijoe.key       # This is your private key
  cijoe.key.pub   # This is your public

Located in ``$HOME/.ssh/``.

SSH Agent
=========

Add the key to the ssh-agent::

  ssh-add $HOME/.ssh/cijoe.key

SSH Config
==========

... describe how to use ``$HOME/.ssh/config`` to provide the default username
and key to use with a given hostname ...

Deploying the public-key
========================

Deploy the public-key to remote host 'hostname'::

  ssh-copy-id -i $HOME/.ssh/cijoe.key.pub hostname

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

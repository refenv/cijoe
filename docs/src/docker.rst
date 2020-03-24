=============
 Docker
=============

**cijoe** can run in docker. First, pull the docker image from DockerHub or
build it yourself.

.. code-block:: bash

  # Pull cijoe image
  docker pull cijoe/cijoe

.. code-block:: bash

  # Build it yourself
  docker build . -t cijoe/cijoe

.. note:: **cijoe** will force the **mktemp** command to create temporary
  directories in the /results folder. This allows for easy extraction of test
  results, but may cause issues if your application relies on **mktemp**. We
  will resolve this issue in a future release.

You can now start the docker container and run a testplan. To make running
testplans easier, you can link your target environment and results folder.

.. code-block:: bash

  # Run cijoe
  docker run -it \
  -v $(pwd)/target_env.sh:/cijoe/target_env.sh \
  -v $(pwd)/results:/results \
  cijoe/cijoe

You can now run your testplan. See `QuickStart`_ for examples on how to use
**cijoe**. Starting the docker container is equivalent to running the **cijoe**
command.

.. note:: If you run **cijoe** tests on a remote system, bear in mind that you
  may need to transfer or link the SSH keys to the container. **cijoe** will
  make sure your keys are available in the docker container, if you mount your
  SSH folder in /tmp/cijoe/.ssh.

.. warning:: Linking SSH keys to the container gives any software running in
  the container full read access to the private keys. Do not do this if cijoe is
  running untrusted code.

.. code-block:: bash

  # Run cijoe with same key as the host
  docker run -it \
  -v $(pwd)/target_env.sh:/cijoe/target_env.sh \
  -v $(pwd)/results:/results \
  -v ~/.ssh:/tmp/cijoe/.ssh:ro \
  cijoe/cijoe

.. _Quickstart: https://cijoe.readthedocs.io/en/latest/quickstart.html#usage

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
  docker build . -f ./docker/Dockerfile -t cijoe/cijoe

You can now start the docker container and run a testplan. To make running
testplans easier, you can link your target environment and results folder. If
you build the docker container with the target_env.sh file, you should not
mount it afterwards.

.. code-block:: bash

  # Run cijoe
  docker run -it \
  -v $(pwd)/target_env.sh:/cijoe/target_env.sh \
  -v $(pwd)/results:/results \
  cijoe/cijoe

.. note:: When creating the RESULTS variable to store the results of a run,
  you should make sure to tell mktemp to store them in the /results folder for
  easier access afterwards.

.. code-block:: bash

  # Create directory to store results
  RESULTS=$(mktemp -p /results -d)

You can now run your testplan. See `QuickStart`_ for examples on how to use
**cijoe**. Starting the docker container is equivalent to running the **cijoe**
command.

.. note:: If you run **cijoe** tests on a remote system, bear in mind that you
  may need to transfer or link the SSH keys to the container. **cijoe** will
  make sure your keys are available in the docker container, if you mount your
  SSH folder in /root/.ssh.

.. warning:: Linking SSH keys to the container gives any software running in
  the container full read access to the private keys. Do not do this if cijoe is
  running untrusted code.

.. code-block:: bash

  # Run cijoe with same key as the host
  docker run -it \
  -v $(pwd)/target_env.sh:/cijoe/target_env.sh \
  -v $(pwd)/results:/results \
  -v ~/.ssh:/root/.ssh:ro \
  cijoe/cijoe

.. _Quickstart: https://cijoe.readthedocs.io/en/latest/quickstart.html#usage

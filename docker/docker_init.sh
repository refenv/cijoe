#!/usr/bin/env bash

# This file should be invoked when the cijoe docker container starts

set -e

if [[ -e ~/.ssh ]]; then
    # Start auth agent
    eval "$(ssh-agent)" > /dev/null

    # Load all private keys
    find ~/.ssh/ -type f -exec grep -l "PRIVATE" {} \; | xargs ssh-add &> /dev/null
fi

# If user has a config, move that config out of RO volume and change permissions
if [[ -e ~/.ssh/config ]]; then
    cp ~/.ssh/config ~/.ssh_config
else
    touch ~/.ssh_config
fi

chmod 600 ~/.ssh_config
chown $(whoami):$(whoami) ~/.ssh_config

# Launch cijoe
cijoe

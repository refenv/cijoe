FROM python:alpine

# Install build essentials, bash and ssh
RUN apk add alpine-sdk bash openssh-client

# Create a results volume
VOLUME /results

# Remap system config
RUN echo 'alias ssh="ssh -F ~/.ssh_config"' >> ~/.bashrc

# copy cijoe to container
COPY . /cijoe
WORKDIR /cijoe

# Build cijoe
RUN make install-system

ENTRYPOINT ["/cijoe/docker_init.sh"]

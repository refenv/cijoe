FROM python:alpine

# Install build essentials, bash and ssh
RUN apk add alpine-sdk bash openssh-client

# Create a results volume
VOLUME /results

# Force mktemp to store results in the volume
RUN echo 'alias mktemp="mktemp -p /results -t XXXXXX"' >> ~/.bashrc

# copy cijoe to container
COPY . /cijoe
WORKDIR /cijoe

# Build cijoe
RUN make install-system

ENTRYPOINT ["cijoe"]

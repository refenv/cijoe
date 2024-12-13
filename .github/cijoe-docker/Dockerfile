# Introduction
# ============
#
# This Dockerfile sets up an environment to run cijoe in CI pipelines, 
# such as those provided by GitHub Actions. It supports:
#
# * Building, installing, and running cijoe.
# * Running QEMU-guest in Docker:
#   - Ideal for using custom virtual machines on GitHub Actions.
# * Running Docker-in-Docker (DinD):
#   - Useful for executing 'docker build' within a Docker container.
#
# Based on Debian, this image leverages one of the most renowned Linux distributions, 
# offering a familiar environment for Ubuntu users. Debian provides freedom, 
# stability, and a vast selection of up-to-date packages.
#
# Custom QEMU
# ===========
#
# For specific use cases, you might require a more recent version of QEMU. 
# In such cases, this image can serve as a base, allowing you to extend it 
# by building a custom version of QEMU. This approach can provide newer 
# features or enable functionality not available in upstream versions.
FROM debian:bookworm

WORKDIR /opt

RUN apt-get -qy update && \
	apt-get -qy \
	-o "Dpkg::Options::=--force-confdef" \
	-o "Dpkg::Options::=--force-confold" upgrade \
	&& \
	apt-get -qy autoclean

RUN apt-get -qy -f install --no-install-recommends \
	bridge-utils \
	build-essential \
	ca-certificates \
	cloud-image-utils \
	docker.io \
	fuse3 \
	genisoimage \
	git \
	guestmount \
	htop \
	libglib2.0-dev \
	libguestfs-tools \
	linux-image-amd64 \
	lshw \
	meson \
	neovim \
	openssh-server \
	pipx \
	procps \
	python3-build \
	python3-jinja2 \
	qemu-kvm \
	qemu-system-arm \
	qemu-system-x86 \
	qemu-utils \
	ssh \
	time \
	kmod \
	pciutils \
	flex \
	bison \
	bc \
	cpio \
	libelf-dev \
	libssl-dev \
	rsync \
	debhelper-compat \
	&& \
	apt-get -qy clean && \
	apt-get -qy autoremove && \
	rm -rf /var/lib/apt/lists/* \
	pipx ensurepath

# Proide the cijoe-version as argument to the build and expose it in ENV
ARG CIJOE_VERSION
ENV CIJOE_VERSION=$CIJOE_VERSION

# Setup environment variables for pipx
ENV PIPX_HOME=/root/.local/pipx
ENV PATH=/root/.local/bin::$PATH

# Install cijoe itself
RUN pipx install cijoe==$CIJOE_VERSION \
	pipx inject cijoe coverage --include-apps --force \
	pipx inject cijoe pytest-cov --force

#
# Modified SSH Configuration, this is done enable the use of ssh to localhost
# without being prompted
#

# Setup SSH
RUN echo "PermitRootLogin yes" >> /etc/ssh/sshd_config && \
	systemctl enable ssh && \
	service ssh restart && \
	mkdir -p /root/.ssh && \
	chmod 0700 /root/.ssh && \
	ssh-keygen -b 2048 -t rsa -f /root/.ssh/id_rsa -q -N "" && \
	cp /root/.ssh/id_rsa.pub /root/.ssh/authorized_keys

# Don't want any of that hastle
RUN echo "Host *" >> /root/.ssh/config && \
	echo "  StrictHostKeyChecking no" >> /root/.ssh/config && \
	echo "  NoHostAuthenticationForLocalhost yes" >> /root/.ssh/config && \
	echo "  UserKnownHostsFile=/dev/null" >> /root/.ssh/config && \
	chmod 0400 /root/.ssh/config

CMD ["bash"]

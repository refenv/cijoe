FROM debian:bookworm

WORKDIR /opt

RUN apt-get -qy update && \
	apt-get -qy \
		-o "Dpkg::Options::=--force-confdef" \
		-o "Dpkg::Options::=--force-confold" upgrade && \
	apt-get -qy autoclean

RUN apt-get -qy -f install \
	bridge-utils \
	build-essential \
	cloud-image-utils \
	genisoimage \
	git \
	guestmount \
	htop \
	lshw \
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
	time

RUN pipx ensurepath

# Setup SSH
RUN echo "PermitRootLogin yes" >> /etc/ssh/sshd_config
RUN systemctl enable ssh
RUN service ssh restart
RUN mkdir -p /root/.ssh
RUN chmod 0700 /root/.ssh
RUN ssh-keygen -b 2048 -t rsa -f /root/.ssh/id_rsa -q -N ""
RUN cp /root/.ssh/id_rsa.pub /root/.ssh/authorized_keys

# Don't want any of that hastle
RUN echo "Host *" >> /root/.ssh/config
RUN echo "  StrictHostKeyChecking no" >> /root/.ssh/config
RUN echo "  NoHostAuthenticationForLocalhost yes" >> /root/.ssh/config
RUN echo "  UserKnownHostsFile=/dev/null" >> /root/.ssh/config
RUN chmod 0400 /root/.ssh/config

# This does not apply when SSH-ing to localhost, then ENV set by this is cleared
ENV PATH="/opt/qemu/bin:$PATH"
# So we also add it to /root/.profile
RUN echo 'PATH="/opt/qemu/bin:$PATH"' > /root/.profile

# Check that the correct qemu is being called
RUN qemu-system-x86_64 --version

CMD ["bash"]

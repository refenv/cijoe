# Base image
FROM fedora:40

# Install required packages: python3, pipx, make, and git
RUN dnf install -y \
    git \
    hostname \
    make \
    pciutils \
    pipx \
    pyproject-rpm-macros \
    python3 \
    python3-pip \
    && \
    dnf clean all \
    && \
    dnf autoremove

# Create a non-root user and group, set home directory
RUN useradd -m -s /bin/bash developer \
    && mkdir /cijoe \
    && chown developer:developer /cijoe

# Switch to the non-root user
USER developer

# Set working directory for the container
WORKDIR /home/developer

# Ensure PATH and environment is correct for pipx
ENV PIPX_HOME=/home/developer/.local/pipx
ENV PATH=/home/developer/.local/bin:/home/developer/.local/pipx/venvs/bin:$PATH

# Configure pipx for the non-root user
RUN pipx ensurepath

# Default command
CMD ["/bin/bash"]

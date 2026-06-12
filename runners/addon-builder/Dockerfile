# Kodi-Fleet Lightweight Addon Builder
FROM ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y \
    curl git jq sudo python3 python3-pip zip unzip \
    && rm -rf /var/lib/apt/lists/*
RUN useradd -m runner && usermod -aG sudo runner && echo "%sudo ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers
WORKDIR /home/runner
ARG RUNNER_VERSION=2.317.0
RUN curl -o actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz -L https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz && \
    tar xzf ./actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz && \
    rm actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz
RUN ./bin/installdependencies.sh
COPY entrypoint.sh /home/runner/entrypoint.sh
RUN sudo chmod +x /home/runner/entrypoint.sh
USER runner
ENTRYPOINT ["/home/runner/entrypoint.sh"]

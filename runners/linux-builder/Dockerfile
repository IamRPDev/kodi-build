# Kodi-Fleet Linux Builder Runner
FROM ubuntu:22.04

# Prevent interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

# Install base dependencies and CI tools
RUN apt-get update && apt-get install -y \
    curl \
    git \
    jq \
    sudo \
    build-essential \
    ca-certificates \
    libicu-dev \
    python3 \
    python3-pip \
    python3-dev \
    zip \
    unzip \
    tar \
    ccache \
    cmake \
    ninja-build \
    && rm -rf /var/lib/apt/lists/*

# Pre-install ALL Kodi C++ build dependencies (The massive list we identified)
RUN apt-get update && apt-get install -y \
    autoconf automake autopoint gettext libtool gawk gperf \
    libudev-dev libdrm-dev libgbm-dev libasound2-dev libpulse-dev libva-dev libvdpau-dev libxml2-dev libxslt1-dev \
    libsqlite3-dev libcurl4-openssl-dev libssl-dev libbluray-dev libcdio-dev libiso9660-dev liblzo2-dev libpcre3-dev \
    libmysqlclient-dev libcap-dev libfribidi-dev libfontconfig1-dev libfreetype6-dev libass-dev \
    libdbus-1-dev libsystemd-dev libavahi-client-dev libavahi-common-dev libmicrohttpd-dev libtinyxml-dev \
    libyajl-dev libplist-dev libnfs-dev libshairplay-dev libsmbclient-dev libfmt-dev libspdlog-dev libflatbuffers-dev \
    libx11-dev libxext-dev libxrandr-dev libxinerama-dev libxcursor-dev libxi-dev libxrender-dev libxss-dev libgl1-mesa-dev \
    # Cross-compilation tools
    mingw-w64 openjdk-17-jdk-headless \
    && rm -rf /var/lib/apt/lists/*

# Install Android SDK & NDK
ENV ANDROID_HOME=/opt/android-sdk
RUN mkdir -p ${ANDROID_HOME} && cd ${ANDROID_HOME} && \
    curl -o sdk.zip https://dl.google.com/android/repository/commandlinetools-linux-9477386_latest.zip && \
    unzip sdk.zip && rm sdk.zip && \
    mkdir -p cmdline-tools/latest && mv cmdline-tools/bin cmdline-tools/latest/ && mv cmdline-tools/lib cmdline-tools/latest/ && \
    yes | cmdline-tools/latest/bin/sdkmanager --sdk_root=${ANDROID_HOME} "platform-tools" "platforms;android-33" "build-tools;33.0.2" "ndk;25.2.9519653" && \
    ln -s ${ANDROID_HOME}/ndk/25.2.9519653 ${ANDROID_HOME}/ndk-bundle

# Add a non-root user for the runner
RUN useradd -m runner && \
    usermod -aG sudo runner && \
    echo "%sudo ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# Download and install the GitHub Runner agent
WORKDIR /home/runner
ARG RUNNER_VERSION=2.317.0
RUN curl -o actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz -L https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz && \
    tar xzf ./actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz && \
    rm actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz

# Install runner dependencies
RUN ./bin/installdependencies.sh

# Set up entrypoint for auto-configuration
COPY entrypoint.sh /home/runner/entrypoint.sh
RUN chmod +x /home/runner/entrypoint.sh

USER runner
ENTRYPOINT ["/home/runner/entrypoint.sh"]

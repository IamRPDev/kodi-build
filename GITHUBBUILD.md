# GitHub Build Fleet: Architecture & Infrastructure Guide

This guide details the multi-tiered GitHub build system used for high-performance, cross-platform compilation of Kodi and its primary add-ons. It is designed to be portable to other `gemini-cli` projects requiring a "Hub-Builder-Distributor" model.

---

## 1. Architecture Overview

The fleet operates across three distinct repository tiers to ensure separation of concerns and avoid resource exhaustion in a single repository.

### Tier 1: The Hub (`kodi-build`)
- **Role**: Command and Control.
- **Functions**:
    - Stores the fleet manifest (`sources.yaml`).
    - Orchestrates the entire fleet via `orchestrate-fleet.yml`.
    - Manages local runner registration scripts.
    - Monitors the fleet via `monitor.zsh`.

### Tier 2: The Builders (e.g., `xbmc-build`, `inputstream.adaptive-build`)
- **Role**: Compilation & Packaging.
- **Functions**:
    - Clones upstream source code.
    - Executes heavy C++ compilation using local or hosted runners.
    - Uploads artifacts directly to Tier 3 (Distributors).

### Tier 3: The Distributors (e.g., `xbmc-build-win64`, `xbmc-build-linux64`)
- **Role**: Artifact Hosting & Release.
- **Functions**:
    - Receives compiled binaries via `workflow_dispatch` or `gh release`.
    - Acts as a permanent host for binary releases for specific OS/Architecture pairs.

---

## 2. OS-Specific Build Logic

We use a unified build approach centered around Kodi's internal `depends` system to ensure consistency across the fleet.

### Linux (Ubuntu 22.04)
- **Method**: Native CMake.
- **Logic**: Uses pre-installed system libraries (`libudev-dev`, `libgbm-dev`, etc.) inside the builder image.
- **Flags**: `-DAPP_RENDER_SYSTEM=gl`.

### Cross-Platform (Windows, Android, macOS)
- **Method**: `tools/depends` Bootstrapping.
- **Workflow**:
    1.  `cd source/xbmc/tools/depends && ./bootstrap`
    2.  `./configure --prefix=$(pwd)/../../../../xbmc-deps $CONFIG_FLAGS`
    3.  `make -j$(nproc)`
    4.  The main CMake build then uses `-DCMAKE_PREFIX_PATH=$(pwd)/../xbmc-deps`.
- **Target Triplets**:
    - **Windows 64**: `--host=x86_64-w64-mingw32 --with-platform=windows`
    - **Android ARM64**: `--host=aarch64-linux-android --with-platform=android`
    - **OSX 64**: `--with-platform=macos`

---

## 3. Local Runner Infrastructure (The "Runner Farm")

To support long-running C++ builds (2+ hours), we utilize organization-level self-hosted runners.

### Dockerized Environment
- **Images**:
    - `linux-builder`: Full C++, Android SDK/NDK, MinGW, and Node.js.
    - `addon-builder`: Lightweight Python/Node environment.
- **Key Requirement**: **Node.js 20+** must be pre-baked into the image. Standard GitHub Actions (`checkout`, `cache`) will fail or hang without a Node runtime.
- **Security**: Runners are configured to run as a non-root `runner` user but with `NOPASSWD:ALL` sudo access for internal build steps.

### Deployment (`docker-compose.yml`)
```yaml
services:
  kodi-linux-builder:
    image: runners_linux-builder:latest
    volumes:
      - /mnt/largedata/github_runners/linux-builder/work:/home/runner/_work
      - /var/run/docker.sock:/var/run/docker.sock
    environment:
      - RUNNER_NAME=kodi-local-linux
      - GH_ORG=RPDevs-Builds
      - GH_TOKEN=${GH_PAT}
```

---

## 4. Automation & Maintenance

The fleet is maintained via API-driven Python scripts to ensure workflow parity across 30+ repositories.

### `_update_workflows_api.py`
This script uses the GitHub API to forcefully update the `.github/workflows/build.yml` file across all builder repositories. It injects:
- Updated runner labels.
- Conditional dependency installation logic.
- Standardized release naming conventions (`xbmc-linux64-v21.0-Piers.zip`).

### `monitor.zsh`
A real-time dashboard that uses parallel background `gh run list` calls to provide a matrix view of the entire organization's build health.

---

## 5. Lessons Learned & Heuristics

- **Pre-bake Dependencies**: Avoid `sudo apt install` during workflow runs on self-hosted runners. This prevents "no new privileges" errors and significantly reduces build time.
- **Explicit Platform Flags**: Kodi's `configure` script often fails to auto-detect cross-compile targets. Always provide `--with-platform` and `--host` explicitly.
- **Version Alignment**: Keep the Dockerized runner version synced with GitHub's latest (e.g., `2.335.1`) to avoid startup delays due to self-updates.
- **Organization Registration**: Register runners at the **Organization level**, not the Repository level. This allows any builder in the fleet to pick up the job immediately.

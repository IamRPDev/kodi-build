# Centralized GitHub Runners

This repository manages the deployment configurations for the RPDevs-Vault build fleet.

## Fleet Nodes
1. **llmadmin01**: High-performance primary node (10 threads, 16GB RAM allocation).
2. **T430**: Auxiliary/Parallel node (3 CPUs, 4GB RAM allocation).

## Storage Architecture
* **Working Directories (`_work`)**: Mounted to compressed `zram` RAM disks on each host (`/mnt/data/github_runners/work` and `/mnt/largedata/github_runners/work`) for ultra-fast, isolated compilation.
* **Apt Cache**: Mounted to NAS (`/mnt/sharedroot/data/apt-cache`) to reduce redundant package downloads across the fleet.
* **Outputs**: Mounted to NAS (`/mnt/sharedroot/github_runners/<node>`) for persistent artifact storage.

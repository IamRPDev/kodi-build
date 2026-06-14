# Centralized GitHub Runners

This repository manages the deployment configurations for the RPDevs ecosystem build fleet.

## Multi-Tenant Architecture
The fleet is configured as a multi-tenant grid supporting:
1. **RPDevs-Vault** (Org): Archival and Infrastructure Management.
2. **RPDevs-Builds** (Org): High-frequency Kodi Core and Addon Builds.
3. **IamRPDev** (User): Personal developer actions.

## Fleet Nodes
1. **llmadmin01**: High-performance primary node (10 threads, 16GB RAM allocation).
2. **T430**: Auxiliary/Parallel node (3 CPUs, 4GB RAM allocation).

## Storage Architecture
* **Working Directories (`_work`)**: Mounted to compressed `zram` RAM disks on each host (`/mnt/data/github_runners/work` and `/mnt/largedata/github_runners/work`) for ultra-fast, isolated compilation.
* **Apt Cache**: Mounted to NAS (`/mnt/sharedroot/data/apt-cache`) to reduce redundant package downloads across the fleet.
* **Outputs**: Mounted to NAS (`/mnt/sharedroot/github_runners/<node>`) for persistent artifact storage.

## Deployment
Each node runs a `docker-compose.yml` that instantiates listeners for each scope.
Images are verified and pulled from **GHCR**: `ghcr.io/rpdevs-vault/runner-linux-builder:latest`.

```bash
# Example Deploy
cd llmadmin01
docker-compose pull && docker-compose up -d
```

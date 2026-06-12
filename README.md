# Kodi Build Hub 🚀

Welcome to the central orchestration hub for all things Kodi. This repository manages the automated compilation and distribution of Kodi Core, Plugins, Scripts, Scrapers, and Inputstream addons.

## Build & Distribution Status

| Component | Piers (master) Status | Omega Status | Build/Release Repository |
|:---|:---:|:---:|:---|
| **Kodi Core** | [![Piers](https://github.com/RPDevs-Builds/xbmc-build/actions/workflows/build.yml/badge.svg?branch=master)](https://github.com/RPDevs-Builds/xbmc-build/actions) | [![Omega](https://github.com/RPDevs-Builds/xbmc-build/actions/workflows/build.yml/badge.svg?branch=Omega)](https://github.com/RPDevs-Builds/xbmc-build/actions) | [xbmc-build](https://github.com/RPDevs-Builds/xbmc-build) |
| **Plugins** | [![Piers](https://github.com/RPDevs-Builds/repo-plugins-build/actions/workflows/build.yml/badge.svg?branch=master)](https://github.com/RPDevs-Builds/repo-plugins-build/actions) | [![Omega](https://github.com/RPDevs-Builds/repo-plugins-build/actions/workflows/build.yml/badge.svg?branch=Omega)](https://github.com/RPDevs-Builds/repo-plugins-build/actions) | [repo-plugins-build](https://github.com/RPDevs-Builds/repo-plugins-build) |
| **Scripts** | [![Piers](https://github.com/RPDevs-Builds/repo-scripts-build/actions/workflows/build.yml/badge.svg?branch=master)](https://github.com/RPDevs-Builds/repo-scripts-build/actions) | [![Omega](https://github.com/RPDevs-Builds/repo-scripts-build/actions/workflows/build.yml/badge.svg?branch=Omega)](https://github.com/RPDevs-Builds/repo-scripts-build/actions) | [repo-scripts-build](https://github.com/RPDevs-Builds/repo-scripts-build) |
| **Scrapers** | [![Piers](https://github.com/RPDevs-Builds/repo-scrapers-build/actions/workflows/build.yml/badge.svg?branch=master)](https://github.com/RPDevs-Builds/repo-scrapers-build/actions) | [![Omega](https://github.com/RPDevs-Builds/repo-scrapers-build/actions/workflows/build.yml/badge.svg?branch=Omega)](https://github.com/RPDevs-Builds/repo-scrapers-build/actions) | [repo-scrapers-build](https://github.com/RPDevs-Builds/repo-scrapers-build) |
| **FFmpegDirect**| [![Piers](https://github.com/RPDevs-Builds/inputstream.ffmpegdirect-build/actions/workflows/build.yml/badge.svg?branch=master)](https://github.com/RPDevs-Builds/inputstream.ffmpegdirect-build/actions) | [![Omega](https://github.com/RPDevs-Builds/inputstream.ffmpegdirect-build/actions/workflows/build.yml/badge.svg?branch=Omega)](https://github.com/RPDevs-Builds/inputstream.ffmpegdirect-build/actions) | [inputstream.ffmpegdirect-build](https://github.com/RPDevs-Builds/inputstream.ffmpegdirect-build) |
| **Adaptive** | [![Piers](https://github.com/RPDevs-Builds/inputstream.adaptive-build/actions/workflows/build.yml/badge.svg?branch=master)](https://github.com/RPDevs-Builds/inputstream.adaptive-build/actions) | [![Omega](https://github.com/RPDevs-Builds/inputstream.adaptive-build/actions/workflows/build.yml/badge.svg?branch=Omega)](https://github.com/RPDevs-Builds/inputstream.adaptive-build/actions) | [inputstream.adaptive-build](https://github.com/RPDevs-Builds/inputstream.adaptive-build) |

## Kodi Core (OS Specific Distributors)
Due to size constraints, the Kodi Core installers are distributed via platform-specific repositories:
- [Linux 64 Release Repo](https://github.com/RPDevs-Builds/xbmc-build-linux64)
- [Windows 64 Release Repo](https://github.com/RPDevs-Builds/xbmc-build-win64)
- [Android ARM64 Release Repo](https://github.com/RPDevs-Builds/xbmc-build-android-arm64)
- [OSX 64 Release Repo](https://github.com/RPDevs-Builds/xbmc-build-osx64)

## Build Architecture
1.  **Hub (`kodi-build`)**: This repository. Orchestrates triggers and monitors the fleet.
2.  **Builders (`-build`)**: Contain logic to compile code into `./compiled/<os>/<version>/`.
3.  **Distributors**: Only used for Kodi Core. Addon components host their own releases.

---
*Maintained by RPDevs-Builds*

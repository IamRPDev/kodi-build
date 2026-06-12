import os
import subprocess

def run(cmd, cwd=None):
    return subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)

builders = [
    ("xbmc-build", "Kodi Core", "xbmc"),
    ("repo-plugins-build", "Plugins", "repo-plugins"),
    ("repo-scripts-build", "Scripts", "repo-scripts"),
    ("repo-scrapers-build", "Scrapers", "repo-scrapers"),
    ("inputstream.ffmpegdirect-build", "FFmpegDirect", "inputstream.ffmpegdirect"),
    ("inputstream.adaptive-build", "Adaptive", "inputstream.adaptive"),
]

oss = ["linux64", "win64", "android-arm64", "osx64"]

os.makedirs("temp_repos", exist_ok=True)

# 1. Update Builders
for repo, name, comp_id in builders:
    print(f"Updating Builder: {repo}")
    path = os.path.join("temp_repos", repo)
    os.makedirs(path, exist_ok=True)
    
    run(f"git clone --depth 1 https://github.com/RPDevs-Builds/{repo}.git .", cwd=path)
    
    readme_content = f"""# {name} Builder 🏗️

This repository is a dedicated **Builder** for the **{name}** component of the Kodi ecosystem. 

## Role in Ecosystem
This repository is part of the [Kodi Build Hub](https://github.com/RPDevs-Builds/kodi-build). Its primary responsibilities are:
1.  **Orchestration**: Triggered by the central hub to start builds.
2.  **Compilation**: Maintains the `./source` and `./compiled` directory structure to build the component from upstream source.
3.  **Distribution**: Upon successful build, it dispatches the final installers to OS-specific release repositories.

## Supported Branches
- **Piers**: The latest development/master branch.
- **Omega**: The stable release branch.

## Build Matrix
| Platform | Status | Release Target |
|:---|:---:|:---|
| Linux 64 | [![Build Status](https://github.com/RPDevs-Builds/{repo}/actions/workflows/build.yml/badge.svg)](https://github.com/RPDevs-Builds/{repo}/actions) | [{comp_id}-build-linux64](https://github.com/RPDevs-Builds/{comp_id}-build-linux64) |
| Windows 64 | | [{comp_id}-build-win64](https://github.com/RPDevs-Builds/{comp_id}-build-win64) |
| Android ARM64 | | [{comp_id}-build-android-arm64](https://github.com/RPDevs-Builds/{comp_id}-build-android-arm64) |
| OSX 64 | | [{comp_id}-build-osx64](https://github.com/RPDevs-Builds/{comp_id}-build-osx64) |

---
*Back to [Kodi Build Hub Index](https://github.com/RPDevs-Builds/kodi-build)*
"""
    with open(os.path.join(path, "README.md"), "w") as f:
        f.write(readme_content)
    
    run("git add README.md", cwd=path)
    run("git commit -m 'docs: initialize comprehensive builder README'", cwd=path)
    run("git push", cwd=path)

# 2. Update Distributors
for repo, name, comp_id in builders:
    for os_name in oss:
        dist_repo = f"{comp_id}-build-{os_name}"
        print(f"Updating Distributor: {dist_repo}")
        path = os.path.join("temp_repos", dist_repo)
        os.makedirs(path, exist_ok=True)
        
        run(f"git clone --depth 1 https://github.com/RPDevs-Builds/{dist_repo}.git .", cwd=path)
        
        readme_content = f"""# {name} {os_name} Distribution 📦

This repository hosts the final compiled installers for **{name}** on the **{os_name}** platform.

## Downloads
All binaries are hosted in the [Releases](https://github.com/RPDevs-Builds/{dist_repo}/releases) section.

### Versioning
- **Piers Releases**: Development builds from the main branch.
- **Omega Releases**: Stable builds from the Omega release branch.

## Ecosystem
This repository is a **Distributor** in the [Kodi Build Hub](https://github.com/RPDevs-Builds/kodi-build). It receives artifacts automatically from the [{repo}](https://github.com/RPDevs-Builds/{repo}) builder.

---
*Back to [Kodi Build Hub Index](https://github.com/RPDevs-Builds/kodi-build)*
"""
        with open(os.path.join(path, "README.md"), "w") as f:
            f.write(readme_content)
        
        run("git add README.md", cwd=path)
        run("git commit -m 'docs: initialize comprehensive distributor README'", cwd=path)
        run("git push", cwd=path)

print("Documentation update complete!")

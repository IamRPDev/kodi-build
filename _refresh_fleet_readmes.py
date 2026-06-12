import os
import subprocess

# Set up GIT_ASKPASS to handle the passphrase
askpass_path = os.path.abspath(".git_askpass_readme.sh")
with open(askpass_path, "w") as f:
    f.write("#!/bin/bash\necho 'Molp;sYrd;s'\n")
os.chmod(askpass_path, 0o755)

env = os.environ.copy()
env["GIT_ASKPASS"] = askpass_path
env["DISPLAY"] = ":0"

def run(cmd, cwd=None):
    return subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True, env=env)

builders = [
    ("xbmc-build", "Kodi Core", "xbmc", True),
    ("repo-plugins-build", "Plugins", "repo-plugins", False),
    ("repo-scripts-build", "Scripts", "repo-scripts", False),
    ("repo-scrapers-build", "Scrapers", "repo-scrapers", False),
    ("inputstream.ffmpegdirect-build", "FFmpegDirect", "inputstream.ffmpegdirect", False),
    ("inputstream.adaptive-build", "Adaptive", "inputstream.adaptive", False),
]

distributors = [
    ("xbmc-build-linux64", "Linux 64"),
    ("xbmc-build-win64", "Windows 64"),
    ("xbmc-build-android-arm64", "Android ARM64"),
    ("xbmc-build-osx64", "OSX 64"),
]

os.makedirs("fleet_docs_update", exist_ok=True)

# 1. Update Builders
for repo, name, comp_id, is_core in builders:
    print(f"Updating README for Builder: {repo}")
    path = os.path.join("fleet_docs_update", repo)
    if not os.path.exists(path):
        run(f"git clone https://github.com/RPDevs-Builds/{repo}.git .", cwd=path) if os.makedirs(path, exist_ok=True) or True else None
        run(f"git clone https://github.com/RPDevs-Builds/{repo}.git .", cwd=path)
    
    release_info = "distributes to platform-specific repositories." if is_core else "hosts its own releases locally."
    
    readme_content = f"""# {name} Builder 🏗️

This repository is the automated **Builder** for **{name}**.

## Ecosystem Role
Part of the [Kodi Build Hub](https://github.com/RPDevs-Builds/kodi-build). This repo {release_info}

## Build Structure
The build process strictly follows this standardized structure:
- **Source**: Upstream code is checked out into `./source/{comp_id}/`.
- **Output**: Compiled binaries are organized into `./compiled/<os>/<version>/`.
- **Artifacts**: Final files use the naming convention `{comp_id}-<os>-<version>-<branch>.[zip|tar.gz]`.

## Live Status
- **Piers (master)**: [![Piers Status](https://github.com/RPDevs-Builds/{repo}/actions/workflows/build.yml/badge.svg?branch=master)](https://github.com/RPDevs-Builds/{repo}/actions)
- **Omega**: [![Omega Status](https://github.com/RPDevs-Builds/{repo}/actions/workflows/build.yml/badge.svg?branch=Omega)](https://github.com/RPDevs-Builds/{repo}/actions)

---
*Back to [Kodi Build Hub](https://github.com/RPDevs-Builds/kodi-build)*
"""
    with open(os.path.join(path, "README.md"), "w") as f:
        f.write(readme_content)
    
    run("git add README.md", cwd=path)
    run("git commit -m 'docs: update README to reflect consolidated architecture'", cwd=path)
    run("git push", cwd=path)

# 2. Update Distributors
for repo, os_name in distributors:
    print(f"Updating README for Distributor: {repo}")
    path = os.path.join("fleet_docs_update", repo)
    if not os.path.exists(path):
        run(f"git clone https://github.com/RPDevs-Builds/{repo}.git .", cwd=path) if os.makedirs(path, exist_ok=True) or True else None
        run(f"git clone https://github.com/RPDevs-Builds/{repo}.git .", cwd=path)

    readme_content = f"""# Kodi Core {os_name} Distribution 📦

This repository hosts the final compiled installers for **Kodi Core** on the **{os_name}** platform.

## Downloads
Find all versions in the [Releases](https://github.com/RPDevs-Builds/{repo}/releases) section.

## Architecture
This is a **Distributor** repository in the [Kodi Build Hub](https://github.com/RPDevs-Builds/kodi-build). It receives artifacts automatically from the [xbmc-build](https://github.com/RPDevs-Builds/xbmc-build) builder.

Files follow the pattern: `xbmc-{repo.split('-')[-1]}-<version>-<branch>.[zip|tar.gz]`

---
*Back to [Kodi Build Hub](https://github.com/RPDevs-Builds/kodi-build)*
"""
    with open(os.path.join(path, "README.md"), "w") as f:
        f.write(readme_content)
    
    run("git add README.md", cwd=path)
    run("git commit -m 'docs: update README for distributor role'", cwd=path)
    run("git push", cwd=path)

# Cleanup
os.remove(askpass_path)
print("Fleet-wide documentation refresh complete!")

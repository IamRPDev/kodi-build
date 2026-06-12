import os
import subprocess
import shutil

# Set up GIT_ASKPASS to handle the passphrase
askpass_path = os.path.abspath(".git_askpass_consolidation.sh")
with open(askpass_path, "w") as f:
    f.write("#!/bin/bash\necho 'Molp;sYrd;s'\n")
os.chmod(askpass_path, 0o755)

env = os.environ.copy()
env["GIT_ASKPASS"] = askpass_path
env["SSH_ASKPASS"] = askpass_path
env["DISPLAY"] = ":0"
env["GIT_TERMINAL_PROMPT"] = "0"

def run(cmd, cwd=None):
    # Use -c to pass the command to bash and ensure env is respected
    return subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True, env=env)

builders = [
    ("xbmc-build", "Kodi Core", "xbmc", True),
    ("repo-plugins-build", "Plugins", "repo-plugins", False),
    ("repo-scripts-build", "Scripts", "repo-scripts", False),
    ("repo-scrapers-build", "Scrapers", "repo-scrapers", False),
    ("inputstream.ffmpegdirect-build", "FFmpegDirect", "inputstream.ffmpegdirect", False),
    ("inputstream.adaptive-build", "Adaptive", "inputstream.adaptive", False),
]

os.makedirs("build_fleet_consolidated", exist_ok=True)

for repo_name, display_name, comp_id, is_core in builders:
    print(f"Refactoring workflow for: {repo_name}")
    repo_path = os.path.join("build_fleet_consolidated", repo_name)
    
    if os.path.exists(repo_path):
        shutil.rmtree(repo_path)
    
    # Use HTTPS with dummy credentials to force GIT_ASKPASS
    res = run(f"git clone https://x-access-token@github.com/RPDevs-Builds/{repo_name}.git {repo_path}")
    if res.returncode != 0:
        print(f"Clone failed for {repo_name}: {res.stderr}")
        continue

    workflow_dir = os.path.join(repo_path, ".github", "workflows")
    os.makedirs(workflow_dir, exist_ok=True)
    
    is_cpp = "inputstream" in comp_id or is_core
    
    # Release Logic: Core dispatches to OS repos, others keep local
    if is_core:
        dispatch_logic = f"""
          DIST_REPO="RPDevs-Builds/{comp_id}-build-${{{{ matrix.platform }}}}"
          gh release create "$TAG" $FILE \\
            --repo "$DIST_REPO" \\
            --title "{display_name} ${{{{ matrix.branch }}}} Build $TAG" \\
            --notes "Automated build from {repo_name}." \\
            --prerelease || \\
          gh release upload "$TAG" $FILE --repo "$DIST_REPO" --clobber
"""
    else:
        dispatch_logic = f"""
          # Create local release in this repo
          gh release create "$TAG" $FILE \\
            --title "{display_name} ${{{{ matrix.branch }}}} Build $TAG" \\
            --notes "Automated build for ${{{{ matrix.platform }}}}." \\
            --prerelease || \\
          gh release upload "$TAG" $FILE --clobber
"""

    workflow_content = f"""name: Build and Dispatch {display_name}

on:
  workflow_dispatch:
    inputs:
      branch_input:
        description: 'Branch to build'
        required: true
        default: 'both'
        type: choice
        options:
          - both
          - Piers
          - Omega

permissions:
  contents: write

env:
  FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: true

jobs:
  setup-matrix:
    runs-on: ubuntu-latest
    outputs:
      matrix: ${{{{ steps.set-matrix.outputs.matrix }}}}
    steps:
      - id: set-matrix
        run: |
          if [ "${{{{ github.event.inputs.branch_input }}}}" == "both" ]; then
            echo 'matrix={{"branch": ["Piers", "Omega"], "platform": ["linux64", "win64", "android-arm64", "osx64"]}}' >> $GITHUB_OUTPUT
          else
            echo 'matrix={{"branch": ["${{{{ github.event.inputs.branch_input }}}}"], "platform": ["linux64", "win64", "android-arm64", "osx64"]}}' >> $GITHUB_OUTPUT
          fi

  build:
    needs: setup-matrix
    strategy:
      fail-fast: false
      matrix: ${{{{ fromJson(needs.setup-matrix.outputs.matrix) }}}}
    name: Build ${{{{ matrix.branch }}}} on ${{{{ matrix.platform }}}}
    runs-on: ${{{{ (matrix.platform == 'osx64' && 'macos-latest') || ('{is_cpp}' == 'True' && fromJSON('["self-hosted", "linux64"]') || fromJSON('["self-hosted", "lightweight"]')) }}}}
    defaults:
      run:
        shell: bash
    steps:
      - name: Checkout Source
        uses: actions/checkout@v4
        with:
          repository: xbmc/{comp_id}
          ref: ${{{{ matrix.branch == 'Piers' && ('{comp_id}' == 'inputstream.ffmpegdirect' || '{comp_id}' == 'inputstream.adaptive') && 'Piers' || (matrix.branch == 'Piers' && 'master' || 'Omega') }}}}
          path: source/{comp_id}
          fetch-depth: 1

      - name: Install System Dependencies
        run: |
          if [ "${{{{ runner.os }}}}" == "Linux" ]; then
            sudo apt update
            sudo apt install -y build-essential autoconf automake autopoint gettext cmake curl gawk gperf python3-dev libtool zip unzip \\
              libudev-dev libdrm-dev libgbm-dev libasound2-dev libpulse-dev libva-dev libvdpau-dev libxml2-dev libxslt1-dev \\
              libsqlite3-dev libcurl4-openssl-dev libssl-dev libbluray-dev libcdio-dev libiso9660-dev liblzo2-dev libpcre3-dev \\
              libmysqlclient-dev libcap-dev libfribidi-dev libfontconfig1-dev libfreetype6-dev libass-dev libfribidi-dev \\
              libdbus-1-dev libsystemd-dev libavahi-client-dev libavahi-common-dev libmicrohttpd-dev libtinyxml-dev \\
              libyajl-dev libplist-dev libnfs-dev libshairplay-dev libsmbclient-dev libfmt-dev libspdlog-dev libflatbuffers-dev
            if [ "${{{{ matrix.platform }}}}" == "linux64" ]; then
              sudo apt install -y libx11-dev libxext-dev libxrandr-dev libxinerama-dev libxcursor-dev libxi-dev libxrender-dev libxss-dev libgl1-mesa-dev
            fi
          elif [ "${{{{ runner.os }}}}" == "Windows" ]; then
            choco install cmake ninja nasm zip -y
          elif [ "${{{{ runner.os }}}}" == "macOS" ]; then
            brew install cmake ninja nasm
          fi

      - name: Build and Package
        run: |
          # Get Version for directory structure
          if [ -f source/{comp_id}/version.txt ]; then
            VERSION=$(grep "VERSION_CODE" source/{comp_id}/version.txt | awk '{{print $2}}')
          else
            VERSION="v-$(date +'%Y%m%d')"
          fi
          echo "VERSION=$VERSION" >> $GITHUB_ENV
          
          # Target Directory: ./compiled/os/version/
          OUT_DIR="compiled/${{{{ matrix.platform }}}}/$VERSION"
          mkdir -p "$OUT_DIR"
          echo "OUT_DIR=$OUT_DIR" >> $GITHUB_ENV

          if [ "{is_cpp}" == "True" ]; then
            echo "🚀 Performing C++ Build for ${{{{ matrix.platform }}}}..."
            if [ "{comp_id}" == "xbmc" ]; then
              if [ "${{{{ matrix.platform }}}}" == "linux64" ]; then
                mkdir build && cd build
                cmake ../source/xbmc -DCMAKE_INSTALL_PREFIX=../$OUT_DIR -DAPP_RENDER_SYSTEM=gl
                make -j$(nproc) install
              else
                # Cross-compilation or non-linux native using depends
                cd source/xbmc/tools/depends
                ./bootstrap
                case "${{{{ matrix.platform }}}}" in
                  win64) CONFIG_FLAGS="--host=x86_64-w64-mingw32" ;;
                  android-arm64) CONFIG_FLAGS="--host=aarch64-linux-android --with-sdk=/opt/android-sdk --with-ndk=/opt/android-sdk/ndk-bundle" ;;
                  osx64) CONFIG_FLAGS="--with-platform=macos" ;;
                esac
                ./configure --prefix=$(pwd)/../../../../xbmc-deps $CONFIG_FLAGS
                make -j$(nproc || sysctl -n hw.ncpu)
                cd ../../../
                mkdir build && cd build
                cmake ../source/xbmc -DCMAKE_INSTALL_PREFIX=../$OUT_DIR -DCMAKE_PREFIX_PATH=$(pwd)/../xbmc-deps
                make -j$(nproc || sysctl -n hw.ncpu) install
              fi
            else
              # Addon C++ Build
              mkdir build && cd build
              # Try to find KodiConfig.cmake if it was built in a previous step or provided
              cmake ../source/{comp_id} -DCMAKE_INSTALL_PREFIX=../$OUT_DIR -DKodi_DIR=$(pwd)/../xbmc-deps/lib/kodi
              make -j$(nproc || sysctl -n hw.ncpu) install
            fi
          else
            echo "📦 Packaging Python/XML Addon..."
            cp -rv source/{comp_id}/* "$OUT_DIR/"
            touch "$OUT_DIR/.kodi_build_marker"
          fi

      - name: Create Archive
        run: |
          TAG="v-${{{{ env.VERSION }}}}-${{{{ matrix.branch }}}}"
          echo "TAG=$TAG" >> $GITHUB_ENV
          FILENAME="{comp_id}-${{{{ matrix.platform }}}}-${{{{ env.VERSION }}}}-${{{{ matrix.branch }}}}"
          if [ "${{{{ matrix.platform }}}}" == "linux64" ]; then
            tar -czf "$FILENAME.tar.gz" -C "$OUT_DIR" .
            echo "FILE=$FILENAME.tar.gz" >> $GITHUB_ENV
          else
            cd "$OUT_DIR" && zip -r "../../$FILENAME.zip" .
            cd ../../..
            echo "FILE=$FILENAME.zip" >> $GITHUB_ENV
          fi

      - name: Dispatch / Release
        env:
          GH_TOKEN: ${{{{ secrets.GH_PAT }}}}
        run: |
          if [ -z "$GH_TOKEN" ]; then
            echo "GH_PAT secret not found. Skipping release step."
            exit 0
          fi
          {dispatch_logic}
"""
    with open(os.path.join(workflow_dir, "build.yml"), "w") as f:
        f.write(workflow_content)
    
    run("git add .", cwd=repo_path)
    run("git commit -m 'feat: implement consolidated build structure and naming conventions'", cwd=repo_path)
    print(f"Pushing {repo_name}...")
    res = run("git push", cwd=repo_path)
    if res.returncode != 0:
        print(f"Push failed for {repo_name}: {res.stderr}")

# Cleanup
if os.path.exists(askpass_path):
    os.remove(askpass_path)
print("Fleet consolidation complete!")

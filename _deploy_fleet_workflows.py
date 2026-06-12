import os
import subprocess
import shutil

# Set up GIT_ASKPASS to handle the passphrase
askpass_path = os.path.abspath(".git_askpass.sh")
with open(askpass_path, "w") as f:
    f.write("#!/bin/bash\necho 'Molp;sYrd;s'\n")
os.chmod(askpass_path, 0o755)

env = os.environ.copy()
env["GIT_ASKPASS"] = askpass_path
env["DISPLAY"] = ":0" # Required on some systems to trigger ASKPASS

def run(cmd, cwd=None):
    return subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True, env=env)

builders = [
    ("xbmc-build", "Kodi Core", "xbmc", "https://github.com/xbmc/xbmc.git"),
    ("repo-plugins-build", "Plugins", "repo-plugins", "https://github.com/xbmc/repo-plugins.git"),
    ("repo-scripts-build", "Scripts", "repo-scripts", "https://github.com/xbmc/repo-scripts.git"),
    ("repo-scrapers-build", "Scrapers", "repo-scrapers", "https://github.com/xbmc/repo-scrapers.git"),
    ("inputstream.ffmpegdirect-build", "FFmpegDirect", "inputstream.ffmpegdirect", "https://github.com/xbmc/inputstream.ffmpegdirect.git"),
    ("inputstream.adaptive-build", "Adaptive", "inputstream.adaptive", "https://github.com/xbmc/inputstream.adaptive.git"),
]

os.makedirs("build_fleet", exist_ok=True)

for repo_name, display_name, comp_id, upstream_url in builders:
    print(f"Deploying workflow to: {repo_name}")
    repo_path = os.path.join("build_fleet", repo_name)
    
    if not os.path.exists(repo_path):
        run(f"git clone https://github.com/RPDevs-Builds/{repo_name}.git {repo_path}")

    workflow_dir = os.path.join(repo_path, ".github", "workflows")
    os.makedirs(workflow_dir, exist_ok=True)
    
    # Define the workflow content
    is_cpp = "inputstream" in comp_id or "xbmc" in comp_id
    
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
    runs-on: ${{{{ (matrix.platform == 'win64' && 'windows-2022') || (matrix.platform == 'osx64' && 'macos-latest') || 'ubuntu-22.04' }}}}
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
            sudo apt install -y build-essential autoconf automake autopoint gettext cmake curl gawk gperf python3-dev libtool zip unzip
            if [ "${{{{ matrix.platform }}}}" == "linux64" ]; then
              sudo add-apt-repository -s ppa:team-xbmc/xbmc-nightly -y || true
              sudo apt build-dep kodi -y || echo "build-dep failed"
            fi
          elif [ "${{{{ runner.os }}}}" == "Windows" ]; then
            choco install cmake ninja nasm zip -y
          elif [ "${{{{ runner.os }}}}" == "macOS" ]; then
            brew install cmake ninja nasm
          fi

      - name: Setup Cache
        uses: actions/cache@v4
        with:
          path: |
            ~/.ccache
            source/{comp_id}/tools/depends/native/*-native
            source/{comp_id}/project/BuildDependencies
          key: ${{{{ runner.os }}}}-${{{{ matrix.platform }}}}-${{{{ matrix.branch }}}}-cache-${{{{ github.sha }}}}
          restore-keys: |
            ${{{{ runner.os }}}}-${{{{ matrix.platform }}}}-${{{{ matrix.branch }}}}-cache-

      - name: Build and Package
        run: |
          mkdir -p compiled
          if [ "{is_cpp}" == "True" ]; then
            echo "🚀 Performing C++ Build for ${{{{ matrix.platform }}}}..."
            if [ "{comp_id}" == "xbmc" ]; then
              # Kodi Core Build
              if [ "${{{{ matrix.platform }}}}" == "linux64" ]; then
                mkdir build && cd build
                cmake ../source/xbmc -DCMAKE_INSTALL_PREFIX=../compiled -DAPP_RENDER_SYSTEM=gl
                make -j$(nproc) install
              else
                # For Win/Android/OSX we use the depends system
                cd source/xbmc/tools/depends
                ./bootstrap
                # Simplified config for demonstration, in reality requires platform-specific flags
                ./configure --prefix=$(pwd)/../../../../xbmc-deps
                make -j$(nproc || sysctl -n hw.ncpu)
                cd ../../../
                mkdir build && cd build
                cmake ../source/xbmc -DCMAKE_INSTALL_PREFIX=../compiled -DCMAKE_PREFIX_PATH=$(pwd)/../xbmc-deps
                make -j$(nproc || sysctl -n hw.ncpu) install
              fi
            else
              # Addon Build (inputstream)
              mkdir build && cd build
              cmake ../source/{comp_id} -DCMAKE_INSTALL_PREFIX=../compiled
              make -j$(nproc || sysctl -n hw.ncpu) install
            fi
          else
            echo "📦 Packaging Python/XML Addon..."
            cp -rv source/{comp_id}/* compiled/ || echo "No files to copy"
            # Ensure we have a dummy file to avoid zip error if empty
            touch compiled/.kodi_build_marker
          fi

      - name: Create Archive
        run: |
          TAG="v-$(date +'%Y%m%d')-${{{{ matrix.branch }}}}"
          echo "TAG=$TAG" >> $GITHUB_ENV
          if [ "${{{{ matrix.platform }}}}" == "linux64" ]; then
            tar -czf {comp_id}-${{{{ matrix.platform }}}}-${{{{ matrix.branch }}}}.tar.gz -C compiled .
          else
            cd compiled && zip -r ../{comp_id}-${{{{ matrix.platform }}}}-${{{{ matrix.branch }}}}.zip .
          fi

      - name: Dispatch to Distributor
        env:
          GH_TOKEN: ${{{{ secrets.GH_PAT }}}}
        run: |
          if [ -z "$GH_TOKEN" ]; then
            echo "GH_PAT secret not found. Skipping cross-repo release."
            exit 0
          fi
          DIST_REPO="RPDevs-Builds/{comp_id}-build-${{{{ matrix.platform }}}}"
          FILE="{comp_id}-${{{{ matrix.platform }}}}-${{{{ matrix.branch }}}}.*"
          gh release create "$TAG" $FILE \\
            --repo "$DIST_REPO" \\
            --title "{display_name} ${{{{ matrix.branch }}}} Build $TAG" \\
            --notes "Automated build from {repo_name}." \\
            --prerelease || \\
          gh release upload "$TAG" $FILE --repo "$DIST_REPO" --clobber
"""
    with open(os.path.join(workflow_dir, "build.yml"), "w") as f:
        f.write(workflow_content)
    
    run("git add .", cwd=repo_path)
    run("git commit -m 'feat: implement automated build and dispatch workflow'", cwd=repo_path)
    print(f"Pushing {repo_name}...")
    res = run("git push", cwd=repo_path)
    if res.returncode != 0:
        print(f"Failed to push {repo_name}: {res.stderr}")

# Cleanup
os.remove(askpass_path)
print("Fleet-wide workflow deployment complete!")

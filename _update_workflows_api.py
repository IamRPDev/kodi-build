import os
import subprocess
import base64
import json

builders = [
    ("xbmc-build", "Kodi Core", "xbmc", True),
    ("repo-plugins-build", "Plugins", "repo-plugins", False),
    ("repo-scripts-build", "Scripts", "repo-scripts", False),
    ("repo-scrapers-build", "Scrapers", "repo-scrapers", False),
    ("inputstream.ffmpegdirect-build", "FFmpegDirect", "inputstream.ffmpegdirect", False),
    ("inputstream.adaptive-build", "Adaptive", "inputstream.adaptive", False),
]

def update_workflow(repo_name, display_name, comp_id, is_core):
    print(f"Updating workflow for: {repo_name}")
    is_cpp = "inputstream" in comp_id or is_core
    is_cpp_js = "true" if is_cpp else "false"
    
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
            --repo "RPDevs-Builds/{repo_name}" \\
            --title "{display_name} ${{{{ matrix.branch }}}} Build $TAG" \\
            --notes "Automated build for ${{{{ matrix.platform }}}}." \\
            --prerelease || \\
          gh release upload "$TAG" $FILE --repo "RPDevs-Builds/{repo_name}" --clobber
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
    runs-on: ${{{{ (matrix.platform == 'osx64' && 'macos-latest') || ({is_cpp_js} && fromJSON('["self-hosted", "linux64"]')) || fromJSON('["self-hosted", "lightweight"]') }}}}
    defaults:
      run:
        shell: bash
    steps:
      - name: Environment Validation (Pre-Flight)
        run: |
          echo "🔍 Running pre-flight checks..."
          if [[ "${{{{ matrix.platform }}}}" != "osx64" ]]; then
            ccache -s || echo "⚠️ ccache not available or failing"
            gh auth status || echo "⚠️ gh cli auth issue"
          fi
          if [[ "${{{{ matrix.platform }}}}" == "android-arm64" ]]; then
            ls -ld /opt/android-sdk/ndk/25.2.9519653 || exit 1
          fi

      - name: Checkout Source
        uses: actions/checkout@v4
        with:
          repository: xbmc/{comp_id}
          ref: ${{{{ matrix.branch == 'Piers' && ('{comp_id}' == 'inputstream.ffmpegdirect' || '{comp_id}' == 'inputstream.adaptive') && 'Piers' || (matrix.branch == 'Piers' && 'master' || 'Omega') }}}}
          path: source/{comp_id}
          fetch-depth: 1

      - name: Install System Dependencies
        if: ${{{{ matrix.platform == 'osx64' }}}}
        run: |
          brew install cmake ninja nasm gettext coreutils groff

      - name: Build and Package
        run: |
          # Clean previous artifacts for self-hosted consistency
          rm -rf build xbmc-deps compiled
          
          # Get Version for directory structure
          if [ -f source/{comp_id}/version.txt ]; then
            VERSION=$(grep "VERSION_CODE" source/{comp_id}/version.txt | awk '{{print $2}}')
          else
            VERSION="v-$(date +'%Y%m%d')"
          fi
          echo "VERSION=$VERSION" >> $GITHUB_ENV
          
          # Target Directory: ./compiled/os/version/
          OUT_DIR="${{{{ github.workspace }}}}/compiled/${{{{ matrix.platform }}}}/$VERSION"
          mkdir -p "$OUT_DIR"
          echo "OUT_DIR=$OUT_DIR" >> $GITHUB_ENV

          if [ "{is_cpp}" == "True" ]; then
            echo "🚀 Performing C++ Build for ${{{{ matrix.platform }}}}..."
            if [ "{comp_id}" == "xbmc" ]; then
              if [ "${{{{ matrix.platform }}}}" == "linux64" ]; then
                mkdir build && cd build
                cmake ${{{{ github.workspace }}}}/source/xbmc -DCMAKE_INSTALL_PREFIX="$OUT_DIR" -DAPP_RENDER_SYSTEM=gl \\
                  -DENABLE_INTERNAL_FFMPEG=ON -DENABLE_INTERNAL_EXIV2=ON -DENABLE_INTERNAL_DAV1D=ON \\
                  -DENABLE_INTERNAL_FSTRCMP=ON -DENABLE_INTERNAL_FLATBUFFERS=ON -DENABLE_INTERNAL_UDFREAD=ON \\
                  -DENABLE_INTERNAL_SPDLOG=ON -DENABLE_INTERNAL_FMT=ON -DENABLE_INTERNAL_NLOHMANNJSON=ON \\
                  -DENABLE_INTERNAL_RAPIDJSON=ON -DENABLE_INTERNAL_CROSSGUID=ON -DENABLE_INTERNAL_TAGLIB=ON \\
                  -DENABLE_INTERNAL_LZO2=ON -DENABLE_INTERNAL_PCRE2=ON -DENABLE_INTERNAL_TINYXML2=ON \\
                  -DENABLE_INTERNAL_SQLITE3=ON -DENABLE_INTERNAL_CURL=ON -DENABLE_INTERNAL_ASS=ON \\
                  -DENABLE_INTERNAL_LCMS2=ON -DENABLE_INTERNAL_PLIST=ON
                make -j$(nproc || sysctl -n hw.ncpu) install
              elif [ "${{{{ matrix.platform }}}}" == "win64" ]; then
                echo "⚠️ Windows Core build via depends is not supported on Linux. Skipping."
                exit 0
              else
                # Download pre-compiled depends or fallback to cross-compilation
                echo "⬇️ Downloading Pre-compiled Depends..."
                DEPENDS_BRANCH="${{{{ matrix.branch == 'Piers' && 'master' || 'Omega' }}}}"
                TAG="depends-${{{{ matrix.platform }}}}-$DEPENDS_BRANCH"
                gh release download "$TAG" --repo "RPDevs-Builds/kodi-build" --pattern "depends-${{{{ matrix.platform }}}}.tar.gz" --dir . || echo "⚠️ Pre-compiled depends not found. Falling back to build..."
                
                if [ -f "depends-${{{{ matrix.platform }}}}.tar.gz" ]; then
                  echo "✅ Extracting Depends..."
                  mkdir -p ${{{{ github.workspace }}}}/xbmc-deps
                  tar -xzf depends-${{{{ matrix.platform }}}}.tar.gz -C ${{{{ github.workspace }}}}/xbmc-deps
                else
                  cd source/xbmc/tools/depends
                  ./bootstrap
                  case "${{{{ matrix.platform }}}}" in
                    android-arm64) export CONFIG_FLAGS="--host=aarch64-linux-android --with-sdk-path=/opt/android-sdk --with-ndk-path=/opt/android-sdk/ndk/25.2.9519653" ;;
                    osx64) 
                      export CONFIG_FLAGS="--with-platform=macos"
                      export PATH="$(brew --prefix gettext)/bin:$(brew --prefix coreutils)/libexec/gnubin:$PATH"
                      ;;
                  esac
                  ./configure --prefix=${{{{ github.workspace }}}}/xbmc-deps $CONFIG_FLAGS
                  make -j$(nproc || sysctl -n hw.ncpu)
                fi
                cd ${{{{ github.workspace }}}}
                mkdir build && cd build
                cmake ${{{{ github.workspace }}}}/source/xbmc -DCMAKE_INSTALL_PREFIX="$OUT_DIR" -DCMAKE_PREFIX_PATH=${{{{ github.workspace }}}}/xbmc-deps
                make -j$(nproc || sysctl -n hw.ncpu) install
              fi
            else
              # Addon C++ Build
              if [ "${{{{ matrix.platform }}}}" == "win64" ]; then
                 echo "⚠️ Windows cross-compiling addons not fully supported yet. Skipping."
                 exit 0
              fi
              if [ "${{{{ matrix.platform }}}}" != "linux64" ]; then
                echo "⬇️ Downloading Pre-compiled Depends for Addon..."
                DEPENDS_BRANCH="${{{{ matrix.branch == 'Piers' && 'master' || 'Omega' }}}}"
                TAG="depends-${{{{ matrix.platform }}}}-$DEPENDS_BRANCH"
                gh release download "$TAG" --repo "RPDevs-Builds/kodi-build" --pattern "depends-${{{{ matrix.platform }}}}.tar.gz" --dir . || echo "⚠️ Pre-compiled depends not found."
                
                if [ -f "depends-${{{{ matrix.platform }}}}.tar.gz" ]; then
                  echo "✅ Extracting Depends..."
                  mkdir -p ${{{{ github.workspace }}}}/xbmc-deps
                  tar -xzf depends-${{{{ matrix.platform }}}}.tar.gz -C ${{{{ github.workspace }}}}/xbmc-deps
                else
                  echo "⚠️ Cannot cross-compile addon without KodiConfig.cmake from depends. Skipping."
                  exit 0
                fi
              fi
              mkdir build && cd build
              cmake ${{{{ github.workspace }}}}/source/{comp_id} -DCMAKE_INSTALL_PREFIX="$OUT_DIR" -DCMAKE_PREFIX_PATH=${{{{ github.workspace }}}}/xbmc-deps
              make -j$(nproc || sysctl -n hw.ncpu) install
            fi
          else
            echo "📦 Packaging Python/XML Addon..."
            cp -rv source/{comp_id}/* "$OUT_DIR/"
            touch "$OUT_DIR/.kodi_build_marker"
          fi

      - name: Create Archive
        run: |
          if [ ! -d "$OUT_DIR" ] || [ -z "$(ls -A $OUT_DIR)" ]; then
            echo "Empty directory, skipping archive."
            exit 0
          fi
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
          if [ -z "$GH_TOKEN" ] || [ -z "$FILE" ]; then
            echo "GH_PAT secret not found or file missing. Skipping release step."
            exit 0
          fi
          {dispatch_logic}

      - name: Send Status to Hub Aggregator
        if: always()
        env:
          GH_TOKEN: ${{{{ secrets.GH_PAT }}}}
        run: |
          gh api -X POST repos/RPDevs-Builds/kodi-build/dispatches \\
            -H "Accept: application/vnd.github.v3+json" \\
            -f event_type="fleet_status_update" \\
            -F client_payload[repository]="{repo_name}" \\
            -F client_payload[status]="${{{{ job.status }}}}" \\
            -F client_payload[conclusion]="${{{{ job.status }}}}" \\
            -F client_payload[url]="$GITHUB_SERVER_URL/$GITHUB_REPOSITORY/actions/runs/$GITHUB_RUN_ID"
"""
    # Use gh api to put the file content
    content_b64 = base64.b64encode(workflow_content.encode()).decode()
    
    # Get SHA using gh api and jq directly in shell
    sha_cmd = f"gh api repos/RPDevs-Builds/{repo_name}/contents/.github/workflows/build.yml --jq .sha"
    res_sha = subprocess.run(sha_cmd, shell=True, capture_output=True, text=True)
    
    data = {
        "message": "feat: update workflow for self-hosted runners",
        "content": content_b64
    }
    if res_sha.returncode == 0 and res_sha.stdout.strip():
        data["sha"] = res_sha.stdout.strip()
    
    # Write JSON to temp file
    with open("payload.json", "w") as f:
        json.dump(data, f)
        
    cmd = f"gh api -X PUT repos/RPDevs-Builds/{repo_name}/contents/.github/workflows/build.yml --input payload.json"
    subprocess.run(cmd, shell=True)
    if os.path.exists("payload.json"):
        os.remove("payload.json")

for repo_name, display_name, comp_id, is_core in builders:
    update_workflow(repo_name, display_name, comp_id, is_core)

print("Fleet workflows updated via API!")

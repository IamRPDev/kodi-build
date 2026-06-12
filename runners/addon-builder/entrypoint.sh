#!/bin/bash
# Registration Logic
# GH_OWNER is always the Org/User
# GH_TOKEN is required
# If GH_REPOSITORY is set, register to repo. Otherwise register to Org.

if [ -n "${GH_REPOSITORY}" ]; then
    echo "Registering to Repository: ${GH_OWNER}/${GH_REPOSITORY}"
    REG_TOKEN=$(curl -sX POST -H "Authorization: token ${GH_TOKEN}" https://api.github.com/repos/${GH_OWNER}/${GH_REPOSITORY}/actions/runners/registration-token | jq -r .token)
    URL="https://github.com/${GH_OWNER}/${GH_REPOSITORY}"
else
    echo "Registering to Organization: ${GH_OWNER}"
    REG_TOKEN=$(curl -sX POST -H "Authorization: token ${GH_TOKEN}" https://api.github.com/orgs/${GH_OWNER}/actions/runners/registration-token | jq -r .token)
    URL="https://github.com/${GH_OWNER}"
fi

./config.sh --url ${URL} --token ${REG_TOKEN} --name "${RUNNER_NAME:-custom-runner}" --labels "${RUNNER_LABELS:-linux64}" --unattended --replace

cleanup() {
    echo "Removing runner..."
    if [ -n "${GH_REPOSITORY}" ]; then
        REG_TOKEN=$(curl -sX POST -H "Authorization: token ${GH_TOKEN}" https://api.github.com/repos/${GH_OWNER}/${GH_REPOSITORY}/actions/runners/registration-token | jq -r .token)
    else
        REG_TOKEN=$(curl -sX POST -H "Authorization: token ${GH_TOKEN}" https://api.github.com/orgs/${GH_OWNER}/actions/runners/registration-token | jq -r .token)
    fi
    ./config.sh remove --token ${REG_TOKEN}
}

trap 'cleanup; exit 130' INT
trap 'cleanup; exit 143' TERM

./run.sh & wait $!

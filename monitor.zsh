#!/bin/zsh

# Kodi Build Fleet Monitor (Ultra-Robust Zsh Version)
# Requirements: gh, jq

builders=(
    "xbmc-build|Kodi Core"
    "repo-plugins-build|Plugins"
    "repo-scripts-build|Scripts"
    "repo-scrapers-build|Scrapers"
    "inputstream.ffmpegdirect-build|FFmpegDirect"
    "inputstream.adaptive-build|Adaptive"
)

# Colors
GREEN='%F{green}'
RED='%F{red}'
YELLOW='%F{yellow}'
BLUE='%F{blue}'
CYAN='%F{cyan}'
NC='%f' 
BOLD='%B'
REG='%b'

refresh_interval=15

fetch_status() {
    local repo_entry=$1
    local repo=$(echo $repo_entry | cut -d'|' -f1)
    local name=$(echo $repo_entry | cut -d'|' -f2)
    
    local run_data=$(gh run list --repo RPDevs-Builds/$repo --workflow=build.yml --limit 1 --json databaseId,status,conclusion,displayTitle,createdAt,headBranch 2>/dev/null)
    
    if [[ -z "$run_data" || "$run_data" == "[]" ]]; then
        echo "$name|⚪|N/A|· · · ·|N/A|N/A"
        return
    fi

    local id=$(echo $run_data | jq -r '.[0].databaseId')
    local r_status=$(echo $run_data | jq -r '.[0].status')
    local conclusion=$(echo $run_data | jq -r '.[0].conclusion')
    local branch=$(echo $run_data | jq -r '.[0].headBranch')

    local jobs_data=$(gh run view --repo RPDevs-Builds/$repo $id --json jobs 2>/dev/null)
    
    # Platform Matrix Logic
    local p_linux=$(echo $jobs_data | jq -r '.jobs[] | select(.name | contains("linux64")) | "\(.status)|\(.conclusion)"')
    local p_win=$(echo $jobs_data | jq -r '.jobs[] | select(.name | contains("win64")) | "\(.status)|\(.conclusion)"')
    local p_android=$(echo $jobs_data | jq -r '.jobs[] | select(.name | contains("android")) | "\(.status)|\(.conclusion)"')
    local p_osx=$(echo $jobs_data | jq -r '.jobs[] | select(.name | contains("osx64")) | "\(.status)|\(.conclusion)"')

    format_job() {
        local info=$1
        [[ -z "$info" || "$info" == "|" ]] && echo "·" && return
        local s=$(echo $info | cut -d'|' -f1)
        local c=$(echo $info | cut -d'|' -f2)
        if [[ "$s" == "completed" ]]; then
            [[ "$c" == "success" ]] && echo "${GREEN}●${NC}" || echo "${RED}●${NC}"
        elif [[ "$s" == "in_progress" ]]; then
            echo "${BLUE}◑${NC}"
        else
            echo "${YELLOW}◌${NC}"
        fi
    }

    local m_l=$(format_job "$p_linux")
    local m_w=$(format_job "$p_win")
    local m_a=$(format_job "$p_android")
    local m_o=$(format_job "$p_osx")
    local plat_summary="$m_l $m_w $m_a $m_o"

    # Step Logic
    local current_step=$(echo $jobs_data | jq -r '.jobs[] | select(.name != "setup-matrix") | .steps[] | select(.status != "completed") | .name' | head -n 1)
    [[ "$current_step" == "null" || -z "$current_step" ]] && current_step=$(echo $jobs_data | jq -r '.jobs[] | select(.name != "setup-matrix") | .steps[-1].name' | head -n 1)
    [[ "$current_step" == "null" ]] && current_step="Ready"

    # Stat Icon
    local icon="🔄"
    [[ "$r_status" == "completed" && "$conclusion" == "success" ]] && icon="✅"
    [[ "$r_status" == "completed" && "$conclusion" == "failure" ]] && icon="❌"
    [[ "$r_status" == "queued" ]] && icon="⏳"

    echo "$name|$icon|$branch|$plat_summary|$current_step|$r_status"
}

while true; do
    clear
    print -P "${BOLD}================================================================================${NC}"
    print -P "🚢 ${BOLD}KODI BUILD FLEET MONITOR${NC} - $(date +'%H:%M:%S') | ${CYAN}L${NC}inux ${CYAN}W${NC}in ${CYAN}A${NC}ndroid ${CYAN}O${NC}SX"
    print -P "${BOLD}================================================================================${NC}"
    print -P "${BOLD}${(r:15:)Component} | Stat | ${(r:8:)Branch} | ${(r:8:)Matrix} | Active/Last Step${NC}"
    print -P "--------------------------------------------------------------------------------"

    tmp_file=$(mktemp)
    for entry in "${builders[@]}"; do
        fetch_status "$entry" >> "$tmp_file" &
    done
    wait

    while IFS= read -r line; do
        IFS='|' read -r name icon branch matrix step r_status <<< "$line"
        print -P "${(r:15:)name} |  $icon  | ${(r:8:)branch} | $matrix | ${step:0:30}"
    done < "$tmp_file"
    rm "$tmp_file"

    print -P "${BOLD}--------------------------------------------------------------------------------${NC}"
    print -P "Status Key: ${GREEN}● Success${NC} | ${RED}● Failure${NC} | ${BLUE}◑ In-Progress${NC} | ${YELLOW}◌ Queued${NC} | · N/A"
    echo "Auto-refresh in ${refresh_interval}s. Press [ENTER] to refresh now."
    
    read -t $refresh_interval
done

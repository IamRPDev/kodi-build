import subprocess
import time
import os
import sys
import select

builders = [
    ("xbmc-build", "Kodi Core"),
    ("repo-plugins-build", "Plugins"),
    ("repo-scripts-build", "Scripts"),
    ("repo-scrapers-build", "Scrapers"),
    ("inputstream.ffmpegdirect-build", "FFmpegDirect"),
    ("inputstream.adaptive-build", "Adaptive"),
]

def get_status(repo):
    try:
        # Get the latest run
        cmd = f"gh run list --repo RPDevs-Builds/{repo} --workflow=build.yml --limit 1 --json status,conclusion,displayTitle"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            import json
            data = json.loads(result.stdout)
            if data:
                run = data[0]
                status = run['status']
                conclusion = run['conclusion']
                title = run['displayTitle']
                
                # Format output
                icon = "🟡" # default running
                if status == "completed":
                    if conclusion == "success":
                        icon = "✅"
                    elif conclusion == "failure":
                        icon = "❌"
                    else:
                        icon = "🔘" # cancelled/skipped
                
                return f"{icon} {status.capitalize()}: {title[:30]}"
            else:
                return "⚪ No runs found"
        else:
            return "❓ Error fetching"
    except Exception as e:
        return f"💀 Error: {str(e)}"

def main():
    refresh_interval = 30
    while True:
        os.system('clear')
        print("="*60)
        print(f"🚢 KODI BUILD FLEET MONITOR - {time.strftime('%H:%M:%S')}")
        print("="*60)
        print(f"{'Component':<25} | {'Latest Build Status'}")
        print("-" * 60)
        
        for repo, name in builders:
            status = get_status(repo)
            print(f"{name:<25} | {status}")
            
        print("="*60)
        print(f"Auto-refreshing every {refresh_interval}s.")
        print("Press ENTER to refresh manually, or Ctrl+C to quit.")
        
        # Wait for input with timeout (manual refresh)
        try:
            rlist, _, _ = select.select([sys.stdin], [], [], refresh_interval)
            if rlist:
                sys.stdin.readline() # Consume the input
                print("🔄 Manual refresh triggered...")
                continue # Jump back to top of loop
        except KeyboardInterrupt:
            print("\n👋 Monitoring stopped.")
            break

if __name__ == "__main__":
    main()

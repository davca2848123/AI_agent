import os
import subprocess
import sys

# Add parent directory to path to import config_secrets
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    import config_secrets
except ImportError:
    print("Error: config_secrets.py not found!")
    sys.exit(1)

REPO_URL = "https://github.com/davca2848123/AI_agent.git"
TOKEN = config_secrets.GITHUB_TOKEN

def run_git(args):
    result = subprocess.run(["git"] + args, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Git command failed: git {' '.join(args)}\n{result.stderr}")
        return False
    return True

def fix_git():
    print(f"Working directory: {os.getcwd()}")
    
    if not os.path.exists(".git"):
        print("Initializing git repository...")
        if not run_git(["init"]): return
    else:
        print("Git repository already initialized.")
    
    # Config
    print("Configuring git user...")
    run_git(["config", "user.email", "agent@rpi.ai"])
    run_git(["config", "user.name", "RPi Agent"])
    
    # Remote
    # Check if remote exists
    res = subprocess.run(["git", "remote", "get-url", "origin"], capture_output=True)
    if res.returncode != 0:
        print("Adding remote origin...")
        if not run_git(["remote", "add", "origin", REPO_URL]): return
    else:
        print("Remote origin already exists.")

    # Set remote URL with token for authentication
    if TOKEN:
        print("Setting up authentication with token...")
        auth_url = REPO_URL.replace("https://", f"https://{TOKEN}@")
        if not run_git(["remote", "set-url", "origin", auth_url]): return
    else:
        print("WARNING: No GITHUB_TOKEN found in config_secrets.py")
    
    print("Git configuration fixed.")
    
    # Try to fetch
    print("Testing connection (git fetch)...")
    if run_git(["fetch"]):
        print("Connection successful!")
    else:
        print("Connection failed. Check your token in config_secrets.py")

if __name__ == "__main__":
    # Change to project root
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    fix_git()

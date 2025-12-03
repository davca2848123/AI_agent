"""GitHub Auto-Release Script with Versioning

Automatically creates GitHub releases with date-based versioning (e.g., 2025.12.3.1)
and uploads project as ZIP asset. Runs on agent startup.
"""

import os
import subprocess
import datetime
import zipfile
import logging
from github import Github

logger = logging.getLogger(__name__)

# Blacklist - files and folders to exclude from Git and ZIP
BLACKLIST = [
    ".git",
    "__pycache__",
    "venv",
    ".env",
    ".DS_Store",
    "*.pyc",
    "*.pyo",
    "*.log",
    "*.db",
    "*.db-shm",
    "*.db-wal",
    "config_secrets.py",
    "agent.log",
    "agent_tools.log",
    "agent_memory.db",
    "tool_stats.json",
    "tool_timestamps.json",
    ".agent_state.json",
    ".restart_flag",
    ".shutdown_incomplete",
    "backup/",
    "tests/",
    "workspace/",
    "models/",
    "release.zip",
    "boredom_topics.json.test_backup"
]

def update_gitignore():
    """Ensures blacklisted items are in .gitignore"""
    gitignore_path = ".gitignore"
    existing_rules = []
    
    if os.path.exists(gitignore_path):
        with open(gitignore_path, "r", encoding='utf-8') as f:
            existing_rules = [line.strip() for line in f.readlines()]
    
    with open(gitignore_path, "a", encoding='utf-8') as f:
        for item in BLACKLIST:
            # Skip .git itself (doesn't belong in .gitignore)
            if item == ".git":
                continue
            if item not in existing_rules:
                f.write(f"\n{item}")
    
    logger.info("Updated .gitignore with blacklist items")

def git_push_changes(branch="main"):
    """Performs git add, commit, and push"""
    try:
        # Check if there are changes
        result = subprocess.run(["git", "status", "--porcelain"], 
                              capture_output=True, text=True, check=True)
        
        if not result.stdout.strip():
            logger.info("No changes to commit")
            return True
        
        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "-m", f"Auto-release {datetime.date.today()}"], check=False)
        subprocess.run(["git", "push", "origin", branch], check=True)
        logger.info("Changes pushed to GitHub")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Git operation failed: {e}")
        return False

def get_new_version(repo):
    """Calculates version based on today's date and existing tags"""
    now = datetime.datetime.now()
    # Format without leading zeros (2025.12.3) as requested
    base_ver = f"{now.year}.{now.month}.{now.day}"
    
    try:
        tags = list(repo.get_tags())
        existing_versions = [t.name for t in tags if t.name.startswith(base_ver)]
    except Exception as e:
        logger.warning(f"Could not fetch tags: {e}, using base version")
        return base_ver

    if not existing_versions:
        return base_ver
    
    # Find highest suffix
    max_suffix = 0
    has_base = False
    
    for v in existing_versions:
        if v == base_ver:
            has_base = True
            continue
        
        # Process version like 2025.12.3.1
        parts = v.replace(base_ver + ".", "")
        if parts.isdigit():
            suffix = int(parts)
            if suffix > max_suffix:
                max_suffix = suffix
    
    if not has_base and max_suffix == 0:
        return base_ver
    
    return f"{base_ver}.{max_suffix + 1}"

def should_exclude(path):
    """Check if path should be excluded based on blacklist"""
    for pattern in BLACKLIST:
        if pattern.endswith('/'):
            # Directory pattern
            if pattern[:-1] in path.split(os.sep):
                return True
        elif pattern.startswith('*'):
            # Extension pattern
            if path.endswith(pattern[1:]):
                return True
        else:
            # Exact match or in path
            if pattern in path or os.path.basename(path) == pattern:
                return True
    return False

def zip_folder(output_filename="release.zip"):
    """Packages current folder into ZIP, excludes blacklist"""
    logger.info("Packaging files into ZIP...")
    with zipfile.ZipFile(output_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk("."):
            # Filter directories in-place (don't traverse excluded dirs)
            dirs[:] = [d for d in dirs if not should_exclude(os.path.join(root, d))]
            
            for file in files:
                file_path = os.path.join(root, file)
                
                if should_exclude(file_path):
                    continue
                
                zipf.write(file_path, os.path.relpath(file_path, "."))
    
    logger.info(f"Created {output_filename}")
    return output_filename

def create_release(github_token, repo_name, branch="main"):
    """Main function to create GitHub release"""
    try:
        # 1. GitHub API login
        g = Github(github_token)
        try:
            repo = g.get_repo(repo_name)
        except Exception as e:
            logger.error(f"Cannot find repository '{repo_name}'. Check name and token.")
            return False

        # 2. Update .gitignore and push
        update_gitignore()
        
        # Update remote with token to ensure push works
        auth_url = f"https://{github_token}@github.com/{repo_name}.git"
        try:
            subprocess.run(["git", "remote", "set-url", "origin", auth_url], check=True)
        except subprocess.CalledProcessError:
            try:
                subprocess.run(["git", "remote", "add", "origin", auth_url], check=True)
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to configure git remote: {e}")

        if not git_push_changes(branch):
            logger.warning("Git push failed, continuing with release...")

        # 3. Calculate version
        new_version = get_new_version(repo)
        logger.info(f"New version will be: {new_version}")

        # 4. Create Release
        release = repo.create_git_release(
            tag=new_version,
            name=new_version,
            message=f"Automatic release from {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}",
            draft=False,
            prerelease=False
        )
        logger.info(f"Release {new_version} created")

        # 5. Upload ZIP asset
        zip_name = "project_source.zip"
        zip_folder(zip_name)
        
        logger.info("Uploading ZIP to release...")
        release.upload_asset(zip_name, label="Source Code (Project)")
        
        # Cleanup
        if os.path.exists(zip_name):
            os.remove(zip_name)
        
        logger.info("GitHub release completed successfully!")
        return True

    except Exception as e:
        logger.error(f"Error creating release: {e}")
        return False

if __name__ == "__main__":
    # Test run
    import config_secrets
    create_release(
        github_token=config_secrets.GITHUB_TOKEN,
        repo_name="davca2848123/AI_agent"
    )

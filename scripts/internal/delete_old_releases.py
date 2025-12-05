import argparse
import requests
import datetime
import os
import sys
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Config
REPO_OWNER = "davca2848123"
REPO_NAME = "AI_agent"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

def delete_old_releases(days=2, dry_run=False):
    if not GITHUB_TOKEN:
        logger.error("GITHUB_TOKEN not found in environment variables.")
        return

    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases"
    
    try:
        # Get all releases
        response = requests.get(url, headers=headers, params={"per_page": 100})
        response.raise_for_status()
        releases = response.json()
        
        logger.info(f"Found {len(releases)} total releases.")
        
        now = datetime.datetime.now(datetime.timezone.utc)
        cutoff_date = now - datetime.timedelta(days=days)
        
        deleted_count = 0
        
        for release in releases:
            # Parse date
            created_at_str = release["created_at"]
            created_at = datetime.datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
            
            if created_at < cutoff_date:
                release_id = release["id"]
                tag_name = release["tag_name"]
                
                logger.info(f"Found old release: {tag_name} (Created: {created_at_str})")
                
                if not dry_run:
                    # Delete release
                    del_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/{release_id}"
                    del_resp = requests.delete(del_url, headers=headers)
                    
                    if del_resp.status_code == 204:
                        logger.info(f"✅ Deleted release {tag_name}")
                        
                        # Delete tag reference
                        tag_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/git/refs/tags/{tag_name}"
                        tag_resp = requests.delete(tag_url, headers=headers)
                        if tag_resp.status_code == 204:
                            logger.info(f"✅ Deleted tag {tag_name}")
                        else:
                            logger.warning(f"⚠️ Failed to delete tag {tag_name}: {tag_resp.status_code}")
                            
                        deleted_count += 1
                    else:
                        logger.error(f"❌ Failed to delete release {tag_name}: {del_resp.status_code} - {del_resp.text}")
                else:
                    logger.info(f"[DRY RUN] Would delete release {tag_name} and tag.")
                    deleted_count += 1
                    
        logger.info(f"Cleanup complete. Deleted {deleted_count} old releases.")
        
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Delete old GitHub releases.")
    parser.add_argument("--days", type=int, default=2, help="Delete releases older than N days (default: 2).")
    parser.add_argument("--dry-run", action="store_true", help="Simulate deletion.")
    
    args = parser.parse_args()
    
    delete_old_releases(args.days, args.dry_run)

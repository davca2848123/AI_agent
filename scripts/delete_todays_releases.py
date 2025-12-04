"""Delete GitHub Releases from Today

This script deletes all releases created today (matching pattern YYYY.M.D.*).
Use this to clean up releases created by the restart loop bug.
"""

import os
import sys
import datetime
from github import Github

def delete_todays_releases(github_token, repo_name):
    """Delete all releases from today."""
    try:
        # Initialize GitHub API
        g = Github(github_token)
        repo = g.get_repo(repo_name)
        
        # Get today's date pattern
        now = datetime.datetime.now()
        today_pattern = f"{now.year}.{now.month}.{now.day}"
        
        print(f"🔍 Searching for releases matching pattern: {today_pattern}.*")
        print(f"📦 Repository: {repo_name}")
        print("=" * 60)
        
        # Get all releases
        releases = list(repo.get_releases())
        todays_releases = [r for r in releases if r.tag_name.startswith(today_pattern)]
        
        if not todays_releases:
            print(f"✅ No releases found for today ({today_pattern})")
            return True
        
        print(f"⚠️  Found {len(todays_releases)} releases from today!")
        print("\nReleases to delete:")
        for r in todays_releases[:10]:  # Show first 10
            print(f"  - {r.tag_name}")
        if len(todays_releases) > 10:
            print(f"  ... and {len(todays_releases) - 10} more")
        
        # Confirm deletion
        print("\n" + "=" * 60)
        response = input(f"❗ Delete ALL {len(todays_releases)} releases? (yes/no): ")
        
        if response.lower() != 'yes':
            print("❌ Deletion cancelled.")
            return False
        
        # Delete releases
        print("\n🗑️  Deleting releases...")
        deleted_count = 0
        failed_count = 0
        
        for i, release in enumerate(todays_releases, 1):
            try:
                tag_name = release.tag_name
                release.delete_release()
                
                # Also delete the tag
                try:
                    ref = repo.get_git_ref(f"tags/{tag_name}")
                    ref.delete()
                except Exception as e:
                    print(f"⚠️  Could not delete tag {tag_name}: {e}")
                
                deleted_count += 1
                if i % 10 == 0 or i == len(todays_releases):
                    print(f"   Progress: {i}/{len(todays_releases)} deleted...")
                    
            except Exception as e:
                print(f"❌ Failed to delete {release.tag_name}: {e}")
                failed_count += 1
        
        print("\n" + "=" * 60)
        print(f"✅ Deletion complete!")
        print(f"   - Deleted: {deleted_count}")
        print(f"   - Failed:  {failed_count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("  GitHub Release Cleanup - Delete Today's Releases")
    print("=" * 60)
    print()
    
    # Load GitHub token from config
    try:
        # Add parent directory to path to import config
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        import config_secrets
        
        github_token = config_secrets.GITHUB_TOKEN
        repo_name = "davca2848123/AI_agent"
        
    except ImportError:
        print("❌ Could not load config_secrets.py")
        print("Please ensure config_secrets.py exists with GITHUB_TOKEN")
        sys.exit(1)
    except AttributeError:
        print("❌ GITHUB_TOKEN not found in config_secrets.py")
        sys.exit(1)
    
    # Run deletion
    success = delete_todays_releases(github_token, repo_name)
    
    if success:
        print("\n✅ Script completed successfully!")
    else:
        print("\n❌ Script failed or was cancelled.")
    
    input("\nPress Enter to exit...")

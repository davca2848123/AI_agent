"""Find GitHub Releases by Date

This script searches for and lists all GitHub releases matching a specific date pattern.
"""

import os
import sys
import datetime
from github import Github, Auth

def find_releases_by_date(github_token, repo_name, year=None, month=None, day=None):
    """Find all releases matching the specified date.
    
    Args:
        github_token: GitHub personal access token
        repo_name: Repository name (owner/repo)
        year: Year to search (YY format, e.g., 25 for 2025). None = current year
        month: Month to search (1-12). None = current month
        day: Day to search (1-31). None = current day
    
    Returns:
        list: Matching release tag names
    """
    try:
        # Initialize GitHub API with new auth method
        auth = Auth.Token(github_token)
        g = Github(auth=auth)
        repo = g.get_repo(repo_name)
        
        # Default to today if not specified
        now = datetime.datetime.now()
        if year is None:
            year = now.year % 100
        if month is None:
            month = now.month
        if day is None:
            day = now.day
        
        # Create search pattern
        search_pattern = f"{year}.{month}.{day}"
        
        print(f"🔍 Searching for releases matching pattern: {search_pattern}*")
        print(f"📦 Repository: {repo_name}")
        print("=" * 60)
        
        # Get all releases
        releases = list(repo.get_releases())
        matching_releases = [r for r in releases if r.tag_name.startswith(search_pattern)]
        
        if not matching_releases:
            print(f"❌ No releases found for date {search_pattern}")
            return []
        
        print(f"✅ Found {len(matching_releases)} release(s):\n")
        
        # Display releases
        for i, release in enumerate(matching_releases, 1):
            created_at = release.created_at.strftime('%Y-%m-%d %H:%M:%S')
            print(f"{i}. Tag: {release.tag_name}")
            print(f"   Name: {release.name}")
            print(f"   Created: {created_at}")
            print(f"   URL: {release.html_url}")
            print()
        
        return [r.tag_name for r in matching_releases]
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return []

if __name__ == "__main__":
    import argparse
    
    print("=" * 60)
    print("  GitHub Release Finder")
    print("=" * 60)
    print()
    
    # Parse arguments
    parser = argparse.ArgumentParser(description='Find GitHub releases by date')
    parser.add_argument('--year', type=int, help='Year (YY format, e.g., 25)')
    parser.add_argument('--month', type=int, help='Month (1-12)')
    parser.add_argument('--day', type=int, help='Day (1-31)')
    args = parser.parse_args()
    
    # Load GitHub token from config
    try:
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
    
    # Find releases
    tags = find_releases_by_date(
        github_token, 
        repo_name,
        year=args.year,
        month=args.month,
        day=args.day
    )
    
    if tags:
        print("=" * 60)
        print(f"✅ Total: {len(tags)} release(s) found")
    
    input("\nPress Enter to exit...")

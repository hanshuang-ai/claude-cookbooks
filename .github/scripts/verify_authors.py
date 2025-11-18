#!/usr/bin/env python3
"""
Verify authors.yaml and registry.yaml integrity:
1. GitHub handles exist
2. Website and avatar URLs are valid
3. All registry.yaml authors are defined in authors.yaml
"""

import yaml
import requests
import sys
from pathlib import Path


def check_github_handle(username):
    """Check if a GitHub handle exists."""
    try:
        response = requests.head(f"https://github.com/{username}", timeout=10, allow_redirects=True)
        if response.status_code == 404:
            return False, "GitHub profile not found"
        elif response.status_code >= 400:
            return False, f"HTTP {response.status_code}"
        return True, None
    except requests.RequestException as e:
        return False, str(e)


def check_url(url):
    """Check if a URL is accessible."""
    # Skip x.com URLs as they block HEAD requests
    if 'x.com' in url:
        return True, "skipped (x.com)"

    try:
        response = requests.head(url, timeout=10, allow_redirects=True)
        if response.status_code >= 400:
            return False, f"HTTP {response.status_code}"
        return True, None
    except requests.RequestException as e:
        return False, str(e)


def main():
    # Load YAML files
    authors_path = Path(__file__).parent.parent.parent / "authors.yaml"
    registry_path = Path(__file__).parent.parent.parent / "registry.yaml"

    with open(authors_path, 'r') as f:
        authors = yaml.safe_load(f)

    with open(registry_path, 'r') as f:
        registry = yaml.safe_load(f)

    failed_handles = []
    failed_urls = []
    missing_authors = []

    # Step 1: Verify GitHub handles
    print("=== Verifying GitHub Handles ===\n")
    for username in authors.keys():
        print(f"Checking GitHub handle: {username}...")
        success, error = check_github_handle(username)
        if not success:
            failed_handles.append(f"{username} ({error})")
            print(f"  ❌ {error}")
        else:
            print(f"  ✓ OK")

    # Step 2: Verify URLs
    print("\n=== Verifying Author URLs ===\n")
    for username, details in authors.items():
        print(f"Checking URLs for {username}...")

        # Check website URL
        if 'website' in details:
            url = details['website']
            success, error = check_url(url)
            if not success:
                failed_urls.append(f"{username}.website: {url} ({error})")
                print(f"  ❌ Website URL: {url} ({error})")
            elif error:
                print(f"  ⊘ Website URL {error}: {url}")
            else:
                print(f"  ✓ Website URL OK: {url}")

        # Check avatar URL
        if 'avatar' in details:
            url = details['avatar']
            success, error = check_url(url)
            if not success:
                failed_urls.append(f"{username}.avatar: {url} ({error})")
                print(f"  ❌ Avatar URL: {url} ({error})")
            elif error:
                print(f"  ⊘ Avatar URL {error}: {url}")
            else:
                print(f"  ✓ Avatar URL OK: {url}")

    # Step 3: Verify registry authors exist in authors.yaml
    print("\n=== Verifying Registry Authors ===\n")
    registry_authors = set()
    for entry in registry:
        if 'authors' in entry:
            for author in entry['authors']:
                registry_authors.add(author)

    print(f"Found {len(registry_authors)} unique authors in registry.yaml")

    for author in sorted(registry_authors):
        if author not in authors:
            missing_authors.append(author)
            print(f"  ❌ Author '{author}' not found in authors.yaml")
        else:
            print(f"  ✓ {author}")

    # Report results
    has_failures = False

    if failed_handles:
        print("\n❌ The following GitHub handles failed verification:")
        for handle in failed_handles:
            print(f"  - {handle}")
        has_failures = True

    if failed_urls:
        print("\n❌ The following URLs failed verification:")
        for url in failed_urls:
            print(f"  - {url}")
        has_failures = True

    if missing_authors:
        print("\n❌ The following authors are in registry.yaml but not in authors.yaml:")
        for author in missing_authors:
            print(f"  - {author}")
        has_failures = True

    if has_failures:
        sys.exit(1)
    else:
        print("\n✓ All verifications passed successfully!")


if __name__ == "__main__":
    main()


#!/usr/bin/env python3
"""
Script to bump version numbers following semantic versioning.
Usage: python scripts/bump_version.py [major|minor|patch]
"""

import argparse
import re
import sys
from pathlib import Path

def update_version_in_file(file_path: Path, old_version: str, new_version: str):
    """Update version in a specific file."""
    content = file_path.read_text()
    
    # Different patterns for different files
    patterns = [
        (r'__version__ = "[^"]*"', f'__version__ = "{new_version}"'),
        (r'version = "[^"]*"', f'version = "{new_version}"'),
        (r'\[(\d+\.\d+\.\d+)\]', f'[{new_version}]'),
    ]
    
    updated = False
    for pattern, replacement in patterns:
        if re.search(pattern, content):
            content = re.sub(pattern, replacement, content)
            updated = True
            break
    
    if updated:
        file_path.write_text(content)
        print(f"Updated {file_path}")
    else:
        print(f"No version pattern found in {file_path}")

def main():
    parser = argparse.ArgumentParser(description="Bump version numbers")
    parser.add_argument("bump_type", choices=["major", "minor", "patch"], 
                       help="Type of version bump")
    args = parser.parse_args()
    
    # Get current version
    version_file = Path("requests_connection_manager/version.py")
    if not version_file.exists():
        print("Version file not found!")
        sys.exit(1)
    
    content = version_file.read_text()
    version_match = re.search(r'__version__ = "([^"]*)"', content)
    if not version_match:
        print("Current version not found!")
        sys.exit(1)
    
    current_version = version_match.group(1)
    
    # Calculate new version
    major, minor, patch = map(int, current_version.split('.'))
    
    if args.bump_type == "major":
        new_version = f"{major + 1}.0.0"
    elif args.bump_type == "minor":
        new_version = f"{major}.{minor + 1}.0"
    else:  # patch
        new_version = f"{major}.{minor}.{patch + 1}"
    
    print(f"Bumping version from {current_version} to {new_version}")
    
    # Update files
    files_to_update = [
        Path("requests_connection_manager/version.py"),
        Path("pyproject.toml"),
    ]
    
    for file_path in files_to_update:
        if file_path.exists():
            update_version_in_file(file_path, current_version, new_version)
    
    print(f"\nVersion bumped to {new_version}")
    print(f"Don't forget to:")
    print(f"1. Update CHANGELOG.md")
    print(f"2. Commit changes: git add . && git commit -m 'Bump version to {new_version}'")
    print(f"3. Create tag: git tag v{new_version}")
    print(f"4. Push: git push && git push --tags")

if __name__ == "__main__":
    main()

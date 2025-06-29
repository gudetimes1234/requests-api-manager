
"""Version management for requests-connection-manager."""

__version__ = "1.0.0"

def get_version():
    """Get the current version of the package."""
    return __version__

def bump_version(current_version: str, bump_type: str) -> str:
    """
    Bump version following semantic versioning.
    
    Args:
        current_version: Current version string (e.g., "1.0.0")
        bump_type: Type of bump ("major", "minor", "patch")
    
    Returns:
        New version string
    """
    major, minor, patch = map(int, current_version.split('.'))
    
    if bump_type == "major":
        return f"{major + 1}.0.0"
    elif bump_type == "minor":
        return f"{major}.{minor + 1}.0"
    elif bump_type == "patch":
        return f"{major}.{minor}.{patch + 1}"
    else:
        raise ValueError("bump_type must be 'major', 'minor', or 'patch'")

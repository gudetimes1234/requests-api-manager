
#!/usr/bin/env python3
"""
Script to verify requests-connection-manager package installation and availability.
Works in Replit and any Python environment.
"""

import sys
import subprocess
import importlib.metadata
from pathlib import Path

def check_package_installed(package_name):
    """Check if package is installed and return its metadata."""
    try:
        metadata = importlib.metadata.metadata(package_name)
        version = importlib.metadata.version(package_name)
        return True, version, metadata
    except importlib.metadata.PackageNotFoundError:
        return False, None, None

def install_package(package_name):
    """Install package using pip."""
    print(f"📦 Installing {package_name}...")
    try:
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", package_name
        ], capture_output=True, text=True, check=True)
        print(f"✅ Successfully installed {package_name}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install {package_name}")
        print(f"Error: {e.stderr}")
        return False

def get_pip_show_info(package_name):
    """Get detailed package info using pip show."""
    try:
        result = subprocess.run([
            sys.executable, "-m", "pip", "show", package_name
        ], capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError:
        return None

def check_pypi_availability(package_name):
    """Check if package is available on PyPI."""
    try:
        import urllib.request
        import json
        
        url = f"https://pypi.org/pypi/{package_name}/json"
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read())
            return True, data.get("info", {})
    except Exception:
        return False, {}

def verify_import():
    """Verify the package can be imported and check its contents."""
    try:
        import requests_connection_manager
        print(f"✅ Successfully imported requests_connection_manager")
        print(f"📍 Module location: {requests_connection_manager.__file__}")
        
        # Check available components
        components = [
            'ConnectionManager', 'AsyncConnectionManager', 
            'CircuitBreakerOpen', 'ConnectionManagerError',
            'MaxRetriesExceeded', 'RateLimitExceeded'
        ]
        
        available_components = []
        for component in components:
            if hasattr(requests_connection_manager, component):
                available_components.append(component)
        
        print(f"🔧 Available components: {', '.join(available_components)}")
        return True
    except ImportError as e:
        print(f"❌ Failed to import requests_connection_manager: {e}")
        return False

def main():
    """Main verification function."""
    package_name = "requests-connection-manager"
    
    print("🔍 Verifying requests-connection-manager package...")
    print("=" * 60)
    
    # Step 1: Check if package is installed
    is_installed, version, metadata = check_package_installed(package_name)
    
    if is_installed:
        print(f"✅ Package is installed")
        print(f"📦 Version: {version}")
        
        # Try to import and verify
        if verify_import():
            print("✅ Package import successful")
        else:
            print("⚠️  Package installed but import failed")
    else:
        print(f"❌ Package not installed")
        
        # Step 2: Check PyPI availability
        print(f"\n🌐 Checking PyPI availability...")
        is_available, pypi_info = check_pypi_availability(package_name)
        
        if is_available:
            print(f"✅ Package available on PyPI")
            print(f"📦 Latest version: {pypi_info.get('version', 'Unknown')}")
            print(f"📝 Description: {pypi_info.get('summary', 'No description')}")
        else:
            print(f"❌ Package not found on PyPI")
            return
        
        # Step 3: Try to install
        print(f"\n🔧 Attempting installation...")
        if install_package(package_name):
            # Re-check after installation
            is_installed, version, metadata = check_package_installed(package_name)
            if is_installed:
                print(f"✅ Installation verified - Version: {version}")
                verify_import()
            else:
                print("❌ Installation verification failed")
                return
        else:
            print("❌ Installation failed")
            return
    
    # Step 4: Display detailed package information
    print(f"\n📋 Detailed Package Information:")
    print("=" * 60)
    
    pip_info = get_pip_show_info(package_name)
    if pip_info:
        print(pip_info)
    else:
        # Fallback to metadata if pip show fails
        if metadata:
            print(f"Name: {metadata.get('Name', 'Unknown')}")
            print(f"Version: {metadata.get('Version', 'Unknown')}")
            print(f"Summary: {metadata.get('Summary', 'No summary')}")
            print(f"Author: {metadata.get('Author', 'Unknown')}")
            print(f"Author-email: {metadata.get('Author-email', 'Unknown')}")
            print(f"Home-page: {metadata.get('Home-page', 'Unknown')}")
            print(f"License: {metadata.get('License', 'Unknown')}")
    
    # Step 5: Test basic functionality
    print(f"\n🧪 Testing basic functionality...")
    print("=" * 60)
    
    try:
        from requests_connection_manager import ConnectionManager
        
        # Create a basic manager instance
        manager = ConnectionManager()
        print("✅ ConnectionManager instance created successfully")
        
        # Test configuration
        print(f"🔧 Default timeout: {getattr(manager, 'timeout', 'Not accessible')}")
        print(f"🔧 Max retries: {getattr(manager, 'max_retries', 'Not accessible')}")
        
        manager.close()
        print("✅ Manager closed successfully")
        
    except Exception as e:
        print(f"❌ Basic functionality test failed: {e}")
    
    print(f"\n🎉 Verification complete!")

if __name__ == "__main__":
    main()

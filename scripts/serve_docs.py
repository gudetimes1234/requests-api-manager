
#!/usr/bin/env python3
"""
Script to build and serve documentation for requests-connection-manager
"""

import subprocess
import sys
import os

def install_dependencies():
    """Install required dependencies for documentation."""
    print("Installing documentation dependencies...")
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", 
            "mkdocs", "mkdocs-material", "mkdocstrings[python]"
        ], check=True)
        print("✅ Dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False
    return True

def serve_docs():
    """Serve the documentation locally."""
    print("Starting documentation server...")
    try:
        subprocess.run([
            "mkdocs", "serve", "--dev-addr=0.0.0.0:5000"
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to serve docs: {e}")
        return False
    except KeyboardInterrupt:
        print("\n👋 Documentation server stopped")
    return True

def build_docs():
    """Build the documentation for deployment."""
    print("Building documentation...")
    try:
        subprocess.run(["mkdocs", "build"], check=True)
        print("✅ Documentation built successfully in 'site/' directory")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to build docs: {e}")
        return False
    return True

def main():
    """Main function to handle command line arguments."""
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "build":
            if install_dependencies():
                build_docs()
        elif command == "serve":
            if install_dependencies():
                serve_docs()
        elif command == "install":
            install_dependencies()
        else:
            print(f"Unknown command: {command}")
            print("Usage: python serve_docs.py [build|serve|install]")
    else:
        # Default: install and serve
        if install_dependencies():
            serve_docs()

if __name__ == "__main__":
    main()

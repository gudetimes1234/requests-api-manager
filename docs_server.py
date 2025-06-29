
#!/usr/bin/env python3
"""
Simple documentation server for requests-connection-manager
Run this script to serve the documentation locally on port 5000
"""

import os
import sys
import subprocess
import webbrowser
from pathlib import Path

def check_mkdocs():
    """Check if mkdocs is installed, install if not."""
    try:
        import mkdocs
        return True
    except ImportError:
        print("📦 Installing documentation dependencies...")
        try:
            subprocess.run([
                sys.executable, "-m", "pip", "install", 
                "mkdocs", "mkdocs-material", "mkdocstrings[python]"
            ], check=True, capture_output=True)
            print("✅ Dependencies installed successfully!")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install dependencies: {e}")
            return False

def serve_docs():
    """Serve the documentation."""
    if not check_mkdocs():
        return False
    
    print("🚀 Starting documentation server...")
    print("📖 Documentation will be available at: http://localhost:5000")
    print("🛑 Press Ctrl+C to stop the server")
    print()
    
    try:
        # Start the server
        subprocess.run([
            "mkdocs", "serve", "--dev-addr=0.0.0.0:5000"
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start server: {e}")
        return False
    except KeyboardInterrupt:
        print("\n👋 Documentation server stopped")
        return True

if __name__ == "__main__":
    print("📚 requests-connection-manager Documentation Server")
    print("=" * 50)
    serve_docs()

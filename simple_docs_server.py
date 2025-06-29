#!/usr/bin/env python3
"""
Simple documentation server for requests-connection-manager
Serves README.md and documentation files on port 5000
"""

import http.server
import socketserver
import os
import markdown
from pathlib import Path

class DocumentationHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            self.serve_readme()
        elif self.path == '/examples':
            self.serve_examples()
        else:
            super().do_GET()
    
    def serve_readme(self):
        """Serve the README.md as HTML"""
        try:
            readme_path = Path('README.md')
            if readme_path.exists():
                with open(readme_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Convert markdown to HTML
                html_content = markdown.markdown(content, extensions=['codehilite', 'fenced_code'])
                
                # Wrap in basic HTML structure
                full_html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>requests-connection-manager Documentation</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 900px; margin: 0 auto; padding: 20px; }}
        code {{ background-color: #f4f4f4; padding: 2px 4px; border-radius: 3px; }}
        pre {{ background-color: #f4f4f4; padding: 10px; border-radius: 5px; overflow-x: auto; }}
        h1, h2, h3 {{ color: #333; }}
        a {{ color: #0066cc; }}
    </style>
</head>
<body>
    <nav>
        <a href="/">Home</a> | 
        <a href="/examples">Examples</a>
    </nav>
    <hr>
    {html_content}
</body>
</html>
                """
                
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(full_html.encode('utf-8'))
            else:
                self.send_error(404, "README.md not found")
        except Exception as e:
            self.send_error(500, f"Error serving documentation: {e}")
    
    def serve_examples(self):
        """Serve examples directory listing"""
        examples_dir = Path('examples')
        if not examples_dir.exists():
            self.send_error(404, "Examples directory not found")
            return
        
        files = list(examples_dir.glob('*.py'))
        
        html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>Examples - requests-connection-manager</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 900px; margin: 0 auto; padding: 20px; }
        .file-list { list-style-type: none; padding: 0; }
        .file-list li { margin: 10px 0; padding: 10px; background-color: #f8f9fa; border-radius: 5px; }
        .file-list a { text-decoration: none; color: #0066cc; font-weight: bold; }
    </style>
</head>
<body>
    <nav>
        <a href="/">Home</a> | 
        <a href="/examples">Examples</a>
    </nav>
    <hr>
    <h1>Example Files</h1>
    <ul class="file-list">
        """
        
        for file in sorted(files):
            html_content += f'<li><a href="/examples/{file.name}">{file.name}</a> - {file.stem.replace("_", " ").title()}</li>'
        
        html_content += """
    </ul>
</body>
</html>
        """
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html_content.encode('utf-8'))

def main():
    PORT = 5000
    
    # Install markdown if not available
    try:
        import markdown
    except ImportError:
        print("Installing markdown...")
        import subprocess
        import sys
        subprocess.check_call([sys.executable, "-m", "pip", "install", "markdown"])
        import markdown
    
    # Change to project directory
    os.chdir(Path(__file__).parent)
    
    with socketserver.TCPServer(("0.0.0.0", PORT), DocumentationHandler) as httpd:
        print(f"Documentation server running at http://0.0.0.0:{PORT}")
        print("Serving README.md and examples")
        print("Press Ctrl+C to stop")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped")

if __name__ == "__main__":
    main()
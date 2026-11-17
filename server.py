#!/usr/bin/env python3
"""
Simple HTTP server for the music player.
Serves static files and provides directory listing for /songs with folder navigation.
"""
import http.server
import socketserver
import os
import json
import urllib.parse
from pathlib import Path

PORT = 8081
BASE_DIR = Path(__file__).parent
SONGS_DIR = BASE_DIR / "songs"
AUDIO_EXTS = {'.mp3', '.wav', '.ogg', '.m4a', '.flac', '.aac'}

class MusicHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(BASE_DIR), **kwargs)
    
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        
        # API endpoint for directory listing
        if path.startswith('/api/browse'):
            self.send_browse_json(parsed)
            return
        
        # Serve songs directory files
        if path.startswith('/songs/'):
            self.serve_songs_file(path)
            return
        
        # Default file serving
        super().do_GET()
    
    def send_browse_json(self, parsed):
        """Return JSON listing of files and folders at given path."""
        query = urllib.parse.parse_qs(parsed.query)
        rel_path = query.get('path', [''])[0]
        
        # Resolve path relative to songs directory
        target_dir = (SONGS_DIR / rel_path).resolve()
        
        # Security: ensure path is within songs directory
        try:
            target_dir.relative_to(SONGS_DIR.resolve())
        except ValueError:
            self.send_error(403, "Access denied")
            return
        
        if not target_dir.exists() or not target_dir.is_dir():
            self.send_error(404, "Directory not found")
            return
        
        items = []
        for entry in sorted(target_dir.iterdir(), key=lambda e: (not e.is_dir(), e.name.lower())):
            if entry.is_dir():
                items.append({
                    'type': 'folder',
                    'name': entry.name,
                    'path': str(entry.relative_to(SONGS_DIR)).replace('\\', '/')
                })
            elif entry.suffix.lower() in AUDIO_EXTS:
                parsed_name = self.parse_filename(entry.name)
                items.append({
                    'type': 'file',
                    'name': entry.name,
                    'path': str(entry.relative_to(SONGS_DIR)).replace('\\', '/'),
                    'url': f'/songs/{urllib.parse.quote(str(entry.relative_to(SONGS_DIR)).replace("\\", "/"))}',
                    'title': parsed_name['title'],
                    'artist': parsed_name['artist']
                })
        
        # Add parent directory entry if not at root
        parent_path = ''
        if rel_path:
            parent_parts = rel_path.rstrip('/').split('/')
            if len(parent_parts) > 1:
                parent_path = '/'.join(parent_parts[:-1])
            else:
                parent_path = ''
        
        response = {
            'current_path': rel_path,
            'parent_path': parent_path,
            'has_parent': bool(rel_path),
            'items': items
        }
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode())
    
    def parse_filename(self, filename):
        """Parse 'Artist - Title' from filename."""
        name = filename.rsplit('.', 1)[0]
        parts = name.split(' - ', 1)
        if len(parts) == 2:
            return {'artist': parts[0].strip(), 'title': parts[1].strip()}
        return {'artist': 'Unknown Artist', 'title': name}
    
    def serve_songs_file(self, path):
        """Serve a file from the songs directory."""
        # Remove /songs/ prefix
        rel_path = path[7:]  # Remove '/songs/'
        rel_path = urllib.parse.unquote(rel_path)
        file_path = (SONGS_DIR / rel_path).resolve()
        
        # Security check
        try:
            file_path.relative_to(SONGS_DIR.resolve())
        except ValueError:
            self.send_error(403, "Access denied")
            return
        
        if file_path.exists() and file_path.is_file():
            self.serve_file(file_path)
        else:
            self.send_error(404, "File not found")
    
    def serve_file(self, file_path):
        """Serve a file with proper headers."""
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            
            self.send_response(200)
            ext = file_path.suffix.lower()
            content_types = {
                '.mp3': 'audio/mpeg',
                '.wav': 'audio/wav',
                '.ogg': 'audio/ogg',
                '.m4a': 'audio/mp4',
                '.flac': 'audio/flac',
                '.aac': 'audio/aac',
            }
            self.send_header('Content-Type', content_types.get(ext, 'application/octet-stream'))
            self.send_header('Content-Length', str(len(content)))
            self.send_header('Accept-Ranges', 'bytes')
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_error(500, str(e))

if __name__ == '__main__':
    os.chdir(BASE_DIR)
    SONGS_DIR.mkdir(exist_ok=True)
    
    with socketserver.TCPServer(("", PORT), MusicHandler) as httpd:
        print(f"Server running at http://localhost:{PORT}")
        print(f"Songs directory: {SONGS_DIR}")
        print("Press Ctrl+C to stop")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped")

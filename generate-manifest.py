#!/usr/bin/env python3
"""
Generate songs-manifest.json for static hosting (GitHub Pages).
Run this after adding new songs to commit the manifest.
"""
import json
import os
from pathlib import Path

SONGS_DIR = Path(__file__).parent / "songs"
AUDIO_EXTS = {'.mp3', '.wav', '.ogg', '.m4a', '.flac', '.aac'}

def parse_filename(filename):
    name = filename.rsplit('.', 1)[0]
    parts = name.split(' - ', 1)
    if len(parts) == 2:
        return {'artist': parts[0].strip(), 'title': parts[1].strip()}
    return {'artist': 'Unknown Artist', 'title': name}

def scan_songs():
    songs = []
    for file in SONGS_DIR.rglob('*'):
        if file.is_file() and file.suffix.lower() in AUDIO_EXTS:
            rel_path = file.relative_to(SONGS_DIR).as_posix()
            parsed = parse_filename(file.name)
            songs.append({
                'path': f'songs/{rel_path}',
                'name': file.name,
                'url': f'https://raw.githubusercontent.com/OWNER/REPO/BRANCH/songs/{rel_path}',
                'title': parsed['title'],
                'artist': parsed['artist']
            })
    return songs

if __name__ == '__main__':
    songs = scan_songs()
    manifest_path = Path(__file__).parent / "songs-manifest.json"
    with open(manifest_path, 'w') as f:
        json.dump(songs, f, indent=2)
    print(f"Generated {manifest_path} with {len(songs)} songs")
    print("Note: Update the URL in the manifest with your actual GitHub repo info")

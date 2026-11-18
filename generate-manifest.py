#!/usr/bin/env python3
"""
Generate songs-manifest.json for static hosting (GitHub Pages).
Run this after adding new songs to commit the manifest.
"""
import json
import os
import subprocess
from pathlib import Path

SONGS_DIR = Path(__file__).parent / "songs"
AUDIO_EXTS = {'.mp3', '.wav', '.ogg', '.m4a', '.flac', '.aac'}

def get_github_info():
    """Try to get owner/repo/branch from git remote."""
    try:
        result = subprocess.run(
            ['git', 'config', '--get', 'remote.origin.url'],
            capture_output=True, text=True, cwd=Path(__file__).parent
        )
        if result.returncode == 0:
            url = result.stdout.strip()
            # Parse git@github.com:owner/repo.git or https://github.com/owner/repo.git
            if 'github.com' in url:
                if url.startswith('git@'):
                    parts = url.split(':')[1].replace('.git', '')
                else:
                    parts = url.split('github.com/')[1].replace('.git', '')
                owner, repo = parts.split('/')[:2]
                
                # Get current branch
                branch_result = subprocess.run(
                    ['git', 'branch', '--show-current'],
                    capture_output=True, text=True, cwd=Path(__file__).parent
                )
                branch = branch_result.stdout.strip() or 'main'
                return owner, repo, branch
    except Exception:
        pass
    return None, None, None

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
    # Try to auto-detect GitHub info
    owner, repo, branch = get_github_info()
    
    songs = scan_songs()
    
    # If we detected GitHub info, update URLs
    if owner and repo and branch:
        for song in songs:
            song['url'] = song['url'].replace('OWNER', owner).replace('REPO', repo).replace('BRANCH', branch)
        print(f"Detected GitHub repo: {owner}/{repo} @ {branch}")
    else:
        print("Could not auto-detect GitHub repo. URLs will need manual update.")
    
    manifest_path = Path(__file__).parent / "songs-manifest.json"
    with open(manifest_path, 'w') as f:
        json.dump({'songs': songs}, f, indent=2)
    print(f"Generated {manifest_path} with {len(songs)} songs")

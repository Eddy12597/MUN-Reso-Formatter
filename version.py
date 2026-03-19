# version.py
import datetime
import subprocess
import os

def update_version_info():
    """Run this script manually or via console to update version info"""
    try:
        # Get last commit info
        commit_hash = subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode('utf-8').strip()
        commit_message = subprocess.check_output(['git', 'log', '-1', '--pretty=%B']).decode('utf-8').strip()
        
        # Get current time
        last_pull = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Write to version file
        with open('version_info.txt', 'w') as f:
            f.write(f"Last Pull: {last_pull}\n")
            f.write(f"Commit: {commit_hash}\n")
            f.write(f"Message: {commit_message}\n")
            
        print(f"Version info updated: {last_pull}")
    except Exception as e:
        print(f"Error updating version: {e}")

def get_version_info():
    """Read version info for display in the app"""
    try:
        with open('version_info.txt', 'r') as f:
            return f.read()
    except FileNotFoundError:
        return "Version info not available"
#!/usr/bin/env python3
# update.py
import subprocess
import sys
from version import update_version_info

def main():
    print("Pulling latest changes...")
    result = subprocess.run(['git', 'pull'], capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print("Errors:", result.stderr)
    
    if result.returncode == 0:
        print("\nUpdating version info...")
        update_version_info()
        print("Done!")
    else:
        print("Git pull failed")
        sys.exit(1)

if __name__ == '__main__':
    main()
#!/usr/bin/env python3

import os
import argparse
import json
from datetime import datetime

def clean_state_files(backup=False, reset_logs=False):
    """Delete crawler state files to start a fresh search."""
    state_files = [
        'visited_urls.pkl',
        'queue.pkl',
        'failed_urls.pkl',
        'crawler_log.json',
        'crawler_detailed.log',
        'all_scraped_content.json'
    ]
    data_dirs = [
        'scraped_data'
    ]
    
    # Create backup directory if needed
    if backup:
        backup_dir = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        os.makedirs(backup_dir, exist_ok=True)
        print(f"Creating backups in: {backup_dir}")
    
    # Process state and log files
    for filename in state_files:
        if os.path.exists(filename):
            if backup:
                backup_path = os.path.join(backup_dir, filename)
                print(f"Backing up {filename} to {backup_path}")
                try:
                    import shutil
                    shutil.copy2(filename, backup_path)
                except Exception as e:
                    print(f"Warning: Backup of {filename} failed: {e}")
            
            # Delete state file
            try:
                os.remove(filename)
                print(f"Deleted: {filename}")
            except Exception as e:
                print(f"Error deleting {filename}: {e}")
        else:
            print(f"File not found: {filename}")
    
    # Process data directories
    for dirname in data_dirs:
        if os.path.exists(dirname):
            if backup:
                backup_path = os.path.join(backup_dir, dirname)
                print(f"Backing up {dirname} to {backup_path}")
                try:
                    import shutil
                    shutil.copytree(dirname, backup_path)
                except Exception as e:
                    print(f"Warning: Backup of {dirname} failed: {e}")
            try:
                import shutil
                shutil.rmtree(dirname)
                print(f"Deleted directory: {dirname}")
            except Exception as e:
                print(f"Error deleting directory {dirname}: {e}")
        else:
            print(f"Directory not found: {dirname}")
    
    # Handle log file if requested
    log_file = 'crawler_log.json'
    if reset_logs and os.path.exists(log_file):
        if backup:
            backup_path = os.path.join(backup_dir, log_file)
            print(f"Backing up {log_file} to {backup_path}")
            try:
                import shutil
                shutil.copy2(log_file, backup_path)
            except Exception as e:
                print(f"Warning: Backup of {log_file} failed: {e}")
        
        # Reset log file (create empty array)
        try:
            with open(log_file, 'w') as f:
                json.dump([], f)
            print(f"Reset log file: {log_file}")
        except Exception as e:
            print(f"Error resetting {log_file}: {e}")

def main():
    parser = argparse.ArgumentParser(
        description="Clean DuskToDawn crawler state to start a fresh search")
    parser.add_argument('--backup', action='store_true', 
                      help='Create backups of state files before deleting')
    parser.add_argument('--reset-logs', action='store_true',
                      help='Also reset the crawler_log.json file')
    args = parser.parse_args()
    
    print("DuskToDawn Crawler State Cleaner")
    print("--------------------------------")
    
    if not args.backup:
        confirm = input("Are you sure you want to delete crawler state without backup? (y/n): ")
        if confirm.lower() != 'y':
            print("Operation cancelled.")
            return
    
    clean_state_files(backup=args.backup, reset_logs=args.reset_logs)
    print("\nCrawler state cleaned. You can now start a fresh search.")

if __name__ == "__main__":
    main()

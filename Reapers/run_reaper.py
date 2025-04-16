#!/usr/bin/env python3

import os
import sys
import time
import argparse
import subprocess

def main():
    parser = argparse.ArgumentParser(description='DuskToDawn Web Intelligence Crawler')
    parser.add_argument('--enhanced', action='store_true', help='Use enhanced stealth crawler')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    args = parser.parse_args()
    
    if args.debug == True:
        print("Debug mode enabled")
        os.environ['CRAWLER_DEBUG'] = 'true'
    
    # Check Tor service before starting
    check_tor_availability()
    
    print("="*60)
    print("DuskToDawn Web Intelligence Crawler")
    print("="*60)
    
    if args.enhanced:
        print("Using enhanced stealth crawler with advanced anti-detection...")
        run_script = os.path.join(os.path.dirname(__file__), 'enhanced_reaper.py')
    else:
        print("Using standard crawler...")
        run_script = os.path.join(os.path.dirname(__file__), 'deep_reaper.py')
    
    print(f"Starting {os.path.basename(run_script)}...")
    time.sleep(1)
    
    try:
        subprocess.run([sys.executable, run_script], check=True)
    except KeyboardInterrupt:
        print("\nCrawl interrupted by user.")
    except subprocess.CalledProcessError as e:
        print(f"Error running crawler: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

def check_tor_availability():
    """Check if Tor service is running and accessible"""
    import socket
    
    print("Checking Tor service availability...")
    
    # Check SOCKS proxy
    try:
        with socket.create_connection(('127.0.0.1', 9050), timeout=5):
            print("✓ Tor SOCKS proxy is accessible (port 9050)")
    except (socket.timeout, ConnectionRefusedError):
        print("✗ ERROR: Cannot connect to Tor SOCKS proxy on port 9050")
        print("  Please ensure Tor service is running.")
        if input("Continue anyway? (y/n): ").lower() != 'y':
            sys.exit(1)
    
    # Check control port if needed for circuit renewal
    try:
        with socket.create_connection(('127.0.0.1', 9051), timeout=2):
            print("✓ Tor control port is accessible (port 9051)")
    except (socket.timeout, ConnectionRefusedError):
        print("! WARNING: Cannot connect to Tor control port on 9051")
        print("  Circuit renewal may not work. IP rotation will be limited.")
        
    print("-"*60)

if __name__ == '__main__':
    main()
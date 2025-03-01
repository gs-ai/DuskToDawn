#!/usr/bin/env python3

import os
import sys
import time
import socket
import argparse
import requests
import json
import random
from stem import Signal
from stem.control import Controller
from colorama import init, Fore, Back, Style

# Initialize colorama
init()

class TorManager:
    """
    Utility tool to manage Tor connections and test their functionality.
    """
    def __init__(self, socks_port=9050, control_port=9051, password=None):
        self.socks_port = socks_port
        self.control_port = control_port
        self.password = password
        self.session = self.setup_tor_session()
        
    def setup_tor_session(self):
        """Set up a requests session that uses Tor as a proxy."""
        session = requests.Session()
        session.proxies.update({
            'http': f'socks5h://127.0.0.1:{self.socks_port}',
            'https': f'socks5h://127.0.0.1:{self.socks_port}'
        })
        return session
        
    def check_tor_connection(self):
        """Check if the Tor connection is working."""
        try:
            # First check if Tor SOCKS proxy is accessible
            with socket.create_connection(('127.0.0.1', self.socks_port), timeout=5):
                print(f"{Fore.GREEN}✓ Tor SOCKS proxy is accessible on port {self.socks_port}{Style.RESET_ALL}")
                
            # Then try to connect to the Tor API
            response = self.session.get('https://check.torproject.org/api/ip', timeout=10)
            data = response.json()
            
            if data.get('IsTor', False):
                print(f"{Fore.GREEN}✓ Successfully connected through Tor!{Style.RESET_ALL}")
                print(f"  IP Address: {data.get('IP', 'unknown')}")
                return True
            else:
                print(f"{Fore.RED}✗ Connected to the internet but not through Tor{Style.RESET_ALL}")
                print(f"  Current IP: {data.get('IP', 'unknown')}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"{Fore.RED}✗ Failed to connect through Tor: {str(e)}{Style.RESET_ALL}")
            return False
        except socket.error as e:
            print(f"{Fore.RED}✗ Cannot connect to Tor SOCKS proxy: {str(e)}{Style.RESET_ALL}")
            return False
            
    def check_control_port(self):
        """Check if the Tor control port is accessible."""
        try:
            with socket.create_connection(('127.0.0.1', self.control_port), timeout=5):
                print(f"{Fore.GREEN}✓ Tor control port is accessible on port {self.control_port}{Style.RESET_ALL}")
                return True
        except socket.error as e:
            print(f"{Fore.RED}✗ Cannot connect to Tor control port: {str(e)}{Style.RESET_ALL}")
            return False
    
    def renew_tor_identity(self):
        """Request a new identity (circuit) from Tor."""
        try:
            old_ip = self.get_current_ip()
            
            print(f"Current Tor IP: {old_ip}")
            print("Requesting new Tor circuit...")
            
            with Controller.from_port(port=self.control_port) as controller:
                if self.password:
                    controller.authenticate(password=self.password)
                else:
                    controller.authenticate()  # Cookie authentication
                    
                controller.signal(Signal.NEWNYM)
                
            # Wait for the circuit to change
            time.sleep(random.uniform(1.0, 2.0))
            
            new_ip = self.get_current_ip()
            
            if old_ip != new_ip:
                print(f"{Fore.GREEN}✓ Successfully changed Tor circuit{Style.RESET_ALL}")
                print(f"  Old IP: {old_ip}")
                print(f"  New IP: {new_ip}")
                return True
            else:
                print(f"{Fore.YELLOW}! Circuit change requested, but IP remained the same{Style.RESET_ALL}")
                print("  This can happen if Tor doesn't have enough circuits available.")
                return False
                
        except Exception as e:
            print(f"{Fore.RED}✗ Failed to change Tor circuit: {str(e)}{Style.RESET_ALL}")
            return False
    
    def get_current_ip(self):
        """Get the current IP address through Tor."""
        try:
            response = self.session.get('https://api.ipify.org', timeout=10)
            return response.text.strip()
        except:
            try:
                response = self.session.get('https://ifconfig.me/ip', timeout=10)
                return response.text.strip()
            except:
                return "unknown"
    
    def run_connectivity_tests(self):
        """Run a series of tests to check Tor connectivity."""
        print(f"\n{Back.BLUE}{Fore.WHITE} TOR CONNECTIVITY TESTS {Style.RESET_ALL}\n")
        
        # Base connection test
        tor_connected = self.check_tor_connection()
        control_port_ok = self.check_control_port()
        
        if not tor_connected:
            print(f"\n{Fore.RED}Tor connection failed. Please check that Tor is running.{Style.RESET_ALL}")
            return False
            
        if not control_port_ok:
            print(f"\n{Fore.YELLOW}Tor control port is not accessible. Circuit renewal won't work.{Style.RESET_ALL}")
            
        # Speed test
        print("\nRunning speed test...")
        start_time = time.time()
        try:
            self.session.get('https://www.google.com', timeout=10)
            elapsed = time.time() - start_time
            print(f"{Fore.GREEN}Speed test successful: {elapsed:.2f} seconds{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}Speed test failed: {str(e)}{Style.RESET_ALL}")
            
        # Test access to common sites
        test_sites = [
            'https://www.google.com',
            'https://www.reddit.com',
            'https://www.wikipedia.org',
            'https://www.github.com'
        ]
        
        print("\nTesting access to common websites...")
        for site in test_sites:
            try:
                start_time = time.time()
                response = self.session.get(site, timeout=15)
                elapsed = time.time() - start_time
                print(f"{Fore.GREEN}✓ {site} - {response.status_code} OK ({elapsed:.2f}s){Style.RESET_ALL}")
            except Exception as e:
                print(f"{Fore.RED}✗ {site} - Failed: {str(e)}{Style.RESET_ALL}")
        
        return True
        
    def monitor_circuit_changes(self, changes=5, delay=30):
        """Monitor IP changes across multiple circuit changes."""
        print(f"\n{Back.BLUE}{Fore.WHITE} TOR CIRCUIT MONITORING {Style.RESET_ALL}\n")
        print(f"Will request {changes} circuit changes with {delay} seconds between each.")
        
        ips = []
        for i in range(changes):
            print(f"\nCircuit change {i+1}/{changes}:")
            current_ip = self.get_current_ip()
            ips.append(current_ip)
            print(f"Current IP: {current_ip}")
            
            if i < changes - 1:
                self.renew_tor_identity()
                print(f"Waiting {delay} seconds...")
                time.sleep(delay)
                
        # Check uniqueness
        unique_ips = len(set(ips))
        print(f"\nResults: Got {unique_ips} unique IPs out of {changes} requests")
        
        if unique_ips < changes:
            print(f"{Fore.YELLOW}Warning: Some IPs were reused. This might indicate limited circuit availability.{Style.RESET_ALL}")
        else:
            print(f"{Fore.GREEN}Perfect! Each circuit change resulted in a unique IP.{Style.RESET_ALL}")

def main():
    parser = argparse.ArgumentParser(description="Tor Connection Manager")
    parser.add_argument('--socks', type=int, default=9050, help='Tor SOCKS port (default: 9050)')
    parser.add_argument('--control', type=int, default=9051, help='Tor control port (default: 9051)')
    parser.add_argument('--password', help='Password for Tor control port (if required)')
    parser.add_argument('--test', action='store_true', help='Run connectivity tests')
    parser.add_argument('--renew', action='store_true', help='Renew Tor identity (circuit)')
    parser.add_argument('--monitor', type=int, metavar='N', help='Monitor N circuit changes')
    parser.add_argument('--delay', type=int, default=30, help='Delay between circuit changes in seconds')
    
    args = parser.parse_args()
    
    tor_manager = TorManager(
        socks_port=args.socks,
        control_port=args.control,
        password=args.password
    )
    
    if args.test:
        tor_manager.run_connectivity_tests()
    elif args.renew:
        tor_manager.renew_tor_identity()
    elif args.monitor:
        tor_manager.monitor_circuit_changes(changes=args.monitor, delay=args.delay)
    else:
        # Default behavior: check connection and show help
        tor_manager.check_tor_connection()
        tor_manager.check_control_port()
        print("\nFor more options, run with --help")

if __name__ == '__main__':
    main()

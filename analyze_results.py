#!/usr/bin/env python3

import os
import json
import argparse
import gzip
import re
import sys
from collections import Counter, defaultdict
from urllib.parse import urlparse
from datetime import datetime
import pandas as pd
from colorama import init, Fore, Back, Style

# Initialize colorama for cross-platform colored terminal output
init()

class ResultAnalyzer:
    def __init__(self, log_file='crawler_log.json', data_dir='scraped_data'):
        self.log_file = log_file
        self.data_dir = data_dir
        self.entries = []
        self.load_entries()
        
    def load_entries(self):
        """Load all entries from the crawler log file."""
        if not os.path.exists(self.log_file):
            print(f"{Fore.RED}Error: Log file '{self.log_file}' not found.{Style.RESET_ALL}")
            sys.exit(1)
            
        print(f"Loading entries from {self.log_file}...")
        try:
            with open(self.log_file, 'r') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        if isinstance(entry, dict):
                            self.entries.append(entry)
                        else:
                            # Skip non-dict entries (e.g., lists)
                            continue
                    except json.JSONDecodeError:
                        continue
            print(f"{Fore.GREEN}Successfully loaded {len(self.entries)} entries.{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}Error loading log file: {str(e)}{Style.RESET_ALL}")
            sys.exit(1)
    
    def summarize_findings(self):
        """Print a summary of findings."""
        if not self.entries:
            print("No entries found.")
            return
            
        print(f"\n{Back.BLUE}{Fore.WHITE} SUMMARY OF FINDINGS {Style.RESET_ALL}")
        print(f"\nTotal mentions found: {len(self.entries)}")
        
        # Analyze by domain
        domains = Counter([urlparse(entry['url']).netloc for entry in self.entries])
        print(f"\nTop domains with mentions:")
        for domain, count in domains.most_common(10):
            print(f"  {domain}: {count} mentions")
            
        # Analyze by name variation
        variations = Counter([entry['variation'] for entry in self.entries])
        print(f"\nMentions by name variation:")
        for var, count in variations.most_common():
            print(f"  {var}: {count} mentions")
            
        # Sentiment analysis
        sentiments = [entry['sentiment']['polarity'] for entry in self.entries]
        avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0
        print(f"\nAverage sentiment: {avg_sentiment:.2f} (-1 negative to +1 positive)")
        
        # Sentiment distribution
        positive = sum(1 for s in sentiments if s > 0.1)
        negative = sum(1 for s in sentiments if s < -0.1)
        neutral = len(sentiments) - positive - negative
        
        print(f"Sentiment distribution:")
        print(f"  Positive: {positive} ({positive/len(sentiments)*100:.1f}%)")
        print(f"  Neutral: {neutral} ({neutral/len(sentiments)*100:.1f}%)")
        print(f"  Negative: {negative} ({negative/len(sentiments)*100:.1f}%)")
    
    def show_detailed_mentions(self, limit=None):
        """Show detailed mentions with context."""
        if not self.entries:
            return
            
        print(f"\n{Back.BLUE}{Fore.WHITE} DETAILED MENTIONS {Style.RESET_ALL}\n")
        
        for i, entry in enumerate(self.entries[:limit]):
            url = entry['url']
            variation = entry['variation']
            context = entry['context']
            sentiment = entry['sentiment']['polarity']
            timestamp = entry.get('timestamp', 'unknown')
            
            # Format the date if it's parseable
            try:
                dt = datetime.fromisoformat(timestamp)
                timestamp = dt.strftime('%Y-%m-%d %H:%M')
            except (ValueError, TypeError):
                pass
                
            print(f"{Fore.GREEN}[{i+1}/{len(self.entries)}] {variation}{Style.RESET_ALL}")
            print(f"URL: {url}")
            print(f"Found: {timestamp}")
            
            # Format sentiment with color
            if sentiment > 0.1:
                sentiment_color = Fore.GREEN
            elif sentiment < -0.1:
                sentiment_color = Fore.RED
            else:
                sentiment_color = Fore.YELLOW
                
            print(f"Sentiment: {sentiment_color}{sentiment:.2f}{Style.RESET_ALL}")
            
            # Format context with highlighted variation
            highlighted = re.sub(
                rf'({re.escape(variation)})', 
                f"{Back.YELLOW}{Fore.BLACK}\\1{Style.RESET_ALL}", 
                context, 
                flags=re.IGNORECASE
            )
            print(f"\nContext:\n{highlighted}\n")
            print("-" * 80)
            
            # Add a pause every 5 entries if showing many
            if limit is None and i > 0 and i % 5 == 0 and i < len(self.entries) - 1:
                input("Press Enter to continue...")
    
    def export_to_csv(self, filename='results.csv'):
        """Export results to a CSV file."""
        if not self.entries:
            print("No entries to export.")
            return
            
        try:
            data = []
            for entry in self.entries:
                data.append({
                    'url': entry['url'],
                    'domain': urlparse(entry['url']).netloc,
                    'variation': entry['variation'],
                    'timestamp': entry.get('timestamp', ''),
                    'context': entry['context'],
                    'sentiment_polarity': entry['sentiment']['polarity'],
                    'sentiment_subjectivity': entry['sentiment']['subjectivity']
                })
                
            df = pd.DataFrame(data)
            df.to_csv(filename, index=False)
            print(f"{Fore.GREEN}Successfully exported {len(self.entries)} entries to {filename}{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}Error exporting to CSV: {str(e)}{Style.RESET_ALL}")
    
    def create_visualizations(self):
        """Create visualizations of the findings."""
        if not self.entries or len(self.entries) < 2:
            print("Not enough entries for visualization.")
            return
            
        try:
            import matplotlib.pyplot as plt
            import numpy as np
            
            # Extract data
            domains = Counter([urlparse(entry['url']).netloc for entry in self.entries])
            sentiments = [entry['sentiment']['polarity'] for entry in self.entries]
            
            # Create figure
            plt.figure(figsize=(15, 10))
            
            # Plot 1: Top domains
            plt.subplot(2, 1, 1)
            top_domains = dict(domains.most_common(10))
            plt.bar(top_domains.keys(), top_domains.values(), color='skyblue')
            plt.title('Top 10 Domains with Mentions')
            plt.xlabel('Domain')
            plt.ylabel('Number of Mentions')
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            
            # Plot 2: Sentiment distribution
            plt.subplot(2, 1, 2)
            plt.hist(sentiments, bins=20, color='lightgreen')
            plt.title('Sentiment Distribution')
            plt.xlabel('Sentiment (Negative to Positive)')
            plt.ylabel('Frequency')
            plt.tight_layout()
            
            # Save and show
            plt.savefig('sentiment_analysis.png')
            print(f"{Fore.GREEN}Visualization saved as sentiment_analysis.png{Style.RESET_ALL}")
            plt.show()
            
        except ImportError:
            print(f"{Fore.YELLOW}Visualization requires matplotlib and numpy. Install with:\npip install matplotlib numpy{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}Error creating visualizations: {str(e)}{Style.RESET_ALL}")

def main():
    parser = argparse.ArgumentParser(description="Analyze DuskToDawn crawler results")
    parser.add_argument('--log', default='crawler_log.json', help='Path to crawler log file')
    parser.add_argument('--data', default='scraped_data', help='Path to crawled data directory')
    parser.add_argument('--limit', type=int, help='Limit the number of detailed mentions to show')
    parser.add_argument('--csv', action='store_true', help='Export results to CSV')
    parser.add_argument('--viz', action='store_true', help='Create visualizations')
    args = parser.parse_args()
    
    analyzer = ResultAnalyzer(log_file=args.log, data_dir=args.data)
    analyzer.summarize_findings()
    
    if args.limit is not None:
        analyzer.show_detailed_mentions(limit=args.limit)
    else:
        show_all = input("\nShow all detailed mentions? (y/n): ")
        if show_all.lower() == 'y':
            analyzer.show_detailed_mentions()
    
    if args.csv:
        analyzer.export_to_csv()
        
    if args.viz:
        analyzer.create_visualizations()
    elif not args.csv:
        create_viz = input("\nCreate visualizations? (y/n): ")
        if create_viz.lower() == 'y':
            analyzer.create_visualizations()

if __name__ == '__main__':
    main()

#!/usr/bin/env python3

import re
import sys
import argparse
import datetime
from collections import Counter, defaultdict
import matplotlib.pyplot as plt

class CrawlerLogAnalyzer:
    def __init__(self, log_file):
        self.log_file = log_file
        self.entries = []
        self.strategies = Counter()
        self.urls_processed = set()
        self.errors = []
        self.url_times = defaultdict(list)
        self.start_time = None
        self.end_time = None
        
    def parse_log(self):
        print(f"Analyzing log file: {self.log_file}")
        
        timestamp_pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})'
        url_pattern = r'URL: (https?://[^\s]+)'
        strategy_pattern = r'strategy: (_\w+)'
        
        try:
            with open(self.log_file, 'r') as f:
                current_url = None
                url_start_time = None
                
                for line in f:
                    # Parse timestamp
                    timestamp_match = re.search(timestamp_pattern, line)
                    if timestamp_match:
                        timestamp_str = timestamp_match.group(1)
                        timestamp = datetime.datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S,%f')
                        
                        # Track overall time range
                        if not self.start_time or timestamp < self.start_time:
                            self.start_time = timestamp
                        if not self.end_time or timestamp > self.end_time:
                            self.end_time = timestamp
                    
                    # Track URL processing
                    if 'Processing:' in line and timestamp_match:
                        url_match = re.search(r'Processing: (https?://[^\s]+)', line)
                        if url_match:
                            current_url = url_match.group(1)
                            url_start_time = timestamp
                            self.urls_processed.add(current_url)
                    
                    # Track completion of URL processing
                    if 'Added' in line and 'new URLs to queue' in line and current_url and url_start_time:
                        if timestamp_match:
                            time_diff = (timestamp - url_start_time).total_seconds()
                            self.url_times[current_url].append(time_diff)
                            current_url = None
                            url_start_time = None
                    
                    # Track strategies used
                    if 'strategy:' in line:
                        strategy_match = re.search(strategy_pattern, line)
                        if strategy_match:
                            self.strategies[strategy_match.group(1)] += 1
                    
                    # Track errors
                    if '[ERROR]' in line or '[WARNING]' in line:
                        self.errors.append(line.strip())
                
                print(f"Log analysis complete. Found {len(self.urls_processed)} URLs processed.")
                
        except FileNotFoundError:
            print(f"Error: Log file '{self.log_file}' not found.")
            sys.exit(1)
        except Exception as e:
            print(f"Error analyzing log file: {str(e)}")
            sys.exit(1)
    
    def display_stats(self):
        """Display statistics from the log."""
        if not self.urls_processed:
            print("No URLs processed found in the log.")
            return
            
        print("\n===== CRAWLER STATISTICS =====")
        
        # Time statistics
        if self.start_time and self.end_time:
            total_time = (self.end_time - self.start_time).total_seconds()
            print(f"\nCrawl Duration: {total_time:.2f} seconds ({total_time/60:.2f} minutes)")
            print(f"Start Time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"End Time: {self.end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # URL statistics
        print(f"\nURLs Processed: {len(self.urls_processed)}")
        
        # Average processing time
        if self.url_times:
            all_times = []
            for times in self.url_times.values():
                all_times.extend(times)
            
            if all_times:
                avg_time = sum(all_times) / len(all_times)
                print(f"Average URL Processing Time: {avg_time:.2f} seconds")
                print(f"Fastest URL: {min(all_times):.2f} seconds")
                print(f"Slowest URL: {max(all_times):.2f} seconds")
        
        # Strategy statistics
        if self.strategies:
            print("\nStrategies Used:")
            for strategy, count in self.strategies.most_common():
                print(f"  {strategy}: {count} times")
        
        # Error statistics
        if self.errors:
            print(f"\nErrors/Warnings ({len(self.errors)}):")
            for i, error in enumerate(self.errors[:5]):  # Show only the first 5 errors
                print(f"  {error}")
            
            if len(self.errors) > 5:
                print(f"  ... and {len(self.errors) - 5} more")
    
    def generate_charts(self, output_file=None):
        """Generate visual charts of the crawler performance."""
        try:
            plt.figure(figsize=(15, 10))
            
            # Strategy usage chart
            if self.strategies:
                plt.subplot(2, 1, 1)
                strategies = [s for s, _ in self.strategies.most_common()]
                counts = [c for _, c in self.strategies.most_common()]
                plt.bar(strategies, counts, color='skyblue')
                plt.title('Strategy Usage')
                plt.xlabel('Strategy')
                plt.ylabel('Number of Times Used')
                plt.xticks(rotation=45)
                
            # Processing time chart if we have time data
            if self.url_times:
                plt.subplot(2, 1, 2)
                all_times = []
                for times in self.url_times.values():
                    all_times.extend(times)
                
                if all_times:
                    plt.hist(all_times, bins=20, color='lightgreen')
                    plt.title('URL Processing Time Distribution')
                    plt.xlabel('Time (seconds)')
                    plt.ylabel('Number of URLs')
            
            plt.tight_layout()
            
            if output_file:
                plt.savefig(output_file)
                print(f"Charts saved to {output_file}")
            else:
                plt.savefig("crawler_performance.png")
                print("Charts saved to crawler_performance.png")
                
            plt.show()
            
        except ImportError:
            print("Matplotlib is required for generating charts. Install with: pip install matplotlib")
        except Exception as e:
            print(f"Error generating charts: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description="Analyze DuskToDawn crawler logs")
    parser.add_argument('log_file', nargs='?', default='crawler_detailed.log',
                      help='Path to the crawler log file')
    parser.add_argument('--charts', action='store_true', help='Generate performance charts')
    parser.add_argument('--output', help='Output file for charts (PNG format)')
    
    args = parser.parse_args()
    
    analyzer = CrawlerLogAnalyzer(args.log_file)
    analyzer.parse_log()
    analyzer.display_stats()
    
    if args.charts:
        analyzer.generate_charts(args.output)

if __name__ == "__main__":
    main()

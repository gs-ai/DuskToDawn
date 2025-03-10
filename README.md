# DuskToDawn Web Intelligence Crawler

A stealth web intelligence crawler that collects and analyzes mentions of specific individuals across the internet. DuskToDawn uses advanced anonymity techniques through Tor integration to maintain operational security while gathering intelligence.

## Features

- **Dual Crawler Architecture**: Choose between standard and enhanced crawling capabilities
- **Tor Integration**: All connections route through Tor for anonymity with automatic circuit rotation
- **Anti-Detection Measures**: Advanced browser fingerprint manipulation and human-like behavior simulation
- **Sentiment Analysis**: Automatic analysis of mentions and their context
- **State Persistence**: Maintains crawler state between sessions
- **Data Analysis Tools**: Visualize and export findings

## Installation

### Prerequisites

- Python 3.7+
- Tor service installed and running on default ports (9050/9051)

### Setup

1. Clone the repository
   ```
   git clone https://github.com/gs-ai/DuskToDawn
   cd DuskToDawn
   ```

2. Create and activate a virtual environment
   ```
   python -m venv reaperENV
   source reaperENV/bin/activate  # On Windows: reaperENV\Scripts\activate
   ```

3. Install dependencies
   ```
   pip install -r requirements.txt
   ```

4. Ensure Tor is running
   ```
   # Check Tor connectivity
   python tor_manager.py --test
   ```

## Usage

### Basic Usage

Run the crawler with:

```bash
# Standard mode
python run_reaper.py

# Enhanced stealth mode (better for sites with anti-bot protection)
python run_reaper.py --enhanced

# With debug output
python run_reaper.py --debug
```

### Input Parameters

When the crawler starts, it will ask for the following information:

- **Target Name**: Enter the person's name you're researching (format: first last)
- **Seed URL**: Starting point for the crawl (e.g., target's company website)
- **Additional URLs**: Optional additional starting points (press Enter on a blank line when done)
- **Organization**: The target's organization or company (optional)
- **Keywords**: Additional terms to search for (optional, one per line)

### Example Session

```
===== Enhanced Web Intelligence Crawler =====
Enter target name (first last): Elon Musk
Enter primary seed URL: https://tesla.com
Enter additional seed URLs (one per line, blank line to finish):
> https://spacex.com
> https://twitter.com/elonmusk
> 
Enter target's organization/company (optional): Tesla
Enter additional keywords to monitor (one per line, blank line to finish):
> X Corp
> Neuralink
> 

Starting crawler with 3 seed URLs
Looking for mentions of: Elon Musk, Musk, Elon and 13 other variations
```

## Features

- **Multiple Crawler Modes**
  - Standard: Balanced approach suitable for most websites
  - Enhanced: More sophisticated anti-detection techniques for harder targets

- **Anti-Detection Capabilities**
  - Browser fingerprinting evasion
  - Multiple access strategies with automatic fallback
  - Random user agent rotation
  - Realistic human-like browsing patterns
  - Automatic Cloudflare/CAPTCHA detection

- **Anonymity**
  - Automatic Tor circuit rotation
  - IP address verification
  - Control port management

- **Content Analysis**
  - Advanced name variation generation
  - Context extraction around name mentions
  - Sentiment analysis of discovered content

- **Robustness**
  - Resource leak prevention
  - Persistent crawl state (can be resumed)
  - Graceful error handling and shutdown
  - Respects robots.txt protocols
  - Adaptive rate limiting

## Output Files

- **crawler_log.json**: Contains all matches found with extracted context and sentiment analysis
- **scraped_data/**: Directory with compressed HTML of all visited pages
- **crawler_detailed.log**: Detailed crawl activity log for debugging
- **visited_urls.pkl**: Pickle file with all visited URLs (for resuming crawls)
- **queue.pkl**: Pickle file with URLs queued for crawling
- **failed_urls.pkl**: Pickle file with URLs that failed to be processed

## Analyzing Results

After running the crawler, you can analyze your findings with:

```bash
python analyze_results.py
```

Additional options:
```bash
# Limit the number of detailed mentions to display
python analyze_results.py --limit 10

# Export results to CSV
python analyze_results.py --csv

# Create visualizations
python analyze_results.py --viz
```

The analyzer will:
1. Show a summary of all detected mentions
2. Display detailed context around each mention
3. Generate sentiment analysis statistics
4. Create visualizations of domain distribution and sentiment

## Tor Management

DuskToDawn includes a Tor management utility:

```bash
# Test Tor connectivity
python tor_manager.py --test

# Renew your Tor circuit (get a new IP)
python tor_manager.py --renew

# Monitor multiple circuit changes
python tor_manager.py --monitor 5 --delay 30
```

## Troubleshooting

If you encounter issues, check the TROUBLESHOOTING.md file for solutions to common problems.

Common issues:
- Tor connectivity problems
- HTTP 403 Forbidden errors (like the one encountered with tesla.com)
- Websites blocking crawlers
- Resource leaks on shutdown
- Memory usage issues

## Security Considerations

- **Legal Compliance**: Always ensure you're operating within legal boundaries and have proper authorization.
- **Rate Limiting**: The crawler implements delays to avoid overloading websites.
- **Data Protection**: Be mindful of storing and processing any sensitive information.
- **Network Security**: Using Tor provides anonymity but isn't a guarantee of complete security.
- **Attribution Risks**: Even with precautions, sophisticated targets might detect crawling activity.

## Advanced Configuration

For advanced users, both crawler implementations (`deep_reaper.py` and `enhanced_reaper.py`) can be modified to:
- Adjust thread counts for performance
- Customize browser fingerprinting
- Add specialized parsing for specific website types
- Implement additional stealth techniques
- Extend content analysis capabilities

## Project Structure

- **deep_reaper.py**: Standard crawler implementation
- **enhanced_reaper.py**: Advanced crawler with better anti-detection features
- **run_reaper.py**: Launcher script to start either crawler
- **tor_manager.py**: Tor connection testing and management
- **analyze_results.py**: Tool for analyzing crawler findings
- **utils/cleanup.py**: Resource management utilities
- **requirements.txt**: Python dependencies
- **TROUBLESHOOTING.md**: Additional help for common issues

## License & Usage

This tool is provided for educational and legitimate research purposes only. Always respect website terms of service, robots.txt directives, and applicable laws when conducting OSINT research.

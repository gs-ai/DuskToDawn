![DuskToDawn Banner](11e5a2fd-cf9f-476e-b972-d9cdfef68d6b.png)

# DuskToDawn Web Intelligence Crawler

[![Python](https://img.shields.io/badge/Python-3.7%2B-blue?logo=python)](https://www.python.org/) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A professional, stealth web intelligence crawler that collects and analyzes mentions of specific individuals across the internet. DuskToDawn uses advanced anonymity techniques through Tor integration to maintain operational security while gathering intelligence.

---

## Features

- **Dual Crawler Architecture**: Choose between standard and enhanced crawling capabilities
- **Tor Integration**: All connections route through Tor for anonymity with automatic circuit rotation
- **Anti-Detection Measures**: Advanced browser fingerprint manipulation and human-like behavior simulation
- **Sentiment Analysis**: Automatic analysis of mentions and their context
- **State Persistence**: Maintains crawler state between sessions
- **Data Analysis Tools**: Visualize and export findings

---

## Installation

### Prerequisites

- Python 3.7+
- Conda (Anaconda or Miniconda)
- Tor service installed and running on default ports (9050/9051)

### Setup

1. Clone the repository
   ```sh
   git clone https://github.com/gs-ai/DuskToDawn
   cd DuskToDawn
   ```

2. Create and activate a conda environment
   ```sh
   conda create -n reaperENV python=3.11
   conda activate reaperENV
   ```

3. Install dependencies
   ```sh
   pip install -r requirements.txt
   ```

4. Ensure Tor is running
   ```sh
   # Check Tor connectivity
   python tor_manager.py --test
   ```

---

## Usage

### Basic Usage

Run the crawler with:

```bash
# Standard mode
python Reapers/run_reaper.py

# Enhanced stealth mode (better for sites with anti-bot protection)
python Reapers/run_reaper.py --enhanced

# With debug output
python Reapers/run_reaper.py --debug
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

---

## Project Structure

```
DuskToDawn/
├── Reapers/
│   ├── deep_reaper.py
│   ├── enhanced_reaper.py
│   └── run_reaper.py
├── utils/
│   ├── cleanup.py
│   └── log_analyzer.py
├── analyze_results.py
├── tor_manager.py
├── requirements.txt
├── README.md
└── ...
```

---

## Output Files

- **crawler_log.json**: Contains all matches found with extracted context and sentiment analysis
- **scraped_data/**: Directory with compressed HTML of all visited pages
- **crawler_detailed.log**: Detailed crawl activity log for debugging
- **visited_urls.pkl**: Pickle file with all visited URLs (for resuming crawls)
- **queue.pkl**: Pickle file with URLs queued for crawling
- **failed_urls.pkl**: Pickle file with URLs that failed to be processed

---

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

---

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

---

## Troubleshooting

If you encounter issues, check the TROUBLESHOOTING.md file for solutions to common problems.

Common issues:
- Tor connectivity problems
- HTTP 403 Forbidden errors (like the one encountered with tesla.com)
- Websites blocking crawlers
- Resource leaks on shutdown
- Memory usage issues

---

## Security Considerations

- **Legal Compliance**: Always ensure you're operating within legal boundaries and have proper authorization.
- **Rate Limiting**: The crawler implements delays to avoid overloading websites.
- **Data Protection**: Be mindful of storing and processing any sensitive information.
- **Network Security**: Using Tor provides anonymity but isn't a guarantee of complete security.
- **Attribution Risks**: Even with precautions, sophisticated targets might detect crawling activity.

---

## Advanced Configuration

For advanced users, both crawler implementations (`deep_reaper.py` and `enhanced_reaper.py`) can be modified to:
- Adjust thread counts for performance
- Customize browser fingerprinting
- Add specialized parsing for specific website types
- Implement additional stealth techniques
- Extend content analysis capabilities

---

# DuskToDawn Program Overview

This project contains several Python programs and modules for web intelligence crawling, data collection, and analysis. Below is a summary of what each main program does:

## Main Programs

- **clean_crawler_state.py**
  - Cleans all crawler state, log, and data files/directories. Optionally creates backups before deleting. Use this to reset the crawler for a fresh start.

- **combine_scraped_data.py**
  - Combines all scraped HTML data (from `scraped_data/`) and matches it with crawler state from `.pkl` files. Outputs a single searchable JSON file (`all_scraped_content.json`) containing the text and status of each page.

- **analyze_results.py**
  - Loads and analyzes crawler results from `crawler_log.json`. Summarizes findings, shows detailed mentions, exports to CSV, and creates visualizations of the data.

- **tor_manager.py**
  - Utility for managing and testing Tor connectivity. Can check Tor status, renew circuits, and monitor IP changes.

## Crawler Programs (in `Reapers/`)

- **run_reaper.py**
  - Main entry point for running the crawler. Launches either the standard or enhanced crawler, checks Tor, and manages execution.

- **deep_reaper.py**
  - Standard crawler implementation. Crawls the web, collects mentions of target names/keywords, and logs results. Uses Tor for anonymity.

- **enhanced_reaper.py**
  - Advanced crawler with enhanced anti-detection and stealth features. Supports more sophisticated crawling and evasion techniques.

## Utilities (in `utils/`)

- **cleanup.py**
  - Resource management and cleanup utilities for safe shutdown and resource release.

- **log_analyzer.py**
  - Analyzes detailed crawler logs for performance, errors, and strategy usage. Generates statistics and charts from `crawler_detailed.log`.

---

For more details on usage, see the individual script docstrings or run each script with `--help`.

## License & Usage

This tool is provided for educational and legitimate research purposes only. Always respect website terms of service, robots.txt directives, and applicable laws when conducting OSINT research.

import os
import re
import csv
import time
import random
import signal
import requests
import itertools
import socks
import socket
import pickle
import json
import zlib
import threading
import gzip
import sys
import logging
import tempfile
from urllib.parse import urljoin, urlparse
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from textblob import TextBlob
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from fake_useragent import UserAgent
import undetected_chromedriver as uc
from robotexclusionrulesparser import RobotExclusionRulesParser
from concurrent.futures import ThreadPoolExecutor, as_completed
from http.cookiejar import CookieJar
from utils.cleanup import register_executor, register_cleanup_handler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('crawler_detailed.log')
    ]
)
logger = logging.getLogger('EnhancedReaper')

class RetryStrategy:
    """Handles retry logic with exponential backoff and different access strategies."""
    
    def __init__(self, max_retries=5):
        self.max_retries = max_retries
        self.strategies = [
            self._direct_request,
            self._selenium_request,
            self._tor_request,
            self._selenium_with_tor,
            self._aggressive_selenium
        ]
        
    def _direct_request(self, crawler, url):
        """Standard request using requests library with randomized headers."""
        headers = crawler._generate_random_headers()
        session = crawler.regular_session
        response = session.get(url, headers=headers, timeout=(5, 20), allow_redirects=True)
        response.raise_for_status()
        return response.content
        
    def _tor_request(self, crawler, url):
        """Request using Tor circuit."""
        crawler.renew_tor_ip()
        headers = crawler._generate_random_headers()
        response = crawler.tor_session.get(url, headers=headers, timeout=(6, 25))
        response.raise_for_status()
        return response.content
        
    def _selenium_request(self, crawler, url):
        """Standard undetected selenium approach."""
        driver = crawler._get_selenium_driver()
        try:
            driver.get(url)
            time.sleep(random.uniform(2, 4))
            return driver.page_source
        finally:
            driver.quit()
            
    def _selenium_with_tor(self, crawler, url):
        """Selenium through Tor proxy."""
        crawler.renew_tor_ip()
        driver = crawler._get_selenium_driver(use_tor=True)
        try:
            driver.get(url)
            time.sleep(random.uniform(3, 5))
            return driver.page_source
        finally:
            driver.quit()
            
    def _aggressive_selenium(self, crawler, url):
        """Advanced selenium approach with extensive human-like behavior."""
        driver = crawler._get_selenium_driver(stealth_level="high")
        try:
            # Random starting viewport
            viewport_width = random.randint(1024, 1920)
            viewport_height = random.randint(768, 1080)
            driver.set_window_size(viewport_width, viewport_height)
            
            # Load page
            driver.get(url)
            
            # Wait for page to stabilize
            time.sleep(random.uniform(4, 7))
            
            # Simulate human behavior
            self._simulate_human_behavior(driver)
            
            # Check if CloudFlare or similar protection is active
            if self._detect_antibot_page(driver):
                self._solve_antibot_challenges(driver)
                
            # Double check we have content
            wait = WebDriverWait(driver, 10)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            return driver.page_source
        finally:
            driver.quit()
            
    def _simulate_human_behavior(self, driver):
        """Add realistic user interactions."""
        actions = ActionChains(driver)
        
        # Random scrolling behavior
        for _ in range(random.randint(2, 5)):
            scroll_amount = random.randint(100, 500)
            driver.execute_script(f"window.scrollBy(0, {scroll_amount})")
            time.sleep(random.uniform(0.5, 1.5))
            
        # Random mouse movements
        for _ in range(random.randint(2, 4)):
            actions.move_by_offset(random.randint(-50, 50), random.randint(-50, 50))
            actions.pause(random.uniform(0.1, 0.3))
        actions.perform()
        
        # Sometimes click on a random non-link element
        if random.random() < 0.3:
            try:
                paragraphs = driver.find_elements(By.TAG_NAME, "p")
                if paragraphs:
                    random.choice(paragraphs).click()
            except:
                pass
                
        time.sleep(random.uniform(1, 2))
            
    def _detect_antibot_page(self, driver):
        """Detect common anti-bot protection systems."""
        page_source = driver.page_source.lower()
        antibot_indicators = [
            "captcha", "cloudflare", "human verification",
            "robot", "automated", "bot check", "security check",
            "prove you're human", "ddos protection"
        ]
        
        return any(indicator in page_source for indicator in antibot_indicators)
        
    def _solve_antibot_challenges(self, driver):
        """Attempt to solve or bypass common anti-bot challenges."""
        # Wait longer for challenges to process
        time.sleep(10)
        
        # Look for common checkbox captcha
        try:
            frames = driver.find_elements(By.TAG_NAME, "iframe")
            for frame in frames:
                try:
                    driver.switch_to.frame(frame)
                    checkboxes = driver.find_elements(By.CSS_SELECTOR, 
                                                    "input[type='checkbox'], .recaptcha-checkbox")
                    for checkbox in checkboxes:
                        checkbox.click()
                        time.sleep(2)
                except:
                    pass
                driver.switch_to.default_content()
        except:
            pass
            
        # Wait for redirects
        time.sleep(5)
            
    def execute(self, crawler, url):
        """Try different strategies with exponential backoff."""
        errors = []
        
        for attempt in range(self.max_retries):
            strategy_index = min(attempt, len(self.strategies) - 1)
            strategy = self.strategies[strategy_index]
            
            try:
                logger.info(f"Attempt {attempt+1} using strategy: {strategy.__name__} for URL: {url}")
                return strategy(crawler, url)
            except Exception as e:
                backoff_time = min(2 ** attempt + random.uniform(0, 1), 60)
                errors.append(f"{strategy.__name__}: {str(e)}")
                logger.warning(f"Strategy {strategy.__name__} failed: {str(e)}. Retrying in {backoff_time:.2f}s")
                time.sleep(backoff_time)
                
        raise Exception(f"All retry strategies failed after {self.max_retries} attempts. Errors: {errors}")

class EnhancedStealthCrawler:
    def __init__(self):
        self._init_debug("[DEBUG] Initializing EnhancedStealthCrawler...")
        self.name_variations = []
        self.visited_urls = self._load_state('visited_urls.pkl') or set()
        self.queue = self._load_state('queue.pkl') or []
        self.failed_urls = self._load_state('failed_urls.pkl') or {}
        self.setup_sessions()
        self.robots_parser = RobotExclusionRulesParser()
        self.ua = UserAgent()
        self.running = True
        self.executor = ThreadPoolExecutor(max_workers=2)  # Lower concurrency for stealth
        register_executor(self.executor)  # Register for cleanup
        self.lock = threading.Lock()
        self.state_file_interval = 180  # 3 minutes
        self.last_state_save = time.time()
        self.retry_strategy = RetryStrategy()
        self._init_components()
        register_cleanup_handler(self._save_state)  # Register state saving as cleanup handler
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    def _init_components(self):
        self.log_file = 'crawler_log.json'
        self.data_dir = 'scraped_data'
        self.tor_check_url = 'https://check.torproject.org/api/ip'
        self.setup_directories()
        self._verify_tor_connection()
        self._load_advanced_headers()
        self._create_browser_profiles()

    def _init_debug(self, message):
        debug_enabled = os.getenv('CRAWLER_DEBUG', 'false').lower() == 'true'
        if debug_enabled:
            print(message)

    def _load_advanced_headers(self):
        self.headers_templates = [
            {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept-Language': 'en-US,en;q=0.9',
                'Upgrade-Insecure-Requests': '1',
                'DNT': str(random.randint(0, 1)),
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Pragma': 'no-cache',
                'Cache-Control': 'no-cache'
            },
            {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Encoding': 'gzip, deflate',
                'Accept-Language': 'en-US,en;q=0.5',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Pragma': 'no-cache'
            },
            {
                'Accept': '*/*',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept-Language': 'en-GB,en;q=0.9',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'cross-site',
                'Sec-Fetch-Dest': 'document',
            }
        ]

    def _get_selenium_driver(self, use_tor=False, stealth_level="normal"):
        options = uc.ChromeOptions()
        
        # Profile handling
        profile_dir = self.profile_dirs[random.randint(0, len(self.profile_dirs)-1)]
        options.add_argument(f"--user-data-dir={profile_dir}")
        
        # Add common options
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument(f"--window-size={random.randint(1024,1920)},{random.randint(768,1080)}")
        options.set_capability("goog:loggingPrefs", {'performance': 'ALL'})
        
        if stealth_level == "high":
            # Extreme anti-detection measures
            options.add_argument("--disable-web-security")
            options.add_argument("--ignore-certificate-errors")
            options.add_argument("--allow-running-insecure-content")
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-sync")
            options.add_argument("--disable-default-apps")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-popup-blocking")
            options.add_argument("--disable-gpu")
            options.add_argument("--disable-notifications")
            options.add_argument("--disable-software-rasterizer")
            options.add_argument("--disable-dev-shm-usage")
        elif stealth_level == "low":
            # Basic settings, less suspicious
            options.add_argument("--headless=new")
        else:
            # Normal level
            if random.random() < 0.3:  # Sometimes use headless
                options.add_argument("--headless=new")
                
        if use_tor:
            options.add_argument("--proxy-server=socks5://127.0.0.1:9050")
        
        # Set a convincing user agent
        selected_ua = self.ua.random
        options.add_argument(f"--user-agent={selected_ua}")
        
        driver = uc.Chrome(options=options)
        
        # Execute stealth steps
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {
                  get: () => undefined
                });
                Object.defineProperty(navigator, 'languages', {
                  get: () => ['en-US', 'en', 'es']
                });
                Object.defineProperty(navigator, 'plugins', {
                  get: () => [
                    {},
                    {},
                    {},
                    {},
                    {},
                  ]
                });
            """
        })
        
        return driver

    def _create_browser_profiles(self):
        """Create persistent browser profiles to look more legitimate."""
        self.profile_dirs = []
        for i in range(3):
            profile_dir = os.path.join(tempfile.gettempdir(), f"crawler_profile_{i}")
            os.makedirs(profile_dir, exist_ok=True)
            self.profile_dirs.append(profile_dir)
            
    def _generate_random_headers(self):
        """Generate random-but-realistic headers for requests."""
        template = random.choice(self.headers_templates).copy()
        template['User-Agent'] = self.ua.random
        
        # Add some randomness to headers
        if random.random() < 0.3:
            template['Referer'] = f"https://www.google.com/search?q={'+'.join(random.sample(['news', 'latest', 'info', 'about'], 2))}"
            
        if random.random() < 0.2:
            template['X-Forwarded-For'] = f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"
            
        return template

    def _verify_tor_connection(self):
        try:
            response = self.tor_session.get(self.tor_check_url, timeout=10)
            tor_status = response.json().get('IsTor', False)
            logger.info(f"Tor connection status: {'Active' if tor_status else 'Inactive'}")
            if not tor_status:
                logger.warning("Tor connection verification failed. Check Tor settings.")
        except Exception as e:
            logger.warning(f"Tor verification error: {str(e)}. Continuing anyway.")

    def setup_sessions(self):
        # Regular session
        self.regular_session = requests.Session()
        self.regular_session.mount('http://', requests.adapters.HTTPAdapter(
            max_retries=3,
            pool_connections=10,
            pool_maxsize=20
        ))
        self.regular_session.mount('https://', requests.adapters.HTTPAdapter(
            max_retries=3,
            pool_connections=10,
            pool_maxsize=20
        ))
        
        # Tor session
        self.tor_session = requests.Session()
        self.tor_session.proxies.update({
            'http': 'socks5h://127.0.0.1:9050',
            'https': 'socks5h://127.0.0.1:9050'
        })
        self.tor_session.mount('http://', requests.adapters.HTTPAdapter(
            max_retries=3,
            pool_connections=10,
            pool_maxsize=20
        ))
        self.tor_session.mount('https://', requests.adapters.HTTPAdapter(
            max_retries=3,
            pool_connections=10, 
            pool_maxsize=20
        ))

    def renew_tor_ip(self):
        logger.info("Attempting to renew Tor circuit...")
        max_retries = 3
        for attempt in range(max_retries):
            try:
                with socket.create_connection(('127.0.0.1', 9051), timeout=5) as ctrl_socket:
                    ctrl_socket.sendall(b'AUTHENTICATE ""\r\n')
                    response = ctrl_socket.recv(1024)
                    if b'250' not in response:
                        raise RuntimeError("Tor authentication failed")
                    
                    ctrl_socket.sendall(b'SIGNAL NEWNYM\r\n')
                    response = ctrl_socket.recv(1024)
                    if b'250' not in response:
                        raise RuntimeError("Tor circuit renewal failed")
                    
                    time.sleep(random.uniform(1.0, 2.0))  # Wait for circuit change
                    logger.info("Tor circuit renewed successfully")
                    return
            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error(f"Tor renewal failed: {str(e)}")
                time.sleep(2 ** attempt)
        
        logger.warning("Could not renew Tor circuit - will continue with current IP")

    def setup_directories(self):
        os.makedirs(self.data_dir, exist_ok=True)
        if not os.path.exists(self.log_file):
            with open(self.log_file, 'w') as f:
                json.dump([], f)

    def _load_state(self, filename):
        try:
            with open(filename, 'rb') as f:
                return pickle.load(f)
        except FileNotFoundError:
            return None
        except Exception as e:
            logger.warning(f"Failed to load state from {filename}: {str(e)}")
            return None

    def _save_state(self):
        try:
            with open('visited_urls.pkl', 'wb') as f:
                pickle.dump(self.visited_urls, f)
            with open('queue.pkl', 'wb') as f:
                pickle.dump(self.queue, f)
            with open('failed_urls.pkl', 'wb') as f:
                pickle.dump(self.failed_urls, f)
            self.last_state_save = time.time()
            logger.debug("Crawler state saved")
        except Exception as e:
            logger.error(f"Failed to save state: {str(e)}")

    def _check_robots_txt(self, url):
        parsed = urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        try:
            response = self.regular_session.get(robots_url, timeout=5)
            self.robots_parser.parse(response.text)
            return self.robots_parser.is_allowed('*', url)
        except Exception:
            return True

    def process_page(self, url):
        try:
            if not self._check_robots_txt(url):
                logger.info(f"Skipping - blocked by robots.txt: {url}")
                return

            logger.info(f"Processing: {url}")
            content = self.retry_strategy.execute(self, url)
            
            if not content:
                logger.warning(f"No content retrieved from {url}")
                return

            # Randomized IP rotation
            if random.random() < 0.2:
                self.renew_tor_ip()

            soup = BeautifulSoup(content, 'html.parser')
            self._analyze_content(soup, url)
            self._save_content(content, url)
            self._enqueue_links(soup, url)

            if time.time() - self.last_state_save > self.state_file_interval:
                self._save_state()

            # Adaptive pause to avoid detection
            time.sleep(random.weibullvariate(3.0, 0.7))
            
        except Exception as e:
            logger.error(f"Error processing {url}: {str(e)}")
            with self.lock:
                self.failed_urls[url] = str(e)

    def _analyze_content(self, soup, url):
        text = soup.get_text(separator=' ', strip=True)
        context_analysis = TextBlob(text)
        
        for variation in self.name_variations:
            if re.search(rf'\b{re.escape(variation)}\b', text, re.I):
                context = self._extract_context(text, variation)
                self._log_match(url, variation, context, sentiment=context_analysis.sentiment)
                # Show hit in console with color
                print(f"\033[92m[HIT]\033[0m Found mention of '{variation}' on {url}")
                break

    def _extract_context(self, text, variation, window=150):
        match = re.search(rf'\b{re.escape(variation)}\b', text, re.I)
        if match:
            start = max(0, match.start() - window)
            end = min(len(text), match.end() + window)
            return text[start:end].replace('\n', ' ').strip()
        return ''

    def _log_match(self, url, variation, context, sentiment):
        entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'url': url,
            'variation': variation,
            'context': context,
            'sentiment': {'polarity': sentiment.polarity, 'subjectivity': sentiment.subjectivity},
        }
        with self.lock:
            with open(self.log_file, 'a') as f:
                f.write(json.dumps(entry) + '\n')

    def _save_content(self, content, url):
        filename = f"{hash(url)}_{int(time.time())}.html.gz"
        path = os.path.join(self.data_dir, filename)
        try:
            with gzip.open(path, 'wb') as f:
                if isinstance(content, str):
                    f.write(content.encode('utf-8'))
                else:
                    f.write(content)
        except Exception as e:
            logger.warning(f"Failed to save content for {url}: {str(e)}")

    def _enqueue_links(self, soup, base_url):
        with self.lock:
            new_links = set()
            for link in soup.find_all('a', href=True):
                try:
                    full_url = urljoin(base_url, link['href']).split('#')[0]
                    if self._validate_url(full_url):
                        new_links.add(full_url)
                except Exception as e:
                    logger.debug(f"Error processing link: {str(e)}")
            
            filtered_links = list(new_links - self.visited_urls)
            
            # Prioritize links from the same domain
            base_domain = urlparse(base_url).netloc
            same_domain = [url for url in filtered_links if urlparse(url).netloc == base_domain]
            other_domain = [url for url in filtered_links if urlparse(url).netloc != base_domain]
            
            self.queue.extend(same_domain + other_domain)
            logger.info(f"Added {len(filtered_links)} new URLs to queue")

    def _validate_url(self, url):
        parsed = urlparse(url)
        if parsed.scheme not in ('http', 'https'):
            return False
        if parsed.netloc in self._get_blacklist():
            return False
        if re.search(r'\.(jpg|jpeg|png|gif|pdf|docx?|xlsx?|zip|rar|gz|tar|mp[34]|avi|mov)$', parsed.path, re.I):
            return False
        return True

    def _get_blacklist(self):
        return {
            'localhost',
            '127.0.0.1',
            'example.com',
            'facebook.com',
            'twitter.com',
            'instagram.com',
            'youtube.com',
            'tiktok.com',
            # Add more domains to block as needed
        }

    def run(self):
        self._collect_target_info()
        print(f"Starting crawler with {len(self.queue)} seed URLs")
        print(f"Looking for mentions of: {', '.join(self.name_variations[:3])} and {len(self.name_variations)-3} other variations")
        
        while self.running and self.queue:
            with self.lock:
                if not self.queue:
                    break
                    
                # Prioritize unexplored domains
                explored_domains = {urlparse(u).netloc for u in self.visited_urls}
                for i, url in enumerate(self.queue):
                    if urlparse(url).netloc not in explored_domains:
                        current_url = self.queue.pop(i)
                        break
                else:
                    current_url = self.queue.pop(0)
                    
                if current_url in self.visited_urls:
                    continue
                self.visited_urls.add(current_url)
            
            self.executor.submit(self.process_page, current_url)
            
            # Update progress periodically
            if len(self.visited_urls) % 10 == 0:
                print(f"Progress: {len(self.visited_urls)} URLs visited, {len(self.queue)} in queue")
        
        self.executor.shutdown(wait=True)
        self._save_state()
        logger.info(f"Crawl complete. Visited {len(self.visited_urls)} URLs.")

    def _collect_target_info(self):
        print("===== Enhanced Web Intelligence Crawler =====")
        name = input("Enter target name (first last): ").strip()
        parts = name.split()
        
        if len(parts) < 2:
            print("Please provide at least a first and last name.")
            sys.exit(1)
            
        first, last = parts[0], parts[-1]
        middle = ' '.join(parts[1:-1]) if len(parts) > 2 else ""
        
        self.name_variations = self._generate_name_variations(first, middle, last)
        
        # Collect seed URLs
        seed_url = input("Enter primary seed URL: ").strip()
        self.queue.append(seed_url)
        
        # Add additional seed URLs
        print("Enter additional seed URLs (one per line, blank line to finish):")
        while True:
            url = input("> ").strip()
            if not url:
                break
            self.queue.append(url)
            
        # Ask if adding company/organization context
        org = input("Enter target's organization/company (optional): ").strip()
        if org:
            self.name_variations.extend([
                f"{first} {last} {org}",
                f"{first} {last}, {org}",
                f"{org} {first} {last}"
            ])
            
        # Additional keywords
        print("Enter additional keywords to monitor (one per line, blank line to finish):")
        while True:
            keyword = input("> ").strip()
            if not keyword:
                break
            self.name_variations.append(keyword)

    def _generate_name_variations(self, first, middle, last):
        variations = [
            f"{first} {last}",
            f"{last}, {first}",
            f"{first} {middle} {last}".strip(),
            f"{first[0]}. {last}",
            f"{first[0]}. {middle} {last}".strip(),
            f"{first[0]}{last}",
            f"{first}.{last}",
            f"{first}_{last}",
            f"{last}_{first}",
            # Additional variations
            f"{first}{last}",
            f"{first} {last[0]}",
            f"{last} {first}",
        ]
        
        # Filter out duplicates and empty strings
        return list(set(filter(None, variations)))

    def signal_handler(self, signum, frame):
        print("\n[INFO] Graceful shutdown initiated...")
        self.running = False
        self._save_state()
        self.executor.shutdown(wait=False)
        print("Crawler state saved. Exiting.")
        sys.exit(0)

if __name__ == "__main__":
    crawler = EnhancedStealthCrawler()
    crawler.run()

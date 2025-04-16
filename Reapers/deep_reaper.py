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
import threading  # Ensuring this import is properly placed and not commented
import gzip
import sys
from urllib.parse import urljoin, urlparse
from datetime import datetime
from bs4 import BeautifulSoup
from textblob import TextBlob
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from fake_useragent import UserAgent
import undetected_chromedriver as uc
from robotexclusionrulesparser import RobotExclusionRulesParser
from concurrent.futures import ThreadPoolExecutor, as_completed
from utils.cleanup import register_executor, register_cleanup_handler

class StealthCrawler:
    def __init__(self):
        self._init_debug("[DEBUG] Initializing HyperRobustStealthCrawler...")
        self.name_variations = []
        self.visited_urls = self._load_state('visited_urls.pkl') or set()
        self.queue = self._load_state('queue.pkl') or []
        self.session = self.setup_tor_session()
        self.robots_parser = RobotExclusionRulesParser()
        self.ua = UserAgent()
        self.running = True
        self.executor = ThreadPoolExecutor(max_workers=3)
        register_executor(self.executor)  # Register for cleanup
        self.lock = threading.Lock()
        self.state_file_interval = 300  # 5 minutes
        self.last_state_save = time.time()
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

    def _init_debug(self, message):
        debug_enabled = os.getenv('CRAWLER_DEBUG', 'false').lower() == 'true'
        if debug_enabled:
            print(message)

    def _load_advanced_headers(self):
        self.headers_template = {
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-US,en;q=0.9',
            'Upgrade-Insecure-Requests': '1',
            'DNT': str(random.randint(0, 1)),
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Pragma': 'no-cache',
            'Cache-Control': 'no-cache'
        }

    def _verify_tor_connection(self):
        try:
            response = self.session.get(self.tor_check_url, timeout=10)
            if not response.json().get('IsTor', False):
                raise RuntimeError("Tor connection verification failed")
        except Exception as e:
            self._emergency_shutdown(f"Critical Tor verification failed: {str(e)}")

    def _emergency_shutdown(self, message):
        print(f"[FATAL] {message}")
        self._save_state()
        os._exit(1)

    def setup_tor_session(self):
        session = requests.Session()
        session.proxies.update({
            'http': 'socks5h://127.0.0.1:9050',
            'https': 'socks5h://127.0.0.1:9050'
        })
        session.mount('http://', requests.adapters.HTTPAdapter(
            max_retries=3,
            pool_connections=20,
            pool_maxsize=100
        ))
        return session

    def renew_tor_ip(self):
        max_retries = 3
        for attempt in range(max_retries):
            try:
                with socket.create_connection(('127.0.0.1', 9051), timeout=5) as ctrl_socket:
                    # Try empty password authentication
                    ctrl_socket.sendall(b'AUTHENTICATE ""\r\n')
                    response = ctrl_socket.recv(1024)
                    if b'250' not in response:
                        # If authentication fails, skip renewal and warn
                        print("[WARNING] Tor authentication failed. Skipping circuit renewal.")
                        return
                    ctrl_socket.sendall(b'SIGNAL NEWNYM\r\n')
                    response = ctrl_socket.recv(1024)
                    if b'250' not in response:
                        print("[WARNING] Tor circuit renewal failed. Skipping renewal.")
                        return
                    old_ip = self.session.get('https://api.ipify.org').text
                    new_ip = self.session.get('https://api.ipify.org').text
                    if old_ip == new_ip:
                        raise RuntimeError("IP address did not change")
                    return
            except Exception as e:
                if attempt == max_retries - 1:
                    print(f"[WARNING] Tor renewal failed: {str(e)}. Skipping renewal.")
                time.sleep(2 ** attempt)

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
            print(f"[WARNING] Failed to load state: {str(e)}")
            return None

    def _save_state(self):
        try:
            with open('visited_urls.pkl', 'wb') as f:
                pickle.dump(self.visited_urls, f)
            with open('queue.pkl', 'wb') as f:
                pickle.dump(self.queue, f)
            self.last_state_save = time.time()
        except Exception as e:
            print(f"[ERROR] Failed to save state: {str(e)}")

    def _check_robots_txt(self, url):
        # Always allow crawling, ignore robots.txt
        return True

    def process_page(self, url):
        try:
            if not self._check_robots_txt(url):
                print(f"[INFO] Blocked by robots.txt: {url}")
                return

            content = self._fetch_content(url)
            if not content:
                return

            if random.random() < 0.1:
                self.renew_tor_ip()

            soup = BeautifulSoup(content, 'html.parser')
            self._analyze_content(soup, url)
            self._save_content(content, url)
            self._enqueue_links(soup, url)

            if time.time() - self.last_state_save > self.state_file_interval:
                self._save_state()

        except Exception as e:
            print(f"[ERROR] Processing {url}: {str(e)}")

    def _fetch_content(self, url):
        for attempt in range(3):
            try:
                if random.random() < 0.7:
                    return self._fetch_requests(url)
                return self._fetch_selenium(url)
            except Exception as e:
                print(f"[WARNING] Attempt {attempt+1} failed: {str(e)}")
                time.sleep(2 ** attempt)
        return None

    def _fetch_requests(self, url):
        headers = {'User-Agent': self.ua.random}
        headers.update(self.headers_template)
        response = self.session.get(
            url,
            headers=headers,
            timeout=(3.05, 15),
            allow_redirects=True,
            stream=True
        )
        response.raise_for_status()
        return response.content

    def _fetch_selenium(self, url):
        # Always create a fresh ChromeOptions object
        options = uc.ChromeOptions()
        options.add_argument("--headless=new")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument(f"--window-size={random.randint(800,1600)},{random.randint(600,1200)}")
        options.set_capability("goog:loggingPrefs", {'performance': 'ALL'})
        driver = uc.Chrome(options=options)
        try:
            driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                "userAgent": self.ua.random,
                "platform": random.choice(['Win32', 'MacIntel', 'Linux x86_64'])
            })
            
            # Simulate human-like interactions
            ActionChains(driver)\
                .move_by_offset(random.randint(1,5), random.randint(1,5))\
                .pause(random.uniform(0.1, 0.5))\
                .perform()

            driver.get(url)
            time.sleep(random.uniform(2, 5))
            
            # Random scrolling
            for _ in range(random.randint(0, 3)):
                driver.execute_script(f"window.scrollBy(0, {random.randint(200, 800)})")
                time.sleep(random.uniform(0.3, 1.2))

            return driver.page_source
        finally:
            driver.quit()

    def _analyze_content(self, soup, url):
        text = soup.get_text(separator=' ', strip=True)
        context_analysis = TextBlob(text)
        
        for variation in self.name_variations:
            if re.search(rf'\b{re.escape(variation)}\b', text, re.I):
                context = self._extract_context(text, variation)
                self._log_match(url, variation, context, sentiment=context_analysis.sentiment)
                break

    def _extract_context(self, text, variation, window=100):
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
            'source': 'requests' if random.random() < 0.7 else 'selenium'
        }
        with self.lock:
            with open(self.log_file, 'a') as f:
                f.write(json.dumps(entry) + '\n')

    def _save_content(self, content, url):
        filename = f"{hash(url)}_{int(time.time())}.html.gz"
        path = os.path.join(self.data_dir, filename)
        with gzip.open(path, 'wb') as f:
            if isinstance(content, str):
                f.write(content.encode('utf-8'))
            else:
                f.write(content)

    def _enqueue_links(self, soup, base_url):
        with self.lock:
            new_links = set()
            for link in soup.find_all('a', href=True):
                full_url = urljoin(base_url, link['href']).split('#')[0].split('?')[0]
                if self._validate_url(full_url):
                    new_links.add(full_url)
            self.queue.extend(list(new_links - self.visited_urls))

    def _validate_url(self, url):
        parsed = urlparse(url)
        if parsed.scheme not in ('http', 'https'):
            return False
        if parsed.netloc in self._get_blacklist():
            return False
        if re.search(r'\.(jpg|jpeg|png|gif|pdf|docx?|xlsx?)$', parsed.path, re.I):
            return False
        return True

    def _get_blacklist(self):
        return {
            'localhost',
            '127.0.0.1',
            'example.com',
            # Add more domains to block
        }

    def run(self):
        self._collect_target_info()
        while self.running and self.queue:
            with self.lock:
                current_url = self.queue.pop(0)
                if current_url in self.visited_urls:
                    continue
                self.visited_urls.add(current_url)
            
            self.executor.submit(self.process_page, current_url)
            
            # Adaptive rate limiting
            time.sleep(random.weibullvariate(1.5, 0.8))
        
        self.executor.shutdown(wait=True)
        self._save_state()

    def _collect_target_info(self):
        # Enhanced target information collection
        name = input("Enter target name (first last): ").strip()
        first, last = name.split()[:2]
        self.name_variations = self._generate_name_variations(first, last)
        seed_url = input("Enter seed URL: ").strip()
        # Allow user to enter URL without scheme (e.g., someurl.com)
        if not seed_url.startswith("http://") and not seed_url.startswith("https://"):
            seed_url = "https://" + seed_url
        self.queue.append(seed_url)
        # Add domain-specific variations
        self.name_variations.extend([
            f"{first}@company.com",
            f"{last}@company.com",
            f"{first[0]}{last}",
        ])

    def _generate_name_variations(self, first, last):
        return list(set(itertools.chain(
            [f"{first} {last}", f"{last}, {first}"],
            [f"{first} {m} {last}" for m in ['A.', 'B.', 'C.']],
            [f"{last}-{first}"],
            [f"{first_initial}.{last}" for first_initial in first[0]],
            [f"{last}{first_initial}" for first_initial in first[0]],
        )))

    def signal_handler(self, signum, frame):
        print("\n[INFO] Graceful shutdown initiated...")
        self.running = False
        self._save_state()
        self.executor.shutdown(wait=False)
        sys.exit(0)

if __name__ == "__main__":
    crawler = StealthCrawler()
    crawler.run()
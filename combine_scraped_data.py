import os
import gzip
import json
import pickle
from bs4 import BeautifulSoup

SCRAPED_DIR = "scraped_data"
OUTPUT_FILE = "all_scraped_content.json"

def load_pickle(filename):
    try:
        with open(filename, "rb") as f:
            return pickle.load(f)
    except Exception:
        return set() if "visited" in filename or "queue" in filename else {}

def extract_url_from_filename(filename, url_map):
    # If you have a mapping of filename to URL, use it here.
    # Otherwise, just return None.
    return url_map.get(filename)

def main():
    # Load .pkl files
    visited = load_pickle("visited_urls.pkl")
    queue = load_pickle("queue.pkl")
    failed = load_pickle("failed_urls.pkl")

    # Try to build a mapping from filename to URL if possible
    # If you have a mapping, load it here. Otherwise, this will be empty.
    filename_to_url = {}

    combined = []
    for fname in os.listdir(SCRAPED_DIR):
        if not fname.endswith(".html.gz"):
            continue
        path = os.path.join(SCRAPED_DIR, fname)
        try:
            with gzip.open(path, "rt", encoding="utf-8", errors="ignore") as f:
                html = f.read()
            soup = BeautifulSoup(html, "html.parser")
            text = soup.get_text(separator=" ", strip=True)
            url = extract_url_from_filename(fname, filename_to_url)
            # If you can't map filename to URL, just use None or the filename
            url = url or fname

            status = []
            if url in visited:
                status.append("visited")
            if url in queue:
                status.append("queued")
            if isinstance(failed, dict) and url in failed:
                status.append("failed")
            elif isinstance(failed, set) and url in failed:
                status.append("failed")

            combined.append({
                "filename": fname,
                "url": url,
                "status": status,
                "text": text
            })
        except Exception as e:
            print(f"Error processing {fname}: {e}")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as out:
        json.dump(combined, out, ensure_ascii=False, indent=2)
    print(f"Combined {len(combined)} files into {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
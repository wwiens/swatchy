#!/usr/bin/env python3
"""
Fetch JSON data from the Activory API by iterating through letters a-z.
Each response is saved as a separate JSON file.
"""

import json
import string
import time
from urllib.parse import quote

import requests


def fetch_letter_data():
    """Fetch data for each letter a-z and save to individual JSON files."""
    base_url = "https://tablemaster-v2.activory.com/api/v1/embed-tables/o5kdobkEDK/data"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "application/json",
    }

    for letter in string.ascii_lowercase:
        params = {
            "search[value]": letter
        }

        try:
            print(f"Fetching data for letter '{letter}'...")
            response = requests.get(base_url, params=params, headers=headers, timeout=30)
            response.raise_for_status()

            data = response.json()

            filename = f"search_{letter}.json"
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            print(f"  Saved to {filename}")

        except requests.exceptions.RequestException as e:
            print(f"  Error fetching letter '{letter}': {e}")
        except json.JSONDecodeError as e:
            print(f"  Error parsing JSON for letter '{letter}': {e}")
        except IOError as e:
            print(f"  Error writing file for letter '{letter}': {e}")

        # Rate limiting: wait 0.5 seconds between requests
        time.sleep(0.5)

    print("\nDone! Fetched data for all letters a-z.")


if __name__ == "__main__":
    fetch_letter_data()

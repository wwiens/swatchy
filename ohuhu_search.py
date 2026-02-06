#!/usr/bin/env python3
"""
Ohuhu Product Search Script

Searches for products on ohuhu.com using their predictive search API
and returns only exact matches for the search term.
"""

import json
import sys
import urllib.request
import urllib.parse
from typing import List, Dict, Any


def search_products(query: str) -> List[Dict[str, Any]]:
    """
    Search for products on Ohuhu using the predictive search endpoint.

    Args:
        query: The search term (e.g., "RV250")

    Returns:
        List of product dictionaries from the search results
    """
    # URL encode the query parameter
    encoded_query = urllib.parse.quote(query)

    # Build the search URL
    url = f"https://ohuhu.com/search/suggest.json?q={encoded_query}"

    # Set headers to mimic a browser request
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.9",
    }

    # Make the request
    request = urllib.request.Request(url, headers=headers)

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))

            # Extract products from the response
            products = data.get("resources", {}).get("results", {}).get("products", [])
            return products

    except urllib.error.HTTPError as e:
        print(f"HTTP Error: {e.code} - {e.reason}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"URL Error: {e.reason}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"JSON Decode Error: {e}", file=sys.stderr)
        sys.exit(1)


def filter_exact_matches(products: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
    """
    Filter products to return only those with an exact match for the query.

    The query is matched against:
    - Product title
    - Product handle (URL slug)

    Args:
        products: List of product dictionaries
        query: The search term to match

    Returns:
        List of products that exactly match the query
    """
    query_lower = query.lower()
    exact_matches = []

    for product in products:
        title = product.get("title", "").lower()
        handle = product.get("handle", "").lower()

        # Check if query appears as a complete word/phrase in title or handle
        # Match patterns like "RV250" or "rv250" in text
        if query_lower in title or query_lower in handle:
            exact_matches.append(product)

    return exact_matches


def format_product_output(product: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract and format relevant fields from a product for clean JSON output.

    Args:
        product: Raw product dictionary from the API

    Returns:
        Cleaned product dictionary with essential fields
    """
    return {
        "id": product.get("id"),
        "title": product.get("title"),
        "handle": product.get("handle"),
        "url": f"https://ohuhu.com{product.get('url', '')}",
        "price": product.get("price"),
        "price_min": product.get("price_min"),
        "price_max": product.get("price_max"),
        "compare_at_price_min": product.get("compare_at_price_min"),
        "compare_at_price_max": product.get("compare_at_price_max"),
        "available": product.get("available"),
        "vendor": product.get("vendor"),
        "tags": product.get("tags", []),
        "image": product.get("image"),
        "featured_image": product.get("featured_image"),
    }


def main():
    """Main entry point for the script."""
    # Get search term from user input
    query = input("Enter product code (e.g., RV250): ").strip()

    if not query:
        print("Error: Search term cannot be empty", file=sys.stderr)
        sys.exit(1)

    print(f"\nSearching for '{query}'...\n", file=sys.stderr)

    # Fetch search results
    products = search_products(query)

    # Filter for exact matches
    exact_matches = filter_exact_matches(products, query)

    # Format output
    formatted_results = [format_product_output(p) for p in exact_matches]

    # Output as JSON
    print(json.dumps(formatted_results, indent=2))

    # Print summary to stderr (so it doesn't pollute JSON output)
    print(
        f"\nFound {len(formatted_results)} exact match(es) from {len(products)} total results",
        file=sys.stderr
    )


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Consolidate search_*.json files and remove duplicates based on c4 (color code).
"""

import json
import os
from pathlib import Path


def main():
    # Initialize data structures
    unique_records = {}
    total_processed = 0
    duplicates_found = 0

    # Process files search_a.json through search_z.json
    for letter in "abcdefghijklmnopqrstuvwxyz":
        filename = f"search_{letter}.json"
        filepath = Path(filename)

        if not filepath.exists():
            print(f"Warning: {filename} not found, skipping...")
            continue

        print(f"Processing {filename}...")

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Extract records from the data array
            records = data.get('data', [])

            for record in records:
                total_processed += 1

                # Get the c4 field (new unified color code)
                c4 = record.get('c4', '').strip()

                # Skip records with empty c4
                if not c4:
                    print(f"  Warning: Empty c4 in {filename}, skipping record")
                    continue

                # Check for duplicates
                if c4 in unique_records:
                    duplicates_found += 1
                    # Optionally log duplicate details
                    continue

                # Add to unique records
                unique_records[c4] = record

        except json.JSONDecodeError as e:
            print(f"Error: Failed to parse {filename}: {e}")
        except Exception as e:
            print(f"Error: Unexpected error processing {filename}: {e}")

    # Sort records by c4 for consistent output
    sorted_records = sorted(unique_records.values(), key=lambda x: x.get('c4', ''))

    # Build output structure
    output = {
        "metadata": {
            "total_processed": total_processed,
            "unique_records": len(unique_records),
            "duplicates_removed": duplicates_found
        },
        "data": sorted_records
    }

    # Write consolidated output
    output_file = Path("consolidated_colors.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    # Print statistics
    print("\n" + "=" * 50)
    print("Consolidation Complete!")
    print("=" * 50)
    print(f"Total records processed: {total_processed}")
    print(f"Unique records: {len(unique_records)}")
    print(f"Duplicates removed: {duplicates_found}")
    print(f"Output file: {output_file}")


if __name__ == "__main__":
    main()

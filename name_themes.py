#!/usr/bin/env python3
"""
Theme Naming Script for Swatchy

Uses OpenAI API to generate clever, evocative names for all themes in generated_themes.json.
Processes themes in batches to optimize API usage and cost.
"""

import json
import os
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

# Configuration
BATCH_SIZE = 15
CHECKPOINT_FILE = "name_themes_checkpoint.json"
INPUT_FILE = "generated_themes.json"
BACKUP_FILE = "generated_themes_backup.json"
MODEL = "gpt-4o-mini"
TEMPERATURE = 0.7
MAX_TOKENS = 2000
DELAY_BETWEEN_BATCHES = 1  # seconds
MAX_RETRIES = 3

# Load environment variables
load_dotenv()


def load_themes():
    """Load themes from the input file."""
    with open(INPUT_FILE, "r") as f:
        data = json.load(f)
    return data["themes"]


def save_themes(themes):
    """Save themes back to the input file."""
    # Create backup first
    if not os.path.exists(BACKUP_FILE):
        with open(INPUT_FILE, "r") as src:
            with open(BACKUP_FILE, "w") as dst:
                dst.write(src.read())
        print(f"Created backup: {BACKUP_FILE}")

    with open(INPUT_FILE, "w") as f:
        json.dump({"themes": themes}, f, indent=2)


def load_checkpoint():
    """Load progress from checkpoint file."""
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, "r") as f:
            return json.load(f)
    return {"last_processed_index": -1, "total_processed": 0}


def save_checkpoint(last_index, total_processed):
    """Save progress to checkpoint file."""
    with open(CHECKPOINT_FILE, "w") as f:
        json.dump(
            {
                "last_processed_index": last_index,
                "total_processed": total_processed,
                "timestamp": datetime.now().isoformat(),
            },
            f,
            indent=2,
        )


def create_batch_prompt(themes_batch, start_index):
    """Create a prompt for the OpenAI API with a batch of themes."""
    prompt_parts = [
        "Generate creative, evocative names for the following color palettes.",
        "",
        "For each palette, create a name (2-4 words) that captures the mood, feeling, and visual essence of the colors.",
        "Consider the color names, hex values, and the overall harmony when naming.",
        "",
        "Examples of good names:",
        '- "Soft Sand Dunes" (for light, warm, earthy tones)',
        '- "Fiery Ocean Sunset" (for bold reds and deep blues)',
        '- "Warm Autumn Glow" (for oranges, reds, and warm browns)',
        '- "Berry Frost" (for cool purples and pinks)',
        '- "Golden Meadow" (for yellows and greens)',
        '- "Midnight Garden" (for deep blues and vibrant greens)',
        '- "Coral Reef Dreams" (for teals, corals, and ocean tones)',
        "",
        "Palettes to name:",
    ]

    for i, theme in enumerate(themes_batch):
        palette_num = start_index + i + 1
        prompt_parts.append(f"\nPalette {palette_num}:")
        for color in theme["colors"]:
            prompt_parts.append(f"- {color['name']} ({color['hex']})")

    prompt_parts.extend(
        [
            "",
            "Return ONLY a valid JSON object in this exact format:",
            "{",
            '  "names": [',
            '    {"index": 0, "name": "Name for first palette"},',
            '    {"index": 1, "name": "Name for second palette"},',
            "    ...",
            "  ]",
            "}",
            "",
            f"Important: Return exactly {len(themes_batch)} names, one for each palette.",
        ]
    )

    return "\n".join(prompt_parts)


def process_batch(client, themes_batch, batch_number, total_batches):
    """Process a batch of themes using OpenAI API."""
    start_index = batch_number * BATCH_SIZE
    prompt = create_batch_prompt(themes_batch, start_index)

    print(f"\nProcessing batch {batch_number + 1}/{total_batches} (themes {start_index + 1}-{start_index + len(themes_batch)})")

    for attempt in range(MAX_RETRIES):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a creative naming assistant specializing in color palettes. You generate evocative, memorable names that capture the essence of color combinations. Always return valid JSON.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=TEMPERATURE,
                max_tokens=MAX_TOKENS,
                response_format={"type": "json_object"},
            )

            content = response.choices[0].message.content
            result = json.loads(content)

            if "names" not in result:
                raise ValueError("Response missing 'names' key")

            names_data = result["names"]
            if len(names_data) != len(themes_batch):
                raise ValueError(f"Expected {len(themes_batch)} names, got {len(names_data)}")

            # Extract names in order
            names = []
            for item in names_data:
                if "name" not in item:
                    raise ValueError(f"Missing 'name' in response item: {item}")
                names.append(item["name"])

            print(f"  Generated names: {', '.join(names[:3])}{'...' if len(names) > 3 else ''}")
            return names

        except Exception as e:
            print(f"  Attempt {attempt + 1}/{MAX_RETRIES} failed: {e}")
            if attempt < MAX_RETRIES - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                print(f"  Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                print(f"  Failed to process batch after {MAX_RETRIES} attempts")
                # Return placeholder names for failed batch
                return [f"Theme {start_index + i + 1}" for i in range(len(themes_batch))]

    return [f"Theme {start_index + i + 1}" for i in range(len(themes_batch))]


def main():
    """Main function to process all themes."""
    print("=" * 60)
    print("Theme Naming Script for Swatchy")
    print("=" * 60)

    # Check for API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("\nError: OPENAI_API_KEY not found in environment variables.")
        print("Please set your OpenAI API key in the .env file:")
        print('  OPENAI_API_KEY="your-api-key-here"')
        return 1

    # Initialize OpenAI client
    client = OpenAI(api_key=api_key)

    # Load themes
    print(f"\nLoading themes from {INPUT_FILE}...")
    themes = load_themes()
    total_themes = len(themes)
    print(f"Loaded {total_themes} themes")

    # Load checkpoint
    checkpoint = load_checkpoint()
    start_batch = (checkpoint["last_processed_index"] + 1) // BATCH_SIZE
    processed_count = checkpoint["total_processed"]

    if start_batch > 0:
        print(f"\nResuming from checkpoint (batch {start_batch}, {processed_count} themes already processed)")

    # Calculate batches
    total_batches = (total_themes + BATCH_SIZE - 1) // BATCH_SIZE
    print(f"\nProcessing {total_batches} batches of ~{BATCH_SIZE} themes each")
    print(f"Estimated time: ~{total_batches * (DELAY_BETWEEN_BATCHES + 2)} seconds")
    print(f"Estimated cost: ~${total_batches * 0.01:.2f} (using {MODEL})")

    # Process batches
    try:
        for batch_num in range(start_batch, total_batches):
            start_idx = batch_num * BATCH_SIZE
            end_idx = min(start_idx + BATCH_SIZE, total_themes)
            batch_themes = themes[start_idx:end_idx]

            # Process this batch
            names = process_batch(client, batch_themes, batch_num, total_batches)

            # Assign names to themes
            for i, name in enumerate(names):
                theme_index = start_idx + i
                if theme_index < total_themes:
                    themes[theme_index]["theme_name"] = name

            # Update progress
            processed_count += len(batch_themes)
            save_checkpoint(end_idx - 1, processed_count)

            # Save progress to main file periodically
            if (batch_num + 1) % 10 == 0 or batch_num == total_batches - 1:
                print(f"  Saving progress... ({processed_count}/{total_themes} themes)")
                save_themes(themes)

            # Delay between batches
            if batch_num < total_batches - 1:
                time.sleep(DELAY_BETWEEN_BATCHES)

    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Saving progress...")
        save_themes(themes)
        save_checkpoint(start_idx, processed_count)
        print(f"Progress saved. Resume by running the script again.")
        return 0

    # Final save
    print("\n" + "=" * 60)
    print("Processing complete!")
    print(f"Total themes processed: {processed_count}")
    print(f"Total batches: {total_batches}")

    # Save final results
    save_themes(themes)
    print(f"Results saved to {INPUT_FILE}")

    # Clean up checkpoint
    if os.path.exists(CHECKPOINT_FILE):
        os.remove(CHECKPOINT_FILE)
        print(f"Removed checkpoint file: {CHECKPOINT_FILE}")

    # Show sample names
    print("\nSample generated names:")
    for i in range(min(5, len(themes))):
        theme = themes[i]
        colors_str = ", ".join([c["name"] for c in theme["colors"]])
        print(f"  - '{theme.get('theme_name', 'N/A')}' ({colors_str})")

    return 0


if __name__ == "__main__":
    exit(main())

#!/usr/bin/env python3
"""
Migrate themes from local JSON file to Vercel KV.
Usage: 
  python migrate_themes.py           # Interactive mode
  python migrate_themes.py --merge   # Auto-merge themes
  python migrate_themes.py --replace # Replace KV with file themes
"""
import json
import os
import sys
import uuid
from storage import get_storage_instance, FileStorage, KVStorage

def migrate_themes(mode='interactive'):
    """Migrate themes from file to KV storage."""
    # Load themes from file
    file_storage = FileStorage()
    file_themes = file_storage.get_all_themes()
    
    if not file_themes:
        print("No themes found in generated_themes.json")
        return
    
    print(f"Found {len(file_themes)} themes in generated_themes.json")
    
    # Get KV storage
    storage = get_storage_instance()
    
    if isinstance(storage, FileStorage):
        print("\nWarning: KV credentials not found. Using file storage.")
        print("Add KV_URL or KV_REST_API_URL to your .env file to use KV storage.")
        return
    
    # Check existing themes in KV
    kv_themes = storage.get_all_themes()
    print(f"Found {len(kv_themes)} themes already in KV")
    
    if kv_themes and mode == 'interactive':
        print("\nKV already has themes. Do you want to:")
        print("1. Merge (add file themes to existing KV themes)")
        print("2. Replace (overwrite KV with file themes)")
        print("3. Cancel")
        response = input("Choice (1/2/3): ").strip()
        
        if response == '3':
            print("Cancelled.")
            return
        elif response == '2':
            mode = 'replace'
        else:
            mode = 'merge'
    
    # Ensure all themes have IDs
    for theme in file_themes:
        if 'id' not in theme:
            theme['id'] = str(uuid.uuid4())
    
    if mode == 'replace':
        # Replace - save all file themes
        print(f"\nReplacing KV with {len(file_themes)} themes from file...")
        success = storage._make_request('set', 'themes:data', {'themes': file_themes})
        if success is not None:
            print(f"✓ Success! KV now has {len(file_themes)} themes")
        else:
            print("✗ Failed to save themes to KV")
        return
    
    # Merge mode - combine and save once
    print(f"\nMerging themes...")
    
    # Create a dict to deduplicate by ID
    theme_map = {}
    
    # Add KV themes first (they stay if duplicate)
    for theme in kv_themes:
        theme_id = theme.get('id')
        if theme_id:
            theme_map[theme_id] = theme
    
    # Add file themes (will overwrite if same ID, but we want newer data from file usually)
    imported_count = 0
    skipped_count = 0
    
    for theme in file_themes:
        theme_id = theme.get('id')
        
        # Check for duplicates by content if no ID match
        is_duplicate = False
        if theme_id in theme_map:
            is_duplicate = True
        else:
            # Check by name + seed_color
            for existing in theme_map.values():
                if (existing.get('theme_name') == theme.get('theme_name') and 
                    existing.get('seed_color') == theme.get('seed_color')):
                    is_duplicate = True
                    break
        
        if is_duplicate:
            skipped_count += 1
        else:
            theme_map[theme_id] = theme
            imported_count += 1
    
    # Convert back to list (maintain order - KV themes first, then new file themes)
    merged_themes = list(theme_map.values())
    
    print(f"Saving {len(merged_themes)} total themes to KV...")
    success = storage._make_request('set', 'themes:data', {'themes': merged_themes})
    
    if success is not None:
        print(f"\n{'='*50}")
        print(f"Migration complete!")
        print(f"  From file: {len(file_themes)}")
        print(f"  From KV: {len(kv_themes)}")
        print(f"  New imported: {imported_count}")
        print(f"  Skipped duplicates: {skipped_count}")
        print(f"  Total in KV now: {len(merged_themes)}")
    else:
        print("\n✗ Failed to save themes to KV")

if __name__ == '__main__':
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Parse arguments
    mode = 'interactive'
    if '--merge' in sys.argv:
        mode = 'merge'
    elif '--replace' in sys.argv:
        mode = 'replace'
    
    migrate_themes(mode)

"""
Storage abstraction for themes.
Uses Vercel KV when credentials are available, falls back to local JSON file.
"""
import os
import json
from typing import List, Dict, Any, Optional

# Try to import Vercel KV, but don't fail if not available
try:
    from vercel_kv import KV
    KV_AVAILABLE = True
except ImportError:
    KV_AVAILABLE = False

# Check if we're running on Vercel (production)
IS_VERCEL = os.environ.get('VERCEL') == '1' or os.environ.get('VERCEL_ENV') is not None


def has_kv_credentials() -> bool:
    """Check if Vercel KV credentials are available in environment."""
    return bool(
        os.environ.get('KV_URL') or 
        os.environ.get('KV_REST_API_URL')
    )

# KV key prefixes
THEME_PREFIX = "theme:"
THEMES_LIST_KEY = "themes:list"
THEMES_DATA_KEY = "themes:data"

class ThemeStorage:
    """Abstract base class for theme storage."""
    
    def get_all_themes(self) -> List[Dict[str, Any]]:
        raise NotImplementedError
    
    def save_theme(self, theme: Dict[str, Any]) -> bool:
        raise NotImplementedError
    
    def delete_theme(self, theme_id: str) -> bool:
        raise NotImplementedError


class FileStorage(ThemeStorage):
    """Local file storage for development."""
    
    def __init__(self, filepath: str = None):
        if filepath is None:
            filepath = os.path.join(os.path.dirname(__file__), 'generated_themes.json')
        self.filepath = filepath
    
    def get_all_themes(self) -> List[Dict[str, Any]]:
        try:
            with open(self.filepath, 'r') as f:
                data = json.load(f)
                return data.get('themes', [])
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def save_theme(self, theme: Dict[str, Any]) -> bool:
        try:
            # Read existing themes
            data = {'themes': []}
            if os.path.exists(self.filepath):
                with open(self.filepath, 'r') as f:
                    data = json.load(f)
            
            if 'themes' not in data:
                data['themes'] = []
            
            # Add new theme to beginning
            data['themes'].insert(0, theme)
            
            # Write back
            with open(self.filepath, 'w') as f:
                json.dump(data, f, indent=2)
            
            return True
        except Exception:
            return False
    
    def delete_theme(self, theme_id: str) -> bool:
        try:
            with open(self.filepath, 'r') as f:
                data = json.load(f)
            
            if 'themes' not in data:
                return False
            
            # Filter out the theme to delete
            original_count = len(data['themes'])
            data['themes'] = [t for t in data['themes'] if t.get('id') != theme_id]
            
            if len(data['themes']) == original_count:
                return False  # Theme not found
            
            with open(self.filepath, 'w') as f:
                json.dump(data, f, indent=2)
            
            return True
        except Exception:
            return False


class KVStorage(ThemeStorage):
    """Vercel KV storage for production."""
    
    def __init__(self):
        if not KV_AVAILABLE:
            raise RuntimeError("Vercel KV SDK not available")
        self.kv = KV()
    
    def get_all_themes(self) -> List[Dict[str, Any]]:
        try:
            # Get the stored themes data
            data = self.kv.get(THEMES_DATA_KEY)
            if data:
                if isinstance(data, str):
                    data = json.loads(data)
                return data.get('themes', [])
            return []
        except Exception as e:
            print(f"Error reading from KV: {e}")
            return []
    
    def save_theme(self, theme: Dict[str, Any]) -> bool:
        try:
            # Get existing themes
            themes = self.get_all_themes()
            
            # Add new theme to beginning
            themes.insert(0, theme)
            
            # Store back to KV
            self.kv.set(THEMES_DATA_KEY, json.dumps({'themes': themes}))
            
            return True
        except Exception as e:
            print(f"Error saving to KV: {e}")
            return False
    
    def delete_theme(self, theme_id: str) -> bool:
        try:
            themes = self.get_all_themes()
            original_count = len(themes)
            themes = [t for t in themes if t.get('id') != theme_id]
            
            if len(themes) == original_count:
                return False
            
            self.kv.set(THEMES_DATA_KEY, json.dumps({'themes': themes}))
            return True
        except Exception as e:
            print(f"Error deleting from KV: {e}")
            return False


def get_storage() -> ThemeStorage:
    """Factory function to get the appropriate storage backend.
    
    Uses KV if credentials are available (for local dev debugging or production).
    Falls back to file storage otherwise.
    """
    # Use KV if credentials are available and KV is installed
    if KV_AVAILABLE and has_kv_credentials():
        try:
            print("Using Vercel KV storage")
            return KVStorage()
        except Exception as e:
            print(f"Failed to initialize KV storage: {e}, falling back to file storage")
            return FileStorage()
    
    # Default to file storage
    print("Using file storage")
    return FileStorage()


# Singleton instance
_storage_instance: Optional[ThemeStorage] = None

def get_storage_instance() -> ThemeStorage:
    """Get the singleton storage instance."""
    global _storage_instance
    if _storage_instance is None:
        _storage_instance = get_storage()
    return _storage_instance

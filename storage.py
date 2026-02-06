"""
Storage abstraction for themes.
Uses Vercel KV when credentials are available, falls back to local JSON file.
"""
import os
import json
import base64
from typing import List, Dict, Any, Optional

# Try to import requests for KV API calls
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


def has_kv_credentials() -> bool:
    """Check if Vercel KV credentials are available in environment."""
    return bool(
        os.environ.get('KV_URL') or 
        os.environ.get('KV_REST_API_URL')
    )


def get_kv_config() -> Optional[Dict[str, str]]:
    """Get KV configuration from environment variables."""
    # First try KV_URL (redis:// format)
    kv_url = os.environ.get('KV_URL')
    if kv_url:
        # Parse redis://username:password@host:port format
        # or redis://default:token@host:port
        try:
            # Remove redis:// prefix
            rest = kv_url.replace('redis://', '')
            # Split auth and host
            if '@' in rest:
                auth, host_port = rest.split('@')
                token = auth.split(':')[-1]  # Get password/token part
                return {
                    'token': token,
                    'url': f"https://{host_port}"
                }
        except Exception:
            pass
    
    # Fall back to REST API env vars
    rest_url = os.environ.get('KV_REST_API_URL')
    rest_token = os.environ.get('KV_REST_API_TOKEN')
    
    if rest_url and rest_token:
        return {
            'token': rest_token,
            'url': rest_url
        }
    
    return None


# KV key for storing all themes
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
    """Vercel KV storage using REST API directly."""
    
    def __init__(self):
        if not REQUESTS_AVAILABLE:
            raise RuntimeError("requests library not available")
        
        config = get_kv_config()
        if not config:
            raise RuntimeError("KV credentials not available")
        
        self.token = config['token']
        self.base_url = config['url'].rstrip('/')
    
    def _make_request(self, command: str, key: str, value: Any = None) -> Any:
        """Make a request to Vercel KV REST API."""
        url = f"{self.base_url}/{command}/{key}"
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
        
        try:
            if command in ['set', 'hset']:
                response = requests.post(url, headers=headers, json=value, timeout=10)
            else:  # get, hget, etc.
                response = requests.get(url, headers=headers, timeout=10)
            
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"KV API error ({command} {key}): {e}")
            return None
    
    def get_all_themes(self) -> List[Dict[str, Any]]:
        try:
            # Get the stored themes data
            result = self._make_request('get', THEMES_DATA_KEY)
            
            if result is None:
                return []
            
            # Handle different response formats
            if isinstance(result, dict):
                if 'result' in result:
                    data = result['result']
                else:
                    data = result
            else:
                data = result
            
            if isinstance(data, str):
                data = json.loads(data)
            
            if isinstance(data, dict):
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
            result = self._make_request('set', THEMES_DATA_KEY, {'themes': themes})
            
            return result is not None
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
            
            result = self._make_request('set', THEMES_DATA_KEY, {'themes': themes})
            return result is not None
        except Exception as e:
            print(f"Error deleting from KV: {e}")
            return False


def get_storage() -> ThemeStorage:
    """Factory function to get the appropriate storage backend.
    
    Uses KV if credentials are available (for local dev debugging or production).
    Falls back to file storage otherwise.
    """
    # Use KV if credentials and requests are available
    if has_kv_credentials() and REQUESTS_AVAILABLE:
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

"""Service for fetching and caching keywords from Scryfall."""
import json
import requests
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple

class ScryfallKeywords:
    """Handles fetching and caching of Scryfall keyword catalogs."""
    
    BASE_URL = "https://api.scryfall.com/catalog"
    CACHE_DIR = Path("data/cache")
    CACHE_DURATION = timedelta(days=7)
    
    def __init__(self):
        self.CACHE_DIR.mkdir(parents=True, exist_ok=True)
        self._abilities = []
        self._actions = []
        
    def get_all_keywords(self) -> Tuple[List[str], List[str]]:
        """
        Get all keyword abilities and actions.
        Returns tuple of (abilities, actions).
        """
        if not self._abilities:
            self._abilities = self._get_catalog("keyword-abilities")
            
        if not self._actions:
            self._actions = self._get_catalog("keyword-actions")
            
        return self._abilities, self._actions
    
    def get_abilities(self) -> List[str]:
        """Get list of keyword abilities (Flying, Trample, etc)."""
        if not self._abilities:
            self._abilities = self._get_catalog("keyword-abilities")
        return self._abilities
        
    def get_actions(self) -> List[str]:
        """Get list of keyword actions (Scry, Mill, etc)."""
        if not self._actions:
            self._actions = self._get_catalog("keyword-actions")
        return self._actions
        
    def _get_catalog(self, catalog_name: str) -> List[str]:
        """Fetch catalog from cache or API."""
        cache_path = self.CACHE_DIR / f"{catalog_name}.json"
        
        # Check cache
        if cache_path.exists():
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    
                timestamp = datetime.fromisoformat(data["timestamp"])
                if datetime.now() - timestamp < self.CACHE_DURATION:
                    return data["keywords"]
            except Exception as e:
                print(f"Error reading cache for {catalog_name}: {e}")
        
        # Fetch from API
        return self._fetch_and_cache_catalog(catalog_name, cache_path)
        
    def _fetch_and_cache_catalog(self, catalog_name: str, cache_path: Path) -> List[str]:
        """Fetch from Scryfall API and save to cache."""
        try:
            url = f"{self.BASE_URL}/{catalog_name}"
            response = requests.get(url)
            response.raise_for_status()
            
            data = response.json()
            keywords = data.get("data", [])
            
            # Save to cache
            cache_data = {
                "timestamp": datetime.now().isoformat(),
                "keywords": keywords,
                "total": data.get("total_values", 0)
            }
            
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, indent=2)
                
            return keywords
            
        except Exception as e:
            print(f"Error fetching {catalog_name}: {e}")
            # Return empty list on error to allow offline functionality if desired
            return []

    def get_keyword_type(self, keyword: str) -> str:
        """Determine if a keyword is an ability or action."""
        abilities, actions = self.get_all_keywords()
        
        # Normalize for comparison
        k_lower = keyword.lower()
        
        if any(k.lower() == k_lower for k in abilities):
            return "ability"
        if any(k.lower() == k_lower for k in actions):
            return "action"
            
        return "unknown"

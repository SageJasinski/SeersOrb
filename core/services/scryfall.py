"""Scryfall API client for card data."""
import time
import json
from pathlib import Path
from typing import List, Optional, Dict
from datetime import datetime, timedelta

try:
    import scrython
    HAS_SCRYTHON = True
except ImportError:
    HAS_SCRYTHON = False

import requests

from core.models.card import Card


class ScryfallClient:
    """Client for interacting with the Scryfall API."""
    
    API_BASE = "https://api.scryfall.com"
    RATE_LIMIT_MS = 100
    
    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = cache_dir or Path("data/cache/cards")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._last_request_time = 0
        
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "SeersOrb/0.1.0",
            "Accept": "application/json"
        })
    
    def _rate_limit(self):
        """Enforce rate limiting between requests."""
        elapsed = (time.time() * 1000) - self._last_request_time
        if elapsed < self.RATE_LIMIT_MS:
            time.sleep((self.RATE_LIMIT_MS - elapsed) / 1000)
        self._last_request_time = time.time() * 1000
    
    def _get_cache_path(self, card_id: str) -> Path:
        """Get cache file path for a card."""
        return self.cache_dir / f"{card_id}.json"
    
    def _is_cache_valid(self, cache_path: Path, ttl_hours: int = 24) -> bool:
        """Check if cache file is still valid."""
        if not cache_path.exists():
            return False
        
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        return datetime.now() - mtime < timedelta(hours=ttl_hours)
    
    def _load_from_cache(self, card_id: str) -> Optional[dict]:
        """Load card data from cache."""
        cache_path = self._get_cache_path(card_id)
        if self._is_cache_valid(cache_path):
            with open(cache_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return None
    
    def _save_to_cache(self, card_id: str, data: dict):
        """Save card data to cache."""
        cache_path = self._get_cache_path(card_id)
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    
    # =========================================================================
    # Card search methods
    # =========================================================================
    
    def search_cards(self, query: str, limit: int = 20) -> List[dict]:
        """
        Search for cards using Scryfall's search syntax.
        
        Args:
            query: Search query (supports Scryfall syntax)
            limit: Maximum number of results
            
        Returns:
            List of card dictionaries
        """
        if HAS_SCRYTHON:
            return self._search_with_scrython(query, limit)
        return self._search_with_requests(query, limit)
    
    def _search_with_scrython(self, query: str, limit: int) -> List[dict]:
        """Search using scrython library."""
        try:
            search = scrython.cards.Search(q=query)
            
            # Give scrython time to complete the async request
            time.sleep(0.15)
            
            # Handle both scrython API versions (data as property or method)
            if callable(getattr(search, 'data', None)):
                data = search.data()
            else:
                data = search.data
            
            # Ensure we have a valid list
            if not data or not isinstance(data, list):
                return self._search_with_requests(query, limit)
            
            cards = []
            for i, card_data in enumerate(data):
                if i >= limit:
                    break
                card = Card.from_scryfall(card_data)
                cards.append(card.to_dict())
                
                # Cache the card
                self._save_to_cache(card.id, card_data)
            
            return cards
        except Exception as e:
            print(f"Scrython search error: {e}")
            # Fall back to requests
            return self._search_with_requests(query, limit)
    
    def _search_with_requests(self, query: str, limit: int) -> List[dict]:
        """Search using requests library."""
        self._rate_limit()
        
        try:
            response = self.session.get(
                f"{self.API_BASE}/cards/search",
                params={"q": query}
            )
            
            if response.status_code == 404:
                return []
            
            response.raise_for_status()
            data = response.json()
            
            cards = []
            for card_data in data.get("data", [])[:limit]:
                card = Card.from_scryfall(card_data)
                cards.append(card.to_dict())
                self._save_to_cache(card.id, card_data)
            
            return cards
        except Exception as e:
            print(f"Search error: {e}")
            return []
    
    def autocomplete(self, partial: str) -> List[str]:
        """
        Get card name autocomplete suggestions.
        
        Args:
            partial: Partial card name
            
        Returns:
            List of card name suggestions
        """
        if len(partial) < 2:
            return []
        
        self._rate_limit()
        
        try:
            response = self.session.get(
                f"{self.API_BASE}/cards/autocomplete",
                params={"q": partial}
            )
            response.raise_for_status()
            return response.json().get("data", [])
        except Exception as e:
            print(f"Autocomplete error: {e}")
            return []
    
    def get_card_by_name(self, name: str, exact: bool = False) -> Optional[Card]:
        """
        Get a card by its name.
        
        Args:
            name: Card name
            exact: If True, require exact match
            
        Returns:
            Card object or None
        """
        self._rate_limit()
        
        try:
            param = "exact" if exact else "fuzzy"
            response = self.session.get(
                f"{self.API_BASE}/cards/named",
                params={param: name}
            )
            
            if response.status_code == 404:
                return None
            
            response.raise_for_status()
            data = response.json()
            
            card = Card.from_scryfall(data)
            self._save_to_cache(card.id, data)
            
            return card
        except Exception as e:
            print(f"Get card by name error: {e}")
            return None
    
    def get_card_by_id(self, card_id: str) -> Optional[Card]:
        """
        Get a card by its Scryfall ID.
        
        Args:
            card_id: Scryfall card ID
            
        Returns:
            Card object or None
        """
        # Try cache first
        cached = self._load_from_cache(card_id)
        if cached:
            return Card.from_scryfall(cached)
        
        self._rate_limit()
        
        try:
            response = self.session.get(f"{self.API_BASE}/cards/{card_id}")
            
            if response.status_code == 404:
                return None
            
            response.raise_for_status()
            data = response.json()
            
            card = Card.from_scryfall(data)
            self._save_to_cache(card_id, data)
            
            return card
        except Exception as e:
            print(f"Get card by ID error: {e}")
            return None
    
    def get_collection(self, identifiers: List[Dict]) -> List[Card]:
        """
        Get multiple cards at once.
        
        Args:
            identifiers: List of card identifiers, each is a dict like:
                         {"id": "..."} or {"name": "..."} or {"set": "...", "collector_number": "..."}
        
        Returns:
            List of Card objects
        """
        if not identifiers:
            return []
        
        self._rate_limit()
        
        try:
            response = self.session.post(
                f"{self.API_BASE}/cards/collection",
                json={"identifiers": identifiers}
            )
            response.raise_for_status()
            data = response.json()
            
            cards = []
            for card_data in data.get("data", []):
                card = Card.from_scryfall(card_data)
                cards.append(card)
                self._save_to_cache(card.id, card_data)
            
            return cards
        except Exception as e:
            print(f"Get collection error: {e}")
            return []
    
    def get_random_card(self) -> Optional[Card]:
        """Get a random card."""
        self._rate_limit()
        
        try:
            response = self.session.get(f"{self.API_BASE}/cards/random")
            response.raise_for_status()
            data = response.json()
            
            return Card.from_scryfall(data)
        except Exception as e:
            print(f"Get random card error: {e}")
            return None

"""Deck storage service - JSON file based."""
import json
from pathlib import Path
from typing import List, Optional, Dict
from datetime import datetime

from core.models.deck import Deck


class DeckStorage:
    """Handles deck persistence using JSON files."""
    
    def __init__(self, storage_dir: Optional[Path] = None):
        self.storage_dir = storage_dir or Path("data/decks")
        self.storage_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_deck_path(self, deck_id: str) -> Path:
        """Get the file path for a deck."""
        return self.storage_dir / f"{deck_id}.json"
    
    def save_deck(self, deck: Deck, deck_id: Optional[str] = None) -> str:
        """
        Save a deck to storage.
        
        Args:
            deck: The deck to save
            deck_id: Optional ID to use (uses deck.id if not provided)
            
        Returns:
            The deck ID
        """
        if deck_id:
            deck.id = deck_id
        
        deck.updated_at = datetime.now().isoformat()
        
        deck_path = self._get_deck_path(deck.id)
        with open(deck_path, "w", encoding="utf-8") as f:
            json.dump(deck.to_dict(), f, indent=2)
        
        return deck.id
    
    def load_deck(self, deck_id: str) -> Optional[Deck]:
        """
        Load a deck from storage.
        
        Args:
            deck_id: The deck ID to load
            
        Returns:
            The Deck or None if not found
        """
        deck_path = self._get_deck_path(deck_id)
        
        if not deck_path.exists():
            return None
        
        try:
            with open(deck_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return Deck.from_dict(data)
        except Exception as e:
            print(f"Error loading deck {deck_id}: {e}")
            return None
    
    def delete_deck(self, deck_id: str) -> bool:
        """
        Delete a deck from storage.
        
        Args:
            deck_id: The deck ID to delete
            
        Returns:
            True if deleted, False if not found
        """
        deck_path = self._get_deck_path(deck_id)
        
        if not deck_path.exists():
            return False
        
        deck_path.unlink()
        return True
    
    def list_decks(self) -> List[Dict]:
        """
        List all saved decks with basic info.
        
        Returns:
            List of deck summaries (id, name, format, card count, updated_at)
        """
        decks = []
        
        for deck_file in self.storage_dir.glob("*.json"):
            try:
                with open(deck_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                decks.append({
                    "id": data.get("id", deck_file.stem),
                    "name": data.get("name", "Untitled"),
                    "format": data.get("format", "unknown"),
                    "card_count": data.get("stats", {}).get("total_cards", 0),
                    "updated_at": data.get("updated_at", ""),
                    "commander": data.get("commander")
                })
            except Exception as e:
                print(f"Error reading deck {deck_file}: {e}")
        
        # Sort by most recently updated
        decks.sort(key=lambda d: d.get("updated_at", ""), reverse=True)
        
        return decks
    
    def deck_exists(self, deck_id: str) -> bool:
        """Check if a deck exists."""
        return self._get_deck_path(deck_id).exists()
    
    def import_from_text(self, text: str, name: str = "Imported Deck") -> Deck:
        """
        Import a deck from text format.
        
        Supports formats like:
            1 Sol Ring
            4 Lightning Bolt
            // Comment lines are ignored
        
        Args:
            text: Deck text content
            name: Name for the imported deck
            
        Returns:
            A new Deck object (cards need to be fetched separately)
        """
        from core.services.scryfall import ScryfallClient
        
        deck = Deck(name=name)
        client = ScryfallClient()
        
        for line in text.strip().split("\n"):
            line = line.strip()
            
            # Skip empty lines and comments
            if not line or line.startswith("//"):
                continue
            
            # Parse quantity and name
            parts = line.split(" ", 1)
            if len(parts) < 2:
                continue
            
            try:
                quantity = int(parts[0].replace("x", ""))
                card_name = parts[1].strip()
            except ValueError:
                # No quantity, assume 1
                quantity = 1
                card_name = line
            
            # Fetch card from Scryfall
            card = client.get_card_by_name(card_name)
            if card:
                deck.add_card(card, quantity)
        
        return deck
    
    def export_to_text(self, deck_id: str) -> Optional[str]:
        """
        Export a deck to text format.
        
        Args:
            deck_id: The deck to export
            
        Returns:
            Text representation or None if deck not found
        """
        deck = self.load_deck(deck_id)
        if not deck:
            return None
        
        return deck.to_text()

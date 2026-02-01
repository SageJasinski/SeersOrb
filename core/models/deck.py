"""Deck data model."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime
import uuid

from core.models.card import Card


@dataclass
class DeckEntry:
    """A card entry in a deck with quantity."""
    card: Card
    quantity: int = 1
    category: str = ""  # User-defined category (e.g., "Ramp", "Draw")
    
    def to_dict(self) -> dict:
        return {
            "card": self.card.to_dict(),
            "quantity": self.quantity,
            "category": self.category
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "DeckEntry":
        return cls(
            card=Card.from_dict(data["card"]),
            quantity=data.get("quantity", 1),
            category=data.get("category", "")
        )


@dataclass
class Deck:
    """Represents an MTG deck."""
    
    # Metadata
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "Untitled Deck"
    format: str = "commander"  # commander, standard, modern, legacy, etc.
    description: str = ""
    
    # Commander (for Commander format)
    commander: Optional[str] = None  # Card ID
    partner: Optional[str] = None  # Second commander card ID
    
    # Cards - stored as {card_id: DeckEntry}
    cards: Dict[str, DeckEntry] = field(default_factory=dict)
    
    # Sideboard
    sideboard: Dict[str, DeckEntry] = field(default_factory=dict)
    
    # Timestamps
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    # =========================================================================
    # Card management
    # =========================================================================
    
    def add_card(self, card: Card, quantity: int = 1, category: str = "") -> None:
        """Add a card to the deck."""
        if card.id in self.cards:
            self.cards[card.id].quantity += quantity
        else:
            self.cards[card.id] = DeckEntry(card=card, quantity=quantity, category=category)
        self.updated_at = datetime.now().isoformat()
    
    def remove_card(self, card_id: str, quantity: int = 1) -> bool:
        """Remove a card from the deck. Returns True if successful."""
        if card_id not in self.cards:
            return False
        
        self.cards[card_id].quantity -= quantity
        if self.cards[card_id].quantity <= 0:
            del self.cards[card_id]
        
        self.updated_at = datetime.now().isoformat()
        return True
    
    def set_card_quantity(self, card_id: str, quantity: int) -> bool:
        """Set the quantity of a card."""
        if card_id not in self.cards:
            return False
        
        if quantity <= 0:
            del self.cards[card_id]
        else:
            self.cards[card_id].quantity = quantity
        
        self.updated_at = datetime.now().isoformat()
        return True
    
    def set_card_category(self, card_id: str, category: str) -> bool:
        """Set the category of a card."""
        if card_id not in self.cards:
            return False
        self.cards[card_id].category = category
        self.updated_at = datetime.now().isoformat()
        return True
    
    def get_card(self, card_id: str) -> Optional[DeckEntry]:
        """Get a card entry by ID."""
        return self.cards.get(card_id)
    
    # =========================================================================
    # Deck statistics
    # =========================================================================
    
    def total_cards(self) -> int:
        """Get total number of cards in the deck."""
        return sum(entry.quantity for entry in self.cards.values())
    
    def unique_cards(self) -> int:
        """Get number of unique cards."""
        return len(self.cards)
    
    def get_cards_list(self) -> List[Card]:
        """Get flat list of all cards (respecting quantities)."""
        cards = []
        for entry in self.cards.values():
            for _ in range(entry.quantity):
                cards.append(entry.card)
        return cards
    
    def get_unique_cards(self) -> List[Card]:
        """Get list of unique cards (one per card regardless of quantity)."""
        return [entry.card for entry in self.cards.values()]
    
    def get_cards_by_type(self, card_type: str) -> List[DeckEntry]:
        """Get all card entries of a specific type."""
        return [
            entry for entry in self.cards.values()
            if card_type in entry.card.type_line
        ]
    
    def get_cards_by_category(self, category: str) -> List[DeckEntry]:
        """Get all card entries in a specific category."""
        return [
            entry for entry in self.cards.values()
            if entry.category.lower() == category.lower()
        ]
    
    def get_categories(self) -> List[str]:
        """Get list of all categories used in the deck."""
        categories = set()
        for entry in self.cards.values():
            if entry.category:
                categories.add(entry.category)
        return sorted(categories)
    
    def mana_curve(self) -> Dict[int, int]:
        """Get mana curve as {cmc: count}."""
        curve = {}
        for entry in self.cards.values():
            if entry.card.is_land():
                continue
            cmc = int(entry.card.cmc)
            curve[cmc] = curve.get(cmc, 0) + entry.quantity
        return dict(sorted(curve.items()))
    
    def color_distribution(self) -> Dict[str, int]:
        """Get color distribution of cards."""
        colors = {"W": 0, "U": 0, "B": 0, "R": 0, "G": 0, "C": 0}
        
        for entry in self.cards.values():
            if not entry.card.colors:
                colors["C"] += entry.quantity
            else:
                for color in entry.card.colors:
                    if color in colors:
                        colors[color] += entry.quantity
        
        return colors
    
    def type_distribution(self) -> Dict[str, int]:
        """Get card type distribution."""
        types = {}
        for entry in self.cards.values():
            for card_type in entry.card.get_card_types():
                types[card_type] = types.get(card_type, 0) + entry.quantity
        return types
    
    def land_count(self) -> int:
        """Get total land count."""
        return sum(
            entry.quantity for entry in self.cards.values()
            if entry.card.is_land()
        )
    
    def average_cmc(self) -> float:
        """Calculate average CMC (excluding lands)."""
        total_cmc = 0
        total_cards = 0
        
        for entry in self.cards.values():
            if not entry.card.is_land():
                total_cmc += entry.card.cmc * entry.quantity
                total_cards += entry.quantity
        
        return total_cmc / total_cards if total_cards > 0 else 0.0
    
    # =========================================================================
    # Serialization
    # =========================================================================
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "format": self.format,
            "description": self.description,
            "commander": self.commander,
            "partner": self.partner,
            "cards": {card_id: entry.to_dict() for card_id, entry in self.cards.items()},
            "sideboard": {card_id: entry.to_dict() for card_id, entry in self.sideboard.items()},
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "stats": {
                "total_cards": self.total_cards(),
                "unique_cards": self.unique_cards(),
                "land_count": self.land_count(),
                "average_cmc": round(self.average_cmc(), 2),
                "mana_curve": self.mana_curve(),
                "color_distribution": self.color_distribution(),
                "type_distribution": self.type_distribution()
            }
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Deck":
        """Create a Deck from a dictionary."""
        deck = cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", "Untitled Deck"),
            format=data.get("format", "commander"),
            description=data.get("description", ""),
            commander=data.get("commander"),
            partner=data.get("partner"),
            created_at=data.get("created_at", datetime.now().isoformat()),
            updated_at=data.get("updated_at", datetime.now().isoformat())
        )
        
        # Load cards
        if "cards" in data:
            for card_id, entry_data in data["cards"].items():
                deck.cards[card_id] = DeckEntry.from_dict(entry_data)
        
        # Load sideboard
        if "sideboard" in data:
            for card_id, entry_data in data["sideboard"].items():
                deck.sideboard[card_id] = DeckEntry.from_dict(entry_data)
        
        return deck
    
    def to_text(self) -> str:
        """Export deck as text format (for import into other tools)."""
        lines = [f"// {self.name}", f"// Format: {self.format}", ""]
        
        if self.commander:
            commander_entry = self.cards.get(self.commander)
            if commander_entry:
                lines.append(f"// Commander: {commander_entry.card.name}")
                lines.append("")
        
        # Group by category or type
        categories = self.get_categories()
        
        if categories:
            for category in categories:
                entries = self.get_cards_by_category(category)
                if entries:
                    lines.append(f"// {category}")
                    for entry in entries:
                        lines.append(f"{entry.quantity} {entry.card.name}")
                    lines.append("")
        else:
            # Group by type
            for card_type in ["Creature", "Instant", "Sorcery", "Artifact", 
                              "Enchantment", "Planeswalker", "Land"]:
                entries = self.get_cards_by_type(card_type)
                if entries:
                    lines.append(f"// {card_type}s")
                    for entry in entries:
                        lines.append(f"{entry.quantity} {entry.card.name}")
                    lines.append("")
        
        return "\n".join(lines)

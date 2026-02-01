"""Card data model."""
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set
import re


@dataclass
class Card:
    """Represents a Magic: The Gathering card."""
    
    # Core identifiers
    id: str
    name: str
    
    # Mana
    mana_cost: str = ""
    cmc: float = 0.0
    colors: List[str] = field(default_factory=list)
    color_identity: List[str] = field(default_factory=list)
    
    # Type information
    type_line: str = ""
    
    # Rules text
    oracle_text: str = ""
    keywords: List[str] = field(default_factory=list)
    
    # Creature stats
    power: Optional[str] = None
    toughness: Optional[str] = None
    
    # Images
    image_uri: str = ""
    art_crop_uri: str = ""
    
    # Legalities
    legalities: Dict[str, str] = field(default_factory=dict)
    
    # Prices
    prices: Dict[str, Optional[str]] = field(default_factory=dict)
    
    # Set info
    set_code: str = ""
    set_name: str = ""
    rarity: str = ""
    
    @classmethod
    def from_scryfall(cls, data: dict) -> "Card":
        """Create a Card from Scryfall API response."""
        # Handle double-faced cards
        image_uri = ""
        art_crop_uri = ""
        
        if "image_uris" in data:
            image_uri = data["image_uris"].get("normal", "")
            art_crop_uri = data["image_uris"].get("art_crop", "")
        elif "card_faces" in data and len(data["card_faces"]) > 0:
            face = data["card_faces"][0]
            if "image_uris" in face:
                image_uri = face["image_uris"].get("normal", "")
                art_crop_uri = face["image_uris"].get("art_crop", "")
        
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            mana_cost=data.get("mana_cost", ""),
            cmc=data.get("cmc", 0.0),
            colors=data.get("colors", []),
            color_identity=data.get("color_identity", []),
            type_line=data.get("type_line", ""),
            oracle_text=data.get("oracle_text", ""),
            keywords=data.get("keywords", []),
            power=data.get("power"),
            toughness=data.get("toughness"),
            image_uri=image_uri,
            art_crop_uri=art_crop_uri,
            legalities=data.get("legalities", {}),
            prices=data.get("prices", {}),
            set_code=data.get("set", ""),
            set_name=data.get("set_name", ""),
            rarity=data.get("rarity", "")
        )
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "mana_cost": self.mana_cost,
            "cmc": self.cmc,
            "colors": self.colors,
            "color_identity": self.color_identity,
            "type_line": self.type_line,
            "oracle_text": self.oracle_text,
            "keywords": self.keywords,
            "power": self.power,
            "toughness": self.toughness,
            "image_uri": self.image_uri,
            "art_crop_uri": self.art_crop_uri,
            "legalities": self.legalities,
            "prices": self.prices,
            "set_code": self.set_code,
            "set_name": self.set_name,
            "rarity": self.rarity
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Card":
        """Create a Card from a dictionary."""
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            mana_cost=data.get("mana_cost", ""),
            cmc=data.get("cmc", 0.0),
            colors=data.get("colors", []),
            color_identity=data.get("color_identity", []),
            type_line=data.get("type_line", ""),
            oracle_text=data.get("oracle_text", ""),
            keywords=data.get("keywords", []),
            power=data.get("power"),
            toughness=data.get("toughness"),
            image_uri=data.get("image_uri", ""),
            art_crop_uri=data.get("art_crop_uri", ""),
            legalities=data.get("legalities", {}),
            prices=data.get("prices", {}),
            set_code=data.get("set_code", ""),
            set_name=data.get("set_name", ""),
            rarity=data.get("rarity", "")
        )
    
    # =========================================================================
    # Type checking helpers
    # =========================================================================
    
    def is_creature(self) -> bool:
        """Check if card is a creature."""
        return "Creature" in self.type_line
    
    def is_land(self) -> bool:
        """Check if card is a land."""
        return "Land" in self.type_line
    
    def is_instant(self) -> bool:
        """Check if card is an instant."""
        return "Instant" in self.type_line
    
    def is_sorcery(self) -> bool:
        """Check if card is a sorcery."""
        return "Sorcery" in self.type_line
    
    def is_artifact(self) -> bool:
        """Check if card is an artifact."""
        return "Artifact" in self.type_line
    
    def is_enchantment(self) -> bool:
        """Check if card is an enchantment."""
        return "Enchantment" in self.type_line
    
    def is_planeswalker(self) -> bool:
        """Check if card is a planeswalker."""
        return "Planeswalker" in self.type_line
    
    def get_card_types(self) -> List[str]:
        """Get list of card types."""
        types = []
        for card_type in ["Creature", "Land", "Instant", "Sorcery", 
                          "Artifact", "Enchantment", "Planeswalker"]:
            if card_type in self.type_line:
                types.append(card_type)
        return types
    
    def get_creature_types(self) -> List[str]:
        """Get creature subtypes (tribal)."""
        if "—" not in self.type_line:
            return []
        
        subtypes_part = self.type_line.split("—")[1].strip()
        return subtypes_part.split()
    
    # =========================================================================
    # Interaction detection helpers
    # =========================================================================
    
    def produces_mana(self) -> bool:
        """Check if card can produce mana."""
        if self.is_land():
            return True
        return bool(re.search(r"[Aa]dd\s+\{[WUBRGC\d]\}", self.oracle_text))
    
    def has_etb_trigger(self) -> bool:
        """Check for enters-the-battlefield triggers."""
        patterns = [
            r"[Ww]hen .* enters the battlefield",
            r"[Ww]hen .* enters",
            r"[Ee]nters the battlefield"
        ]
        return any(re.search(p, self.oracle_text) for p in patterns)
    
    def has_death_trigger(self) -> bool:
        """Check for death/dies triggers."""
        patterns = [
            r"[Ww]hen .* dies",
            r"[Ww]henever .* dies",
            r"[Ww]hen .* is put into a graveyard"
        ]
        return any(re.search(p, self.oracle_text) for p in patterns)
    
    def can_sacrifice(self) -> bool:
        """Check if card can sacrifice permanents."""
        patterns = [
            r"[Ss]acrifice a",
            r"[Ss]acrifice another",
            r", [Ss]acrifice"
        ]
        return any(re.search(p, self.oracle_text) for p in patterns)
    
    def is_tutor(self) -> bool:
        """Check if card can search library."""
        patterns = [
            r"[Ss]earch your library",
            r"[Ss]earch your library for"
        ]
        return any(re.search(p, self.oracle_text) for p in patterns)
    
    def draws_cards(self) -> bool:
        """Check if card draws cards."""
        patterns = [
            r"[Dd]raw a card",
            r"[Dd]raw \d+ cards",
            r"[Dd]raw cards",
            r"[Dd]raws a card"
        ]
        return any(re.search(p, self.oracle_text) for p in patterns)
    
    def has_counter_synergy(self) -> bool:
        """Check for +1/+1 counter synergy."""
        patterns = [
            r"\+1/\+1 counter",
            r"[Pp]roliferate",
            r"[Dd]ouble the number of .* counters"
        ]
        return any(re.search(p, self.oracle_text) for p in patterns)
    
    def get_referenced_types(self) -> Set[str]:
        """Get card types referenced in oracle text."""
        types = set()
        type_patterns = [
            "creature", "artifact", "enchantment", "land", 
            "planeswalker", "instant", "sorcery"
        ]
        
        text_lower = self.oracle_text.lower()
        for type_name in type_patterns:
            if type_name in text_lower:
                types.add(type_name.capitalize())
        
        return types

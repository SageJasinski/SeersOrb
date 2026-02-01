"""Card interaction types for graph edges."""
from enum import Enum
from dataclasses import dataclass
from typing import Optional


class InteractionType(Enum):
    """Types of card interactions."""
    
    # Direct synergies
    COMBOS_WITH = "combos_with"       # Part of a combo together
    ENABLES = "enables"                # One card enables the other
    SYNERGY = "synergy"               # General synergy
    
    # Protection/Support
    PROTECTS = "protects"             # Provides protection
    BUFFS = "buffs"                   # Provides stat boost
    
    # Search/Tutoring
    TUTORS = "tutors"                 # Can search for the other card
    
    # Resource relationships
    MANA_ENABLES = "mana_enables"     # Provides mana for the other
    DRAWS_INTO = "draws_into"         # Draw effects increase odds
    
    # Tribal
    TRIBAL = "tribal"                 # Shares creature type synergy
    
    # Type synergy
    TYPE_MATTERS = "type_matters"     # Cares about card type
    
    # Sacrifice synergy
    SACRIFICE_FODDER = "sacrifice_fodder"    # Good to sacrifice
    SACRIFICE_OUTLET = "sacrifice_outlet"    # Can sacrifice things
    
    # Counter synergy
    COUNTER_SYNERGY = "counter_synergy"      # +1/+1 counter synergy
    
    # ETB/LTB
    ETB_CHAIN = "etb_chain"           # ETB trigger synergy
    DEATH_CHAIN = "death_chain"       # Death trigger synergy


@dataclass
class Interaction:
    """Represents an interaction between two cards."""
    
    source_id: str               # Card that provides the interaction
    target_id: str               # Card that benefits
    interaction_type: InteractionType
    weight: float = 1.0          # Strength of interaction (0-1)
    description: Optional[str] = None
    bidirectional: bool = False  # If True, both cards benefit equally
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "interaction_type": self.interaction_type.value,
            "weight": self.weight,
            "description": self.description,
            "bidirectional": self.bidirectional
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Interaction":
        """Create from dictionary."""
        return cls(
            source_id=data["source_id"],
            target_id=data["target_id"],
            interaction_type=InteractionType(data["interaction_type"]),
            weight=data.get("weight", 1.0),
            description=data.get("description"),
            bidirectional=data.get("bidirectional", False)
        )


# Interaction type colors for visualization
INTERACTION_COLORS = {
    InteractionType.COMBOS_WITH: "#FF6B6B",       # Red
    InteractionType.ENABLES: "#4ECDC4",           # Teal
    InteractionType.SYNERGY: "#45B7D1",           # Blue
    InteractionType.PROTECTS: "#96CEB4",          # Green
    InteractionType.BUFFS: "#FFEAA7",             # Yellow
    InteractionType.TUTORS: "#DDA0DD",            # Purple
    InteractionType.MANA_ENABLES: "#F7DC6F",      # Gold
    InteractionType.DRAWS_INTO: "#85C1E9",        # Light blue
    InteractionType.TRIBAL: "#F39C12",            # Orange
    InteractionType.TYPE_MATTERS: "#9B59B6",      # Purple
    InteractionType.SACRIFICE_FODDER: "#E74C3C",  # Dark red
    InteractionType.SACRIFICE_OUTLET: "#C0392B",  # Darker red
    InteractionType.COUNTER_SYNERGY: "#2ECC71",   # Emerald
    InteractionType.ETB_CHAIN: "#1ABC9C",         # Turquoise
    InteractionType.DEATH_CHAIN: "#34495E",       # Dark gray
}


# Interaction type labels for UI
INTERACTION_LABELS = {
    InteractionType.COMBOS_WITH: "Combos With",
    InteractionType.ENABLES: "Enables",
    InteractionType.SYNERGY: "Synergy",
    InteractionType.PROTECTS: "Protects",
    InteractionType.BUFFS: "Buffs",
    InteractionType.TUTORS: "Tutors For",
    InteractionType.MANA_ENABLES: "Provides Mana For",
    InteractionType.DRAWS_INTO: "Draws Into",
    InteractionType.TRIBAL: "Tribal Synergy",
    InteractionType.TYPE_MATTERS: "Type Matters",
    InteractionType.SACRIFICE_FODDER: "Sacrifice Fodder",
    InteractionType.SACRIFICE_OUTLET: "Sacrifice Outlet",
    InteractionType.COUNTER_SYNERGY: "Counter Synergy",
    InteractionType.ETB_CHAIN: "ETB Chain",
    InteractionType.DEATH_CHAIN: "Death Trigger Chain",
}

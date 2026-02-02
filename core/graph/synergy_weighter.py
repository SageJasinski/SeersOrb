"""Synergy weighting system with custom formula support."""
from typing import List, Dict, Set, Optional
import re

from core.models.card import Card
from core.graph.tagging import KeywordTagger

class SynergyWeighter:
    """
    Calculate synergy weights using the user-defined formula:
    S(A,B) = sum(Ti * alpha) + C
    
    Where:
    - Ti: Matching tag/keyword present in the interaction
    - alpha: User-defined weight for that tag's category
    - C: Constant bonus for direct name reference
    """
    
    # Default alpha weights per category
    DEFAULT_CATEGORY_WEIGHTS = {
        "evasion": 1.2,
        "combat": 1.1,
        "protection": 1.3,
        "speed": 1.1,
        "recursion": 1.5,
        "economy": 1.4,
        "advantage": 1.3,
        "removal": 1.2,
        "tokens": 1.5,
        "counters": 1.5,
        "graveyard": 1.4,
        "other": 1.0
    }
    
    DEFAULT_CONSTANT_C = 5.0
    
    def __init__(self, category_weights: Dict[str, float] = None):
        """
        Initialize weighter with optional custom weights.
        """
        self.category_weights = self.DEFAULT_CATEGORY_WEIGHTS.copy()
        if category_weights:
            self.category_weights.update(category_weights)
            
        self.tagger = KeywordTagger()
        
    def calculate_synergy_score(self, card1: Card, card2: Card, 
                               interaction_tags: List[str]) -> float:
        """
        Calculate S(A,B) score.
        """
        # S = sum(Ti * alpha)
        score = 0.0
        
        # Calculate weighted sum of tags
        for tag in interaction_tags:
            category = self.tagger.get_category(tag)
            alpha = self.category_weights.get(category, 1.0)
            score += 1.0 * alpha  # Ti is 1 (existence) * alpha
            
        # Add Constant C if direct reference exists
        if self.check_direct_reference(card1, card2):
            score += self.DEFAULT_CONSTANT_C
            
        return score
        
    def check_direct_reference(self, card1: Card, card2: Card) -> bool:
        """
        Check if one card explicitly names the other.
        Checking C (Constant bonus).
        """
        # Exact name match in text
        if card1.name in card2.oracle_text:
            return True
        if card2.name in card1.oracle_text:
            return True
            
        # "Search for" specific patterns
        # e.g. "search your library for a card named [Card Name]"
        # This is partly covered above, but we can be more specific if needed.
        # For now, simple name check is a strong signal of C.
        
        return False
        
    def get_shared_keywords(self, card1: Card, card2: Card) -> List[str]:
        """
        Identify shared keywords or synergistic keywords between two cards.
        This helps populate the 'interaction_tags' list.
        """
        tags = []
        
        # 1. Exact shared keywords (Tribal-like)
        k1 = set(k.lower() for k in card1.keywords)
        k2 = set(k.lower() for k in card2.keywords)
        
        shared = k1.intersection(k2)
        tags.extend(list(shared))
        
        # 2. Extract keywords from text using NLP tagger
        try:
            extracted1 = self.tagger.extract_keywords(card1.oracle_text)
            extracted2 = self.tagger.extract_keywords(card2.oracle_text)
            
            # Add extracted abilities/actions as tags if they match across cards
            # Logic: If Card A has "Flying" and Card B says "Creatures with flying...", 
            # then "Flying" is a relevant tag.
            
            # This logic mimics InteractionDetector but is centered on Keywords
            
            # Simple check: add all extracted keywords from both cards as potential tags
            # The 'interaction_tags' usually come from the Detector which says WHY they interact.
            # But here we can verify if we want to auto-discover based on text content.
            pass
        except Exception:
            pass
            
        return tags

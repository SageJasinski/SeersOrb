"""Card interaction detection system."""
from typing import List, Set, Dict, Tuple
import re

from core.models.card import Card
from core.models.interaction import Interaction, InteractionType


class InteractionDetector:
    """
    Detects interactions between cards based on various heuristics.
    
    This uses pattern matching on oracle text, keywords, and card types
    to identify synergies between cards.
    """
    
    def __init__(self):
        # Keywords that indicate sacrifice outlets
        self.sacrifice_outlet_patterns = [
            r"[Ss]acrifice a creature",
            r"[Ss]acrifice another",
            r"[Ss]acrifice a permanent",
            r", [Ss]acrifice a",
        ]
        
        # Keywords that indicate death payoffs
        self.death_trigger_patterns = [
            r"[Ww]henever .* dies",
            r"[Ww]hen .* dies",
            r"[Ww]henever another .* dies",
            r"[Ww]henever a creature dies",
        ]
        
        # ETB patterns
        self.etb_patterns = [
            r"[Ww]hen .* enters the battlefield",
            r"[Ww]hen .* enters",
            r"[Ee]nters the battlefield",
        ]
        
        # Blink/flicker patterns
        self.blink_patterns = [
            r"[Ee]xile .* then return",
            r"[Ee]xile target .* [Rr]eturn",
            r"[Ff]licker",
        ]
        
        # Counter synergy
        self.counter_add_patterns = [
            r"[Pp]ut .* \+1/\+1 counter",
            r"[Ee]nters .* with .* \+1/\+1 counter",
        ]
        
        self.counter_care_patterns = [
            r"\+1/\+1 counter",
            r"[Pp]roliferate",
            r"[Dd]ouble the number of .* counters",
            r"[Ff]or each .* counter",
        ]
        
        # Tutor patterns - indexed by what they can find
        self.tutor_type_patterns = {
            "creature": r"[Ss]earch .* for a creature",
            "artifact": r"[Ss]earch .* for an artifact",
            "enchantment": r"[Ss]earch .* for an enchantment",
            "land": r"[Ss]earch .* for a .* land",
            "instant": r"[Ss]earch .* for an instant",
            "sorcery": r"[Ss]earch .* for a sorcery",
        }
    
    def detect_all(self, cards: List[Card]) -> List[Interaction]:
        """
        Detect all interactions between the given cards.
        
        Args:
            cards: List of cards to analyze
            
        Returns:
            List of detected interactions
        """
        interactions = []
        
        # Build lookup indices
        card_by_id = {card.id: card for card in cards}
        
        # Check each pair of cards
        for i, card1 in enumerate(cards):
            for card2 in cards[i + 1:]:
                pair_interactions = self._detect_pair_interactions(card1, card2)
                interactions.extend(pair_interactions)
        
        return interactions
    
    def _detect_pair_interactions(
        self, 
        card1: Card, 
        card2: Card
    ) -> List[Interaction]:
        """Detect interactions between two specific cards."""
        interactions = []
        
        # Sacrifice synergy
        interactions.extend(self._check_sacrifice_synergy(card1, card2))
        
        # ETB synergy
        interactions.extend(self._check_etb_synergy(card1, card2))
        
        # Counter synergy
        interactions.extend(self._check_counter_synergy(card1, card2))
        
        # Tribal synergy
        interactions.extend(self._check_tribal_synergy(card1, card2))
        
        # Type matters
        interactions.extend(self._check_type_matters(card1, card2))
        
        # Mana relationships
        interactions.extend(self._check_mana_relationship(card1, card2))
        
        # Keyword synergies
        interactions.extend(self._check_keyword_synergy(card1, card2))
        
        # Tutor relationships
        interactions.extend(self._check_tutor_relationship(card1, card2))
        
        return interactions
    
    def _check_sacrifice_synergy(
        self, 
        card1: Card, 
        card2: Card
    ) -> List[Interaction]:
        """Check for sacrifice outlet + death trigger synergy."""
        interactions = []
        
        # Check if card1 is sacrifice outlet and card2 has death trigger
        c1_outlet = any(
            re.search(p, card1.oracle_text) 
            for p in self.sacrifice_outlet_patterns
        )
        c2_death = any(
            re.search(p, card2.oracle_text) 
            for p in self.death_trigger_patterns
        )
        
        if c1_outlet and c2_death:
            interactions.append(Interaction(
                source_id=card1.id,
                target_id=card2.id,
                interaction_type=InteractionType.DEATH_CHAIN,
                weight=0.8,
                description=f"{card1.name} can sacrifice creatures to trigger {card2.name}"
            ))
        
        # Check reverse
        c2_outlet = any(
            re.search(p, card2.oracle_text) 
            for p in self.sacrifice_outlet_patterns
        )
        c1_death = any(
            re.search(p, card1.oracle_text) 
            for p in self.death_trigger_patterns
        )
        
        if c2_outlet and c1_death:
            interactions.append(Interaction(
                source_id=card2.id,
                target_id=card1.id,
                interaction_type=InteractionType.DEATH_CHAIN,
                weight=0.8,
                description=f"{card2.name} can sacrifice creatures to trigger {card1.name}"
            ))
        
        # Sacrifice fodder check - creatures with death triggers are good sac targets
        if c1_outlet and card2.has_death_trigger() and card2.is_creature():
            interactions.append(Interaction(
                source_id=card1.id,
                target_id=card2.id,
                interaction_type=InteractionType.SACRIFICE_OUTLET,
                weight=0.7,
                description=f"{card1.name} can sacrifice {card2.name} for value"
            ))
        
        if c2_outlet and card1.has_death_trigger() and card1.is_creature():
            interactions.append(Interaction(
                source_id=card2.id,
                target_id=card1.id,
                interaction_type=InteractionType.SACRIFICE_OUTLET,
                weight=0.7,
                description=f"{card2.name} can sacrifice {card1.name} for value"
            ))
        
        return interactions
    
    def _check_etb_synergy(
        self, 
        card1: Card, 
        card2: Card
    ) -> List[Interaction]:
        """Check for ETB + blink synergy."""
        interactions = []
        
        c1_etb = card1.has_etb_trigger()
        c2_etb = card2.has_etb_trigger()
        
        c1_blink = any(
            re.search(p, card1.oracle_text) 
            for p in self.blink_patterns
        )
        c2_blink = any(
            re.search(p, card2.oracle_text) 
            for p in self.blink_patterns
        )
        
        # Blink enables ETB
        if c1_blink and c2_etb:
            interactions.append(Interaction(
                source_id=card1.id,
                target_id=card2.id,
                interaction_type=InteractionType.ETB_CHAIN,
                weight=0.85,
                description=f"{card1.name} can reuse {card2.name}'s ETB"
            ))
        
        if c2_blink and c1_etb:
            interactions.append(Interaction(
                source_id=card2.id,
                target_id=card1.id,
                interaction_type=InteractionType.ETB_CHAIN,
                weight=0.85,
                description=f"{card2.name} can reuse {card1.name}'s ETB"
            ))
        
        return interactions
    
    def _check_counter_synergy(
        self, 
        card1: Card, 
        card2: Card
    ) -> List[Interaction]:
        """Check for +1/+1 counter synergy."""
        interactions = []
        
        c1_adds = any(
            re.search(p, card1.oracle_text) 
            for p in self.counter_add_patterns
        )
        c2_adds = any(
            re.search(p, card2.oracle_text) 
            for p in self.counter_add_patterns
        )
        
        c1_cares = card1.has_counter_synergy()
        c2_cares = card2.has_counter_synergy()
        
        # Cards that add counters synergize with cards that care about counters
        if c1_adds and c2_cares:
            interactions.append(Interaction(
                source_id=card1.id,
                target_id=card2.id,
                interaction_type=InteractionType.COUNTER_SYNERGY,
                weight=0.75,
                description=f"{card1.name} adds counters for {card2.name}"
            ))
        
        if c2_adds and c1_cares:
            interactions.append(Interaction(
                source_id=card2.id,
                target_id=card1.id,
                interaction_type=InteractionType.COUNTER_SYNERGY,
                weight=0.75,
                description=f"{card2.name} adds counters for {card1.name}"
            ))
        
        # Both cards care about counters = synergy
        if c1_cares and c2_cares and (c1_adds or c2_adds):
            interactions.append(Interaction(
                source_id=card1.id,
                target_id=card2.id,
                interaction_type=InteractionType.COUNTER_SYNERGY,
                weight=0.7,
                bidirectional=True,
                description=f"Both {card1.name} and {card2.name} work with counters"
            ))
        
        return interactions
    
    def _check_tribal_synergy(
        self, 
        card1: Card, 
        card2: Card
    ) -> List[Interaction]:
        """Check for tribal (creature type) synergy."""
        interactions = []
        
        # Get creature types
        types1 = set(card1.get_creature_types())
        types2 = set(card2.get_creature_types())
        
        # Check for shared types
        shared_types = types1 & types2
        
        if shared_types and card1.is_creature() and card2.is_creature():
            interactions.append(Interaction(
                source_id=card1.id,
                target_id=card2.id,
                interaction_type=InteractionType.TRIBAL,
                weight=0.5,
                bidirectional=True,
                description=f"Both are {', '.join(shared_types)}"
            ))
        
        # Check if one card references the type of another
        text1_lower = card1.oracle_text.lower()
        text2_lower = card2.oracle_text.lower()
        
        for ctype in types2:
            if ctype.lower() in text1_lower:
                interactions.append(Interaction(
                    source_id=card1.id,
                    target_id=card2.id,
                    interaction_type=InteractionType.TRIBAL,
                    weight=0.7,
                    description=f"{card1.name} cares about {ctype}s"
                ))
        
        for ctype in types1:
            if ctype.lower() in text2_lower:
                interactions.append(Interaction(
                    source_id=card2.id,
                    target_id=card1.id,
                    interaction_type=InteractionType.TRIBAL,
                    weight=0.7,
                    description=f"{card2.name} cares about {ctype}s"
                ))
        
        return interactions
    
    def _check_type_matters(
        self, 
        card1: Card, 
        card2: Card
    ) -> List[Interaction]:
        """Check for card type matters synergy (artifact/enchantment/etc matters)."""
        interactions = []
        
        # Get types each card cares about
        types1_cares = card1.get_referenced_types()
        types2_cares = card2.get_referenced_types()
        
        # Get actual types
        types1_is = set(card1.get_card_types())
        types2_is = set(card2.get_card_types())
        
        # Card1 cares about types that Card2 is
        matches = types1_cares & types2_is
        if matches:
            interactions.append(Interaction(
                source_id=card1.id,
                target_id=card2.id,
                interaction_type=InteractionType.TYPE_MATTERS,
                weight=0.6,
                description=f"{card1.name} cares about {', '.join(matches)}"
            ))
        
        # Card2 cares about types that Card1 is
        matches = types2_cares & types1_is
        if matches:
            interactions.append(Interaction(
                source_id=card2.id,
                target_id=card1.id,
                interaction_type=InteractionType.TYPE_MATTERS,
                weight=0.6,
                description=f"{card2.name} cares about {', '.join(matches)}"
            ))
        
        return interactions
    
    def _check_mana_relationship(
        self, 
        card1: Card, 
        card2: Card
    ) -> List[Interaction]:
        """Check for mana production relationships."""
        interactions = []
        
        # Check if card1 produces mana for card2
        if card1.produces_mana() and not card2.is_land():
            # Higher weight for ramp into expensive spells
            weight = min(0.4 + (card2.cmc * 0.05), 0.8)
            if card2.cmc >= 4:
                interactions.append(Interaction(
                    source_id=card1.id,
                    target_id=card2.id,
                    interaction_type=InteractionType.MANA_ENABLES,
                    weight=weight,
                    description=f"{card1.name} helps cast {card2.name}"
                ))
        
        # Check if card2 produces mana for card1
        if card2.produces_mana() and not card1.is_land():
            weight = min(0.4 + (card1.cmc * 0.05), 0.8)
            if card1.cmc >= 4:
                interactions.append(Interaction(
                    source_id=card2.id,
                    target_id=card1.id,
                    interaction_type=InteractionType.MANA_ENABLES,
                    weight=weight,
                    description=f"{card2.name} helps cast {card1.name}"
                ))
        
        return interactions
    
    def _check_keyword_synergy(
        self, 
        card1: Card, 
        card2: Card
    ) -> List[Interaction]:
        """Check for keyword ability synergies."""
        interactions = []
        
        keywords1 = set(k.lower() for k in card1.keywords)
        keywords2 = set(k.lower() for k in card2.keywords)
        
        # Flying synergies
        if "flying" in keywords1 and "reach" in keywords2:
            pass  # Not really synergy
        
        # Deathtouch + First Strike/Double Strike
        if "deathtouch" in keywords1:
            if "first strike" in keywords2 or "double strike" in keywords2:
                # Card2 could give first strike to card1
                if "target creature gains" in card2.oracle_text.lower():
                    interactions.append(Interaction(
                        source_id=card2.id,
                        target_id=card1.id,
                        interaction_type=InteractionType.BUFFS,
                        weight=0.75,
                        description=f"First strike + deathtouch combo"
                    ))
        
        if "deathtouch" in keywords2:
            if "first strike" in keywords1 or "double strike" in keywords1:
                if "target creature gains" in card1.oracle_text.lower():
                    interactions.append(Interaction(
                        source_id=card1.id,
                        target_id=card2.id,
                        interaction_type=InteractionType.BUFFS,
                        weight=0.75,
                        description=f"First strike + deathtouch combo"
                    ))
        
        # Lifelink synergy
        if "lifelink" in keywords1 or "lifelink" in keywords2:
            # Check for life gain payoffs
            text1 = card1.oracle_text.lower()
            text2 = card2.oracle_text.lower()
            
            if "lifelink" in keywords1 and "whenever you gain life" in text2:
                interactions.append(Interaction(
                    source_id=card1.id,
                    target_id=card2.id,
                    interaction_type=InteractionType.ENABLES,
                    weight=0.7,
                    description=f"{card1.name} triggers {card2.name}"
                ))
            
            if "lifelink" in keywords2 and "whenever you gain life" in text1:
                interactions.append(Interaction(
                    source_id=card2.id,
                    target_id=card1.id,
                    interaction_type=InteractionType.ENABLES,
                    weight=0.7,
                    description=f"{card2.name} triggers {card1.name}"
                ))
        
        return interactions
    
    def _check_tutor_relationship(
        self, 
        card1: Card, 
        card2: Card
    ) -> List[Interaction]:
        """Check if one card can tutor for another."""
        interactions = []
        
        # Check if card1 can tutor for card2
        for card_type, pattern in self.tutor_type_patterns.items():
            if re.search(pattern, card1.oracle_text):
                if card_type.capitalize() in card2.type_line:
                    interactions.append(Interaction(
                        source_id=card1.id,
                        target_id=card2.id,
                        interaction_type=InteractionType.TUTORS,
                        weight=0.9,
                        description=f"{card1.name} can find {card2.name}"
                    ))
        
        # Check if card2 can tutor for card1
        for card_type, pattern in self.tutor_type_patterns.items():
            if re.search(pattern, card2.oracle_text):
                if card_type.capitalize() in card1.type_line:
                    interactions.append(Interaction(
                        source_id=card2.id,
                        target_id=card1.id,
                        interaction_type=InteractionType.TUTORS,
                        weight=0.9,
                        description=f"{card2.name} can find {card1.name}"
                    ))
        
        return interactions

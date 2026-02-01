"""Multivariate hypergeometric distribution for combo probabilities."""
from typing import List, Dict, Tuple
import numpy as np
from scipy import stats


class MultivariateCalculator:
    """
    Calculate probabilities using the multivariate hypergeometric distribution.
    
    Use this for questions like:
    - "What's the probability of drawing Sol Ring AND Command Tower in my opening hand?"
    - "What's the chance I draw at least 1 of each combo piece?"
    
    The multivariate hypergeometric models drawing multiple types of cards
    without replacement simultaneously.
    
    Parameters:
    - N (deck_size): Total cards in deck
    - K_i (card_counts): Number of each type of card we care about
    - n (cards_drawn): Number of cards drawn
    - k_i (successes): Number of each type we want to draw
    """
    
    def __init__(
        self, 
        deck_size: int = 99, 
        card_counts: List[int] = None,
        cards_drawn: int = 7
    ):
        """
        Initialize the calculator.
        
        Args:
            deck_size: Total cards in the deck
            card_counts: List of copy counts for each card type we care about
                        e.g., [1, 4, 3] for 1 Sol Ring, 4 Bolts, 3 Counterspells
            cards_drawn: Number of cards drawn
        """
        self.deck_size = deck_size
        self.card_counts = card_counts or []
        self.cards_drawn = cards_drawn
        
        # Calculate "other" cards
        self.cards_of_interest = sum(self.card_counts)
        self.other_cards = deck_size - self.cards_of_interest
        
        if self.other_cards < 0:
            raise ValueError("Card counts exceed deck size")
    
    def probability(self, successes: List[int]) -> float:
        """
        Calculate probability of drawing exactly the specified number of each card type.
        
        Args:
            successes: List of exact counts for each card type
                      e.g., [1, 2, 0] means exactly 1 of type 1, 2 of type 2, 0 of type 3
                      
        Returns:
            Probability (0 to 1)
        """
        if len(successes) != len(self.card_counts):
            raise ValueError("Successes must match card_counts length")
        
        # Check if request is possible
        for s, c in zip(successes, self.card_counts):
            if s < 0 or s > c:
                return 0.0
        
        total_successes = sum(successes)
        if total_successes > self.cards_drawn:
            return 0.0
        
        # Number of "other" cards drawn
        other_drawn = self.cards_drawn - total_successes
        if other_drawn < 0 or other_drawn > self.other_cards:
            return 0.0
        
        # Build the full population and sample
        m = self.card_counts + [self.other_cards]  # Population of each type
        x = successes + [other_drawn]              # Drawn of each type
        
        # Use scipy's multivariate_hypergeom
        return stats.multivariate_hypergeom.pmf(x, m, self.cards_drawn)
    
    def at_least(self, min_successes: List[int]) -> float:
        """
        Calculate probability of drawing at least the specified number of each card type.
        
        This is the most common combo question:
        "What's the chance I draw at least 1 of each combo piece?"
        
        Args:
            min_successes: List of minimum counts for each card type
            
        Returns:
            Probability (0 to 1)
        """
        if len(min_successes) != len(self.card_counts):
            raise ValueError("min_successes must match card_counts length")
        
        # We need to sum over all combinations that meet the minimums
        # This uses inclusion-exclusion principle internally via enumeration
        total_prob = 0.0
        
        # Generate all valid combinations
        for combo in self._generate_combinations(min_successes):
            total_prob += self.probability(combo)
        
        return total_prob
    
    def _generate_combinations(self, min_successes: List[int]) -> List[List[int]]:
        """Generate all valid combinations meeting minimums."""
        combinations = []
        
        # Max for each slot
        maxes = [
            min(count, self.cards_drawn) 
            for count in self.card_counts
        ]
        
        def generate(index: int, current: List[int], remaining: int):
            if index == len(self.card_counts):
                if remaining >= 0 and remaining <= self.other_cards:
                    combinations.append(current.copy())
                return
            
            for val in range(min_successes[index], maxes[index] + 1):
                if val <= remaining:
                    current.append(val)
                    generate(index + 1, current, remaining - val)
                    current.pop()
        
        generate(0, [], self.cards_drawn)
        return combinations
    
    def combo_probability(
        self,
        pieces: List[Dict[str, int]],
        at_least_each: int = 1
    ) -> float:
        """
        Simplified interface for combo probability.
        
        Args:
            pieces: List of dictionaries with 'copies' key
                   e.g., [{'copies': 1}, {'copies': 4}, {'copies': 2}]
            at_least_each: Minimum of each piece needed (default: 1)
            
        Returns:
            Probability of having at least the required copies of each piece
        """
        self.card_counts = [p['copies'] for p in pieces]
        self.cards_of_interest = sum(self.card_counts)
        self.other_cards = self.deck_size - self.cards_of_interest
        
        min_successes = [at_least_each] * len(pieces)
        return self.at_least(min_successes)


# =============================================================================
# Convenience functions
# =============================================================================

def two_card_combo_probability(
    deck_size: int,
    copies_a: int,
    copies_b: int,
    cards_drawn: int = 7
) -> float:
    """
    Calculate probability of drawing at least one of each of two combo pieces.
    
    Args:
        deck_size: Total deck size
        copies_a: Copies of piece A
        copies_b: Copies of piece B
        cards_drawn: Cards drawn
        
    Returns:
        Probability
    """
    calc = MultivariateCalculator(deck_size, [copies_a, copies_b], cards_drawn)
    return calc.at_least([1, 1])


def three_card_combo_probability(
    deck_size: int,
    copies_a: int,
    copies_b: int,
    copies_c: int,
    cards_drawn: int = 7
) -> float:
    """
    Calculate probability of drawing at least one of each of three combo pieces.
    
    Args:
        deck_size: Total deck size
        copies_a: Copies of piece A
        copies_b: Copies of piece B
        copies_c: Copies of piece C
        cards_drawn: Cards drawn
        
    Returns:
        Probability
    """
    calc = MultivariateCalculator(
        deck_size, 
        [copies_a, copies_b, copies_c], 
        cards_drawn
    )
    return calc.at_least([1, 1, 1])


def land_and_spell_probability(
    deck_size: int,
    lands: int,
    min_lands: int,
    min_spells: int,
    cards_drawn: int = 7
) -> float:
    """
    Calculate probability of a balanced opening hand.
    
    Args:
        deck_size: Total deck size
        lands: Total lands in deck
        min_lands: Minimum lands wanted
        min_spells: Minimum spells wanted
        cards_drawn: Cards drawn
        
    Returns:
        Probability of meeting both requirements
    """
    spells = deck_size - lands
    calc = MultivariateCalculator(deck_size, [lands, spells], cards_drawn)
    return calc.at_least([min_lands, min_spells])


def opening_hand_analysis(
    deck_size: int,
    lands: int,
    key_cards: List[int],
    key_card_needs: List[int] = None
) -> Dict[str, float]:
    """
    Comprehensive opening hand analysis.
    
    Args:
        deck_size: Total deck size
        lands: Total lands in deck
        key_cards: List of copy counts for key cards
        key_card_needs: List of minimum copies needed (default: 1 each)
        
    Returns:
        Dictionary with various probabilities
    """
    if key_card_needs is None:
        key_card_needs = [1] * len(key_cards)
    
    cards_drawn = 7
    
    # Just lands analysis
    from core.probability.hypergeometric import HypergeometricCalculator
    land_calc = HypergeometricCalculator(deck_size, lands, cards_drawn)
    
    results = {
        "at_least_2_lands": land_calc.at_least(2),
        "at_least_3_lands": land_calc.at_least(3),
        "exactly_3_lands": land_calc.exactly(3),
        "0_lands": land_calc.exactly(0),
        "flood_5plus_lands": land_calc.at_least(5),
    }
    
    # Key card analysis
    if key_cards:
        all_cards = [lands] + key_cards
        other_cards = deck_size - sum(all_cards)
        
        if other_cards >= 0:
            # Probability of 2+ lands AND at least 1 of each key card
            calc = MultivariateCalculator(deck_size, all_cards, cards_drawn)
            
            # This is complex - we need lands >= 2 AND each key card >= 1
            # We'll use a simplified approach
            total_prob = 0.0
            
            for land_count in range(2, min(lands, cards_drawn) + 1):
                remaining = cards_drawn - land_count
                if remaining >= len(key_cards):
                    # Need at least 1 of each key card in remaining slots
                    inner_calc = MultivariateCalculator(
                        deck_size - lands,
                        key_cards,
                        remaining
                    )
                    key_prob = inner_calc.at_least(key_card_needs)
                    land_prob = land_calc.exactly(land_count)
                    total_prob += land_prob * key_prob
            
            results["lands_plus_key_cards"] = total_prob
    
    return results

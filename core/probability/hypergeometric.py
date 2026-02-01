"""Hypergeometric distribution calculator for single card probabilities."""
from typing import Dict, List, Tuple
from scipy import stats


class HypergeometricCalculator:
    """
    Calculate probabilities using the hypergeometric distribution.
    
    Use this for questions like:
    - "What's the probability of drawing at least 1 Sol Ring in my opening hand?"
    - "What's the chance I hit 3 lands in 7 cards?"
    
    The hypergeometric distribution models drawing without replacement,
    which is exactly how MTG works.
    
    Parameters:
    - N (deck_size): Total cards in deck
    - K (copies): Number of success cards (copies of the target card)
    - n (cards_drawn): Number of cards drawn
    - k (successes): Number of successes we want
    """
    
    def __init__(self, deck_size: int = 99, copies: int = 1, cards_drawn: int = 7):
        """
        Initialize the calculator.
        
        Args:
            deck_size: Total cards in the deck (default: 99 for Commander)
            copies: Number of copies of the target card
            cards_drawn: Number of cards drawn
        """
        self.deck_size = deck_size
        self.copies = copies
        self.cards_drawn = cards_drawn
        
        # Validate inputs
        if copies > deck_size:
            raise ValueError("Copies cannot exceed deck size")
        if cards_drawn > deck_size:
            raise ValueError("Cards drawn cannot exceed deck size")
    
    def exactly(self, successes: int) -> float:
        """
        P(X = k): Probability of drawing exactly k copies.
        
        Args:
            successes: Exact number of copies to draw
            
        Returns:
            Probability (0 to 1)
        """
        if successes > self.copies or successes > self.cards_drawn:
            return 0.0
        if successes < 0:
            return 0.0
        
        # PMF: P(X = k)
        return stats.hypergeom.pmf(
            successes,
            self.deck_size,
            self.copies,
            self.cards_drawn
        )
    
    def at_least(self, successes: int) -> float:
        """
        P(X >= k): Probability of drawing at least k copies.
        
        This is the most common question:
        "What's the chance I see at least 1 copy?"
        
        Args:
            successes: Minimum number of copies to draw
            
        Returns:
            Probability (0 to 1)
        """
        if successes <= 0:
            return 1.0
        if successes > self.copies or successes > self.cards_drawn:
            return 0.0
        
        # SF: P(X >= k) = 1 - P(X < k) = 1 - CDF(k-1)
        return stats.hypergeom.sf(
            successes - 1,
            self.deck_size,
            self.copies,
            self.cards_drawn
        )
    
    def at_most(self, successes: int) -> float:
        """
        P(X <= k): Probability of drawing at most k copies.
        
        Args:
            successes: Maximum number of copies to draw
            
        Returns:
            Probability (0 to 1)
        """
        if successes < 0:
            return 0.0
        if successes >= min(self.copies, self.cards_drawn):
            return 1.0
        
        # CDF: P(X <= k)
        return stats.hypergeom.cdf(
            successes,
            self.deck_size,
            self.copies,
            self.cards_drawn
        )
    
    def full_distribution(self) -> Dict[int, float]:
        """
        Get the full probability distribution.
        
        Returns:
            Dictionary of {k: P(X = k)} for all possible values
        """
        max_successes = min(self.copies, self.cards_drawn)
        return {
            k: self.exactly(k)
            for k in range(max_successes + 1)
        }
    
    def mean(self) -> float:
        """
        Expected number of copies drawn.
        
        Returns:
            Expected value
        """
        return stats.hypergeom.mean(
            self.deck_size,
            self.copies,
            self.cards_drawn
        )
    
    def variance(self) -> float:
        """
        Variance of the distribution.
        
        Returns:
            Variance
        """
        return stats.hypergeom.var(
            self.deck_size,
            self.copies,
            self.cards_drawn
        )
    
    def std_dev(self) -> float:
        """
        Standard deviation of the distribution.
        
        Returns:
            Standard deviation
        """
        return stats.hypergeom.std(
            self.deck_size,
            self.copies,
            self.cards_drawn
        )


# =============================================================================
# Convenience functions
# =============================================================================

def opening_hand_probability(
    deck_size: int, 
    copies: int, 
    at_least: int = 1
) -> float:
    """
    Calculate probability of seeing a card in opening hand.
    
    Args:
        deck_size: Total deck size
        copies: Number of copies
        at_least: Minimum copies to see (default: 1)
        
    Returns:
        Probability
    """
    calc = HypergeometricCalculator(deck_size, copies, 7)
    return calc.at_least(at_least)


def probability_by_turn(
    deck_size: int,
    copies: int,
    turn: int,
    at_least: int = 1,
    on_play: bool = True
) -> float:
    """
    Calculate probability of seeing a card by a given turn.
    
    Args:
        deck_size: Total deck size
        copies: Number of copies
        turn: Turn number (1-indexed)
        at_least: Minimum copies to see
        on_play: True if on the play, False if on the draw
        
    Returns:
        Probability
    """
    # On the play: 7 + (turn - 1) cards
    # On the draw: 7 + turn cards (extra draw turn 1)
    if on_play:
        cards_seen = 7 + (turn - 1)
    else:
        cards_seen = 7 + turn
    
    # Can't see more cards than deck size
    cards_seen = min(cards_seen, deck_size)
    
    calc = HypergeometricCalculator(deck_size, copies, cards_seen)
    return calc.at_least(at_least)


def optimal_copies(
    deck_size: int,
    target_probability: float,
    by_cards_drawn: int = 7
) -> int:
    """
    Find optimal number of copies to hit a target probability.
    
    Args:
        deck_size: Total deck size
        target_probability: Desired probability (0 to 1)
        by_cards_drawn: Cards drawn (default: 7 for opening hand)
        
    Returns:
        Recommended number of copies
    """
    for copies in range(1, deck_size + 1):
        calc = HypergeometricCalculator(deck_size, copies, by_cards_drawn)
        if calc.at_least(1) >= target_probability:
            return copies
    
    return deck_size


def mulligan_impact(
    deck_size: int,
    copies: int,
    mulligan_to: int = 6
) -> Dict[str, float]:
    """
    Calculate how mulliganing affects seeing a card.
    
    Args:
        deck_size: Total deck size
        copies: Number of copies
        mulligan_to: Hand size after mulligan
        
    Returns:
        Dictionary with probabilities for different scenarios
    """
    # Original 7 card hand
    keep_7 = HypergeometricCalculator(deck_size, copies, 7).at_least(1)
    
    # After mulligan (simplified - ignoring bottom card)
    mull_to = HypergeometricCalculator(deck_size, copies, mulligan_to).at_least(1)
    
    # Probability of seeing it in either the 7 OR the mulligan
    # P(A ∪ B) = P(A) + P(B) - P(A ∩ B)
    # But since mulligan reshuffles, they're independent
    # P(see it at some point) = 1 - P(don't see in 7) * P(don't see in mull)
    combined = 1 - (1 - keep_7) * (1 - mull_to)
    
    return {
        "keep_7": keep_7,
        f"mulligan_to_{mulligan_to}": mull_to,
        "see_in_either": combined
    }

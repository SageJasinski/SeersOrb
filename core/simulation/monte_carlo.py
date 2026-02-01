"""Monte Carlo simulation engine for deck testing."""
import random
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from collections import Counter
import numpy as np

from core.models.deck import Deck
from core.models.card import Card


@dataclass
class SimulationResult:
    """Results from a single simulation run."""
    
    success: bool
    turn_achieved: Optional[int] = None
    opening_hand: List[Card] = field(default_factory=list)
    cards_drawn: List[Card] = field(default_factory=list)
    mulligans: int = 0
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SimulationStats:
    """Aggregated statistics from multiple simulation runs."""
    
    iterations: int
    successes: int
    success_rate: float
    average_turn: float
    turn_distribution: Dict[int, int]
    mulligan_stats: Dict[int, int]
    
    # Confidence interval
    confidence_level: float = 0.95
    confidence_interval: tuple = (0.0, 0.0)
    
    # Additional metrics
    card_frequency_in_wins: Dict[str, float] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "iterations": self.iterations,
            "successes": self.successes,
            "success_rate": round(self.success_rate, 4),
            "success_percentage": round(self.success_rate * 100, 2),
            "average_turn": round(self.average_turn, 2) if self.average_turn else None,
            "turn_distribution": self.turn_distribution,
            "mulligan_stats": self.mulligan_stats,
            "confidence_level": self.confidence_level,
            "confidence_interval": {
                "lower": round(self.confidence_interval[0], 4),
                "upper": round(self.confidence_interval[1], 4)
            },
            "card_frequency_in_wins": self.card_frequency_in_wins
        }


class MonteCarloSimulator:
    """
    Monte Carlo simulation engine for testing deck consistency.
    
    Simulates game scenarios (opening hands, draws, mulligans) to
    estimate probabilities that may be too complex for analytical solutions.
    """
    
    def __init__(self, deck: Deck):
        """
        Initialize the simulator.
        
        Args:
            deck: The deck to simulate
        """
        self.deck = deck
        self.card_library = self._build_library()
    
    def _build_library(self) -> List[Card]:
        """Build a flat list of cards respecting quantities."""
        library = []
        for entry in self.deck.cards.values():
            for _ in range(entry.quantity):
                library.append(entry.card)
        return library
    
    def shuffle(self) -> List[Card]:
        """Return a shuffled copy of the library."""
        library = self.card_library.copy()
        random.shuffle(library)
        return library
    
    def draw_hand(
        self, 
        library: List[Card], 
        hand_size: int = 7
    ) -> tuple:
        """
        Draw an opening hand.
        
        Returns:
            Tuple of (hand, remaining_library)
        """
        hand = library[:hand_size]
        remaining = library[hand_size:]
        return hand, remaining
    
    def run(
        self,
        iterations: int = 10000,
        criteria: Dict = None,
        max_turn: int = 10,
        mulligan_strategy: Callable = None
    ) -> Dict:
        """
        Run Monte Carlo simulation.
        
        Args:
            iterations: Number of simulations to run
            criteria: Success criteria dictionary with keys like:
                     - 'cards': List of card names that must be present
                     - 'min_lands': Minimum lands required
                     - 'min_cmc_X': Minimum cards at CMC X or less
                     - 'custom': Custom function(hand, turn) -> bool
            max_turn: Maximum turn to simulate
            mulligan_strategy: Function(hand) -> bool, True = mulligan
            
        Returns:
            SimulationStats as dictionary
        """
        if criteria is None:
            criteria = {"min_lands": 2}
        
        results: List[SimulationResult] = []
        
        for _ in range(iterations):
            result = self._run_single(
                criteria=criteria,
                max_turn=max_turn,
                mulligan_strategy=mulligan_strategy
            )
            results.append(result)
        
        return self._aggregate_results(results).to_dict()
    
    def _run_single(
        self,
        criteria: Dict,
        max_turn: int,
        mulligan_strategy: Callable = None
    ) -> SimulationResult:
        """Run a single simulation."""
        library = self.shuffle()
        mulligans = 0
        hand_size = 7
        
        # Mulligan phase
        if mulligan_strategy:
            while hand_size >= 4:
                hand, library = self.draw_hand(library, hand_size)
                
                if mulligan_strategy(hand):
                    mulligans += 1
                    hand_size -= 1
                    library = self.shuffle()
                else:
                    break
        else:
            hand, library = self.draw_hand(library, 7)
        
        # Check opening hand
        if self._check_criteria(hand, criteria, turn=0):
            return SimulationResult(
                success=True,
                turn_achieved=0,
                opening_hand=hand,
                mulligans=mulligans
            )
        
        # Simulate turns
        cards_drawn = []
        for turn in range(1, max_turn + 1):
            if library:
                draw = library.pop(0)
                cards_drawn.append(draw)
                hand.append(draw)
            
            if self._check_criteria(hand, criteria, turn=turn):
                return SimulationResult(
                    success=True,
                    turn_achieved=turn,
                    opening_hand=hand[:7],
                    cards_drawn=cards_drawn,
                    mulligans=mulligans
                )
        
        return SimulationResult(
            success=False,
            opening_hand=hand[:7],
            cards_drawn=cards_drawn,
            mulligans=mulligans
        )
    
    def _check_criteria(
        self, 
        hand: List[Card], 
        criteria: Dict, 
        turn: int
    ) -> bool:
        """Check if hand meets the success criteria."""
        
        # Check minimum lands
        if "min_lands" in criteria:
            land_count = sum(1 for c in hand if c.is_land())
            if land_count < criteria["min_lands"]:
                return False
        
        # Check maximum lands (anti-flood)
        if "max_lands" in criteria:
            land_count = sum(1 for c in hand if c.is_land())
            if land_count > criteria["max_lands"]:
                return False
        
        # Check required cards by name
        if "cards" in criteria:
            hand_names = [c.name for c in hand]
            for required_card in criteria["cards"]:
                if required_card not in hand_names:
                    return False
        
        # Check at least one of cards
        if "any_of" in criteria:
            hand_names = set(c.name for c in hand)
            if not any(card in hand_names for card in criteria["any_of"]):
                return False
        
        # Check minimum CMC curve
        if "min_cmc_plays" in criteria:
            # Can we play something each turn up to N?
            for target_turn, min_cards in criteria["min_cmc_plays"].items():
                castable = sum(
                    1 for c in hand 
                    if not c.is_land() and c.cmc <= target_turn
                )
                if castable < min_cards:
                    return False
        
        # Check mana availability by turn
        if "mana_by_turn" in criteria and turn > 0:
            lands_in_hand = sum(1 for c in hand if c.is_land())
            required_mana = criteria["mana_by_turn"].get(turn, 0)
            # Simplified: assume 1 land drop per turn
            available_mana = min(lands_in_hand, turn)
            if available_mana < required_mana:
                return False
        
        # Custom criteria function
        if "custom" in criteria:
            if not criteria["custom"](hand, turn):
                return False
        
        return True
    
    def _aggregate_results(
        self, 
        results: List[SimulationResult]
    ) -> SimulationStats:
        """Aggregate individual results into statistics."""
        iterations = len(results)
        successes = sum(1 for r in results if r.success)
        success_rate = successes / iterations if iterations > 0 else 0
        
        # Turn distribution
        turn_dist = Counter(
            r.turn_achieved for r in results 
            if r.success and r.turn_achieved is not None
        )
        
        # Average turn for successes
        successful_turns = [
            r.turn_achieved for r in results 
            if r.success and r.turn_achieved is not None
        ]
        avg_turn = np.mean(successful_turns) if successful_turns else None
        
        # Mulligan stats
        mulligan_dist = Counter(r.mulligans for r in results)
        
        # Confidence interval using Wilson score
        ci = self._wilson_score_interval(successes, iterations)
        
        # Card frequency in winning hands
        card_freq = {}
        winning_results = [r for r in results if r.success]
        if winning_results:
            total_wins = len(winning_results)
            for result in winning_results:
                all_cards = result.opening_hand + result.cards_drawn
                for card in set(c.name for c in all_cards):
                    card_freq[card] = card_freq.get(card, 0) + 1
            
            card_freq = {
                name: round(count / total_wins, 3)
                for name, count in sorted(
                    card_freq.items(), 
                    key=lambda x: x[1], 
                    reverse=True
                )[:20]
            }
        
        return SimulationStats(
            iterations=iterations,
            successes=successes,
            success_rate=success_rate,
            average_turn=avg_turn,
            turn_distribution=dict(turn_dist),
            mulligan_stats=dict(mulligan_dist),
            confidence_interval=ci,
            card_frequency_in_wins=card_freq
        )
    
    def _wilson_score_interval(
        self, 
        successes: int, 
        n: int, 
        confidence: float = 0.95
    ) -> tuple:
        """Calculate Wilson score confidence interval."""
        if n == 0:
            return (0.0, 0.0)
        
        from scipy import stats as scipy_stats
        
        z = scipy_stats.norm.ppf(1 - (1 - confidence) / 2)
        p = successes / n
        
        denominator = 1 + z**2 / n
        center = (p + z**2 / (2 * n)) / denominator
        margin = z * np.sqrt((p * (1 - p) + z**2 / (4 * n)) / n) / denominator
        
        return (max(0, center - margin), min(1, center + margin))


# =============================================================================
# Pre-built mulligan strategies
# =============================================================================

def standard_mulligan_strategy(hand: List[Card]) -> bool:
    """
    Standard mulligan strategy: keep 2-5 lands.
    
    Args:
        hand: Current hand
        
    Returns:
        True if should mulligan
    """
    lands = sum(1 for c in hand if c.is_land())
    return lands < 2 or lands > 5


def aggressive_mulligan_strategy(hand: List[Card]) -> bool:
    """
    Aggressive mulligan: need 2-4 lands AND a 1-2 drop.
    
    Args:
        hand: Current hand
        
    Returns:
        True if should mulligan
    """
    lands = sum(1 for c in hand if c.is_land())
    early_plays = sum(
        1 for c in hand 
        if not c.is_land() and c.cmc <= 2
    )
    
    return lands < 2 or lands > 4 or early_plays < 1


def combo_mulligan_strategy(
    required_pieces: List[str],
    min_pieces: int = 1
) -> Callable:
    """
    Create a mulligan strategy for combo decks.
    
    Args:
        required_pieces: Names of combo pieces
        min_pieces: Minimum pieces needed to keep
        
    Returns:
        Mulligan function
    """
    def strategy(hand: List[Card]) -> bool:
        lands = sum(1 for c in hand if c.is_land())
        if lands < 2 or lands > 5:
            return True
        
        pieces_found = sum(
            1 for c in hand if c.name in required_pieces
        )
        return pieces_found < min_pieces
    
    return strategy

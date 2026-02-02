"""Smoke test for connected graph components."""
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from core.models.card import Card
from core.models.deck import Deck
from core.graph.deck_graph import DeckGraph
from core.graph.visualizer import GraphVisualizer

def test_visualization():
    print("Initializing test...")
    
    # Create dummy deck
    deck = Deck(name="Test Synergies")
    
    # Create cards with synergistic text
    card1 = Card(
        id="c1", 
        name="Sacrifice Outlet", 
        oracle_text="Sacrifice a creature: Add {B}.",
        type_line="Artifact",
        cmc=2.0
    )
    
    card2 = Card(
        id="c2",
        name="Death Trigger",
        oracle_text="When this creature dies, draw a card.",
        type_line="Creature",
        cmc=3.0,
        keywords=["Flying"]
    )
    
    card3 = Card(
        id="c3",
        name="Keyword Lord",
        oracle_text="Creatures with flying get +1/+1.",
        type_line="Enchantment",
        cmc=4.0
    )
    
    deck.add_card(card1)
    deck.add_card(card2)
    deck.add_card(card3)
    
    print("Detecting interactions...")
    graph = DeckGraph(deck)
    graph.detect_interactions()
    
    print(f"Found {len(graph.interactions)} interactions.")
    for i in graph.interactions:
        print(f" - {i.source_id} -> {i.target_id}: {i.interaction_type} ({i.weight})")
        
    print("Generating visualization...")
    viz = GraphVisualizer(output_dir=Path("tests/output"))
    path = viz.generate_visualization(graph, "test_graph.html")
    
    print(f"Generated HTML at: {path}")
    
    # Check if file exists and has size
    p = Path(path)
    if p.exists() and p.stat().st_size > 0:
        print("SUCCESS: Graph HTML generated.")
    else:
        print("FAILURE: output file invalid.")

if __name__ == "__main__":
    test_visualization()

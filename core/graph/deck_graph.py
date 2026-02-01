"""Deck graph representation using NetworkX."""
from typing import List, Dict, Optional, Set, Tuple
import networkx as nx

from core.models.deck import Deck
from core.models.card import Card
from core.models.interaction import (
    Interaction, InteractionType, 
    INTERACTION_COLORS, INTERACTION_LABELS
)
from core.graph.interaction_detector import InteractionDetector


class DeckGraph:
    """
    Graph representation of a deck where:
    - Nodes = Cards
    - Edges = Interactions between cards
    """
    
    def __init__(self, deck: Deck, auto_detect: bool = True):
        """
        Initialize the deck graph.
        
        Args:
            deck: The deck to represent
            auto_detect: Whether to auto-detect interactions
        """
        self.deck = deck
        self.graph = nx.Graph()
        self.interactions: List[Interaction] = []
        
        # Build nodes
        self._build_nodes()
        
        # Detect interactions if requested
        if auto_detect:
            self.detect_interactions()
    
    def _build_nodes(self):
        """Add cards as nodes with their attributes."""
        for entry in self.deck.cards.values():
            card = entry.card
            
            # Node attributes for visualization
            self.graph.add_node(
                card.id,
                name=card.name,
                type_line=card.type_line,
                card_types=card.get_card_types(),
                cmc=card.cmc,
                colors=card.colors,
                color_identity=card.color_identity,
                keywords=card.keywords,
                quantity=entry.quantity,
                category=entry.category,
                image_uri=card.image_uri,
                is_commander=(card.id == self.deck.commander)
            )
    
    def detect_interactions(self):
        """Detect all interactions between cards."""
        #TODO: Implement Custom MTG ruels and state based interaction detect
s        detector = InteractionDetector()
        cards = self.deck.get_unique_cards()
        
        self.interactions = detector.detect_all(cards)
        
        # Add edges to graph
        for interaction in self.interactions:
            self.add_interaction(interaction)
    
    def add_interaction(self, interaction: Interaction):
        """Add an interaction as an edge."""
        # Add edge with attributes
        if self.graph.has_edge(interaction.source_id, interaction.target_id):
            # Edge exists, update attributes
            edge_data = self.graph.edges[interaction.source_id, interaction.target_id]
            types = edge_data.get("interaction_types", [])
            types.append(interaction.interaction_type.value)
            edge_data["interaction_types"] = types
            edge_data["weight"] = max(edge_data.get("weight", 0), interaction.weight)
        else:
            # New edge
            self.graph.add_edge(
                interaction.source_id,
                interaction.target_id,
                interaction_types=[interaction.interaction_type.value],
                weight=interaction.weight,
                description=interaction.description
            )
    
    def remove_interaction(self, source_id: str, target_id: str):
        """Remove an interaction edge."""
        if self.graph.has_edge(source_id, target_id):
            self.graph.remove_edge(source_id, target_id)
    
    def add_custom_interaction(
        self,
        source_id: str,
        target_id: str,
        interaction_type: InteractionType,
        weight: float = 1.0,
        description: str = None
    ) -> Interaction:
        """Add a custom user-defined interaction."""
        interaction = Interaction(
            source_id=source_id,
            target_id=target_id,
            interaction_type=interaction_type,
            weight=weight,
            description=description
        )
        
        self.interactions.append(interaction)
        self.add_interaction(interaction)
        
        return interaction
    
    # =========================================================================
    # Query methods
    # =========================================================================
    
    def get_connected_cards(self, card_id: str) -> List[str]:
        """Get IDs of all cards connected to a given card."""
        if card_id not in self.graph:
            return []
        return list(self.graph.neighbors(card_id))
    
    def get_interaction_types(self, card_id: str) -> Set[str]:
        """Get all interaction types a card participates in."""
        types = set()
        for _, _, data in self.graph.edges(card_id, data=True):
            types.update(data.get("interaction_types", []))
        return types
    
    def get_cards_by_interaction_type(
        self, 
        interaction_type: InteractionType
    ) -> List[Tuple[str, str]]:
        """Get all card pairs with a specific interaction type."""
        pairs = []
        for source, target, data in self.graph.edges(data=True):
            if interaction_type.value in data.get("interaction_types", []):
                pairs.append((source, target))
        return pairs
    
    def get_isolated_cards(self) -> List[str]:
        """Get cards with no interactions."""
        return [
            node for node in self.graph.nodes()
            if self.graph.degree(node) == 0
        ]
    
    def get_most_connected_cards(self, top_n: int = 10) -> List[Tuple[str, int]]:
        """Get the most connected cards."""
        degrees = sorted(
            self.graph.degree(),
            key=lambda x: x[1],
            reverse=True
        )
        return degrees[:top_n]
    
    # =========================================================================
    # Export methods
    # =========================================================================
    
    def to_cytoscape_format(self) -> Dict:
        """
        Convert graph to Cytoscape.js format.
        
        Returns:
            Dictionary with 'nodes' and 'edges' arrays
        """
        nodes = []
        edges = []
        
        # Build nodes
        for node_id, data in self.graph.nodes(data=True):
            # Determine node color based on card types
            node_color = self._get_type_color(data.get("card_types", []))
            
            nodes.append({
                "data": {
                    "id": node_id,
                    "label": data.get("name", "Unknown"),
                    "type_line": data.get("type_line", ""),
                    "card_types": data.get("card_types", []),
                    "cmc": data.get("cmc", 0),
                    "colors": data.get("colors", []),
                    "quantity": data.get("quantity", 1),
                    "category": data.get("category", ""),
                    "image": data.get("image_uri", ""),
                    "is_commander": data.get("is_commander", False),
                    "color": node_color,
                    "size": 30 + (self.graph.degree(node_id) * 5)
                }
            })
        
        # Build edges
        for source, target, data in self.graph.edges(data=True):
            interaction_types = data.get("interaction_types", [])
            primary_type = interaction_types[0] if interaction_types else "synergy"
            
            edges.append({
                "data": {
                    "id": f"{source}-{target}",
                    "source": source,
                    "target": target,
                    "interaction_types": interaction_types,
                    "weight": data.get("weight", 1.0),
                    "description": data.get("description", ""),
                    "color": INTERACTION_COLORS.get(
                        InteractionType(primary_type), 
                        "#888888"
                    ),
                    "label": INTERACTION_LABELS.get(
                        InteractionType(primary_type),
                        primary_type
                    )
                }
            })
        
        return {
            "nodes": nodes,
            "edges": edges,
            "stats": {
                "total_nodes": len(nodes),
                "total_edges": len(edges),
                "density": nx.density(self.graph) if len(nodes) > 1 else 0,
                "connected_components": nx.number_connected_components(self.graph)
            }
        }
    
    def _get_type_color(self, card_types: List[str]) -> str:
        """Get color for a card based on its types."""
        type_colors = {
            "Creature": "#4CAF50",      # Green
            "Instant": "#2196F3",       # Blue
            "Sorcery": "#F44336",       # Red
            "Artifact": "#9E9E9E",      # Gray
            "Enchantment": "#9C27B0",   # Purple
            "Planeswalker": "#FF9800",  # Orange
            "Land": "#8D6E63",          # Brown
        }
        
        for card_type in card_types:
            if card_type in type_colors:
                return type_colors[card_type]
        
        return "#607D8B"  # Default blue-gray
    
    def to_networkx(self) -> nx.Graph:
        """Get the underlying NetworkX graph."""
        return self.graph
    
    def to_adjacency_matrix(self) -> Tuple[List[str], List[List[float]]]:
        """
        Get adjacency matrix representation.
        
        Returns:
            Tuple of (node_ids, matrix)
        """
        node_ids = list(self.graph.nodes())
        matrix = nx.to_numpy_array(self.graph, weight="weight").tolist()
        return node_ids, matrix

"""Interactive graph visualization using Pyvis."""
from typing import List, Dict, Any
from pathlib import Path
import networkx as nx
from pyvis.network import Network
import logging

from core.models.deck import Deck
from core.graph.deck_graph import DeckGraph
from core.graph.synergy_weighter import SynergyWeighter

class GraphVisualizer:
    """
    Generates interactive HTML visualizations of deck graphs.
    Features:
    - Directional edges
    - Edge bundling (aggregation by Synergy Score)
    - Card art nodes
    """
    
    def __init__(self, output_dir: Path = None):
        self.output_dir = output_dir or Path("app/static/graphs")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
        
    def generate_visualization(self, deck_graph: DeckGraph, filename: str = None) -> str:
        """
        Generate HTML graph for a deck.
        Returns the absolute path to the generated HTML file.
        """
        if not filename:
            filename = f"{deck_graph.deck.id}.html"
            
        output_path = self.output_dir / filename
        
        # Initialize Pyvis network
        # height="800px", width="100%", bgcolor="#222222", font_color="white"
        net = Network(height="800px", width="100%", bgcolor="#1a1a1a", font_color="white", directed=True)
        
        # Configure physics for organic layout
        net.force_atlas_2based()
        net.set_options("""
        var options = {
          "physics": {
            "forceAtlas2Based": {
              "gravitationalConstant": -50,
              "springLength": 100,
              "springConstant": 0.08
            },
            "minVelocity": 0.75,
            "solver": "forceAtlas2Based"
          }
        }
        """)
        
        # Add nodes
        self._add_nodes(net, deck_graph)
        
        # Add bundled edges
        self._add_bundled_edges(net, deck_graph)
        
        # Save
        # Pyvis write_html might need string path
        net.save_graph(str(output_path))
        
        return str(output_path)
        
    def _add_nodes(self, net: Network, deck_graph: DeckGraph):
        """Add nodes with card art and details."""
        for node_id, data in deck_graph.graph.nodes(data=True):
            card = data.get("card")
            if not card:
                continue
                
            # Node styling
            # shape='circularImage' requires an 'image' attribute
            image_url = card.image_uri if card.image_uri else "https://c2.scryfall.com/file/scryfall-errors/missing.jpg"
            
            # Tooltip content
            title = f"<b>{card.name}</b><br>{card.type_line}<br>CMC: {card.cmc}<br><br>{card.oracle_text}"
            
            net.add_node(
                node_id,
                label=card.name,
                title=title,
                shape="circularImage",
                image=image_url,
                borderWidth=2,
                borderWidthSelected=4,
                color={"border": "#4a9eff", "background": "#444444"},
                size=25
            )
            
    def _add_bundled_edges(self, net: Network, deck_graph: DeckGraph):
        """
        Aggregate multiple edges between two nodes into a single weighted edge.
        Bundling Logic:
        - Group all edges between A -> B
        - Calculate Synergy Score S(A,B) using SynergyWeighter
        - Create one edge with thickness = score
        - Tooltip lists all individual interaction types
        """
        # Create a map of (source, target) -> List[interactions]
        # NetworkX multigraph allows multiple edges. We need to iterate them appropriately.
        
        bundled_edges = {}  # (u, v) -> {score: float, descriptions: List[str]}
        weighter = SynergyWeighter()
        
        # Iterate over all edges in the MultiDiGraph
        for u, v, data in deck_graph.graph.edges(data=True):
            key = (u, v)
            
            # Get interaction info
            interaction_type = data.get("interaction_type", "Synergy")
            description = data.get("description", "")
            
            if key not in bundled_edges:
                bundled_edges[key] = {
                    "score": 0.0,
                    "interactions": [],
                    "tags": set()
                }
                
            # Accumulate data
            # Determine tags/weight for this specific interaction instance
            # For simplicity, we assign a base category weight if available, 
            # OR we rely on the weighter to calculate fresh from cards if we had the cards.
            # But deck_graph edges should already have some data.
            # Let's assume we want to re-calculate score using Weighter logic:
            
            u_node = deck_graph.graph.nodes[u]
            v_node = deck_graph.graph.nodes[v]
            card_u = u_node.get("card")
            card_v = v_node.get("card")
            
            if card_u and card_v:
                # Extract tags from the description or interaction type
                tags = [interaction_type]  # Simple tag for now
                if description:
                    # Maybe extract more tags from description using simple splitting or NLP?
                    pass
                
                # Calculate Score Component for this interaction
                # S += Ti * alpha
                # We reuse the Weighter to calculate component score
                component_score = weighter.calculate_synergy_score(card_u, card_v, tags)
                
                bundled_edges[key]["score"] += component_score
                bundled_edges[key]["interactions"].append(f"• {interaction_type}: {description}")
                bundled_edges[key]["tags"].add(interaction_type)
        
        # Add the final bundled edges to Pyvis
        for (u, v), data in bundled_edges.items():
            score = data["score"]
            interactions_list = "<br>".join(data["interactions"])
            tooltip = f"<b>Synergy Score: {score:.1f}</b><br><br>{interactions_list}"
            
            # Visual properties
            # Thickness capped/scaled
            width = max(1, min(10, score))
            
            # Color gradient based on score (Blue low -> Red high)
            # Simple threshold for now
            color = "#4a9eff"  # Blue
            if score > 5:
                color = "#ff4a4a"  # Red
            elif score > 3:
                color = "#d64aff"  # Purple
                
            net.add_edge(
                u, 
                v, 
                width=width,
                title=tooltip,
                color={"color": color, "opacity": 0.8},
                arrows="to"
            )

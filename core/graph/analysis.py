"""Graph analysis algorithms for deck analysis."""
from typing import Dict, List, Tuple, Any
import networkx as nx

from core.graph.deck_graph import DeckGraph
from core.models.interaction import InteractionType


class GraphAnalyzer:
    """
    Provides graph analysis algorithms for deck analysis.
    
    Uses NetworkX algorithms to compute metrics like centrality,
    clustering, and community detection.
    """
    
    def __init__(self, deck_graph: DeckGraph):
        self.deck_graph = deck_graph
        self.graph = deck_graph.graph
    
    # =========================================================================
    # Centrality measures
    # =========================================================================
    
    def degree_centrality(self) -> Dict[str, float]:
        """
        Calculate degree centrality for each card.
        
        Higher values = more connections = potentially more important.
        
        Returns:
            Dictionary of {card_id: centrality_score}
        """
        return nx.degree_centrality(self.graph)
    
    def betweenness_centrality(self) -> Dict[str, float]:
        """
        Calculate betweenness centrality for each card.
        
        Higher values = acts as a bridge between other cards.
        These are key cards that connect different parts of your deck.
        
        Returns:
            Dictionary of {card_id: centrality_score}
        """
        if len(self.graph.nodes()) < 2:
            return {}
        return nx.betweenness_centrality(self.graph, weight="weight")
    
    def closeness_centrality(self) -> Dict[str, float]:
        """
        Calculate closeness centrality for each card.
        
        Higher values = can reach other cards quickly.
        
        Returns:
            Dictionary of {card_id: centrality_score}
        """
        if len(self.graph.nodes()) < 2:
            return {}
        return nx.closeness_centrality(self.graph)
    
    def eigenvector_centrality(self) -> Dict[str, float]:
        """
        Calculate eigenvector centrality for each card.
        
        Similar to PageRank - cards connected to important cards
        are themselves important.
        
        Returns:
            Dictionary of {card_id: centrality_score}
        """
        if len(self.graph.nodes()) < 2:
            return {}
        try:
            return nx.eigenvector_centrality(self.graph, max_iter=500)
        except nx.PowerIterationFailedConvergence:
            return {}
    
    def pagerank(self) -> Dict[str, float]:
        """
        Calculate PageRank for each card.
        
        Cards that are referenced by important cards rank higher.
        
        Returns:
            Dictionary of {card_id: pagerank_score}
        """
        if len(self.graph.nodes()) < 2:
            return {}
        
        # Convert to directed graph for PageRank
        directed = self.graph.to_directed()
        return nx.pagerank(directed, weight="weight")
    
    # =========================================================================
    # Clustering and community detection
    # =========================================================================
    
    def clustering_coefficient(self) -> Dict[str, float]:
        """
        Calculate clustering coefficient for each card.
        
        Higher values = cards neighbors also interact with each other
        (tight synergy groups).
        
        Returns:
            Dictionary of {card_id: clustering_score}
        """
        return nx.clustering(self.graph, weight="weight")
    
    def average_clustering(self) -> float:
        """Get the average clustering coefficient for the deck."""
        if len(self.graph.nodes()) < 3:
            return 0.0
        return nx.average_clustering(self.graph, weight="weight")
    
    def connected_components(self) -> List[List[str]]:
        """
        Find connected components (isolated groups of cards).
        
        If there are multiple components, some cards don't interact
        with the rest of the deck.
        
        Returns:
            List of components, each component is a list of card IDs
        """
        return [
            list(component) 
            for component in nx.connected_components(self.graph)
        ]
    
    def detect_communities(self) -> List[List[str]]:
        """
        Detect communities of highly connected cards.
        
        Uses the Louvain algorithm to find natural groupings.
        
        Returns:
            List of communities, each is a list of card IDs
        """
        if len(self.graph.nodes()) < 2:
            return [list(self.graph.nodes())]
        
        try:
            from networkx.algorithms.community import louvain_communities
            communities = louvain_communities(self.graph, weight="weight")
            return [list(c) for c in communities]
        except Exception:
            # Fallback to connected components
            return self.connected_components()
    
    # =========================================================================
    # Synergy analysis
    # =========================================================================
    
    def synergy_score(self) -> float:
        """
        Calculate overall deck synergy score.
        
        Based on edge density and average edge weight.
        
        Returns:
            Score from 0 to 1, higher = more synergistic
        """
        if len(self.graph.nodes()) < 2:
            return 0.0
        
        # Base density
        density = nx.density(self.graph)
        
        # Average edge weight
        weights = [
            d.get("weight", 1.0) 
            for _, _, d in self.graph.edges(data=True)
        ]
        avg_weight = sum(weights) / len(weights) if weights else 0
        
        # Combined score
        return (density * 0.5 + avg_weight * 0.5)
    
    def key_cards(self, top_n: int = 10) -> List[Tuple[str, Dict[str, float]]]:
        """
        Identify the key cards in the deck based on multiple metrics.
        
        Args:
            top_n: Number of top cards to return
            
        Returns:
            List of (card_id, metrics_dict) sorted by importance
        """
        # Calculate all metrics
        degree = self.degree_centrality()
        betweenness = self.betweenness_centrality()
        pagerank_scores = self.pagerank()
        clustering = self.clustering_coefficient()
        
        # Combine into composite score
        scores = {}
        for card_id in self.graph.nodes():
            composite = (
                degree.get(card_id, 0) * 0.3 +
                betweenness.get(card_id, 0) * 0.3 +
                pagerank_scores.get(card_id, 0) * 0.3 +
                clustering.get(card_id, 0) * 0.1
            )
            scores[card_id] = {
                "composite": composite,
                "degree": degree.get(card_id, 0),
                "betweenness": betweenness.get(card_id, 0),
                "pagerank": pagerank_scores.get(card_id, 0),
                "clustering": clustering.get(card_id, 0)
            }
        
        # Sort by composite score
        sorted_cards = sorted(
            scores.items(),
            key=lambda x: x[1]["composite"],
            reverse=True
        )
        
        return sorted_cards[:top_n]
    
    def weak_links(self, threshold: float = 0.3) -> List[str]:
        """
        Find cards with low synergy (potential cut candidates).
        
        Args:
            threshold: Degree centrality below this = weak
            
        Returns:
            List of card IDs with low connectivity
        """
        degree = self.degree_centrality()
        return [
            card_id for card_id, cent in degree.items()
            if cent < threshold
        ]
    
    def interaction_type_distribution(self) -> Dict[str, int]:
        """
        Get distribution of interaction types in the deck.
        
        Returns:
            Dictionary of {interaction_type: count}
        """
        distribution = {}
        
        for _, _, data in self.graph.edges(data=True):
            for itype in data.get("interaction_types", []):
                distribution[itype] = distribution.get(itype, 0) + 1
        
        return distribution
    
    # =========================================================================
    # Full analysis
    # =========================================================================
    
    def full_analysis(self) -> Dict[str, Any]:
        """
        Run full analysis and return all metrics.
        
        Returns:
            Dictionary with all analysis results
        """
        return {
            "synergy_score": round(self.synergy_score(), 3),
            "average_clustering": round(self.average_clustering(), 3),
            "num_components": len(self.connected_components()),
            "communities": self.detect_communities(),
            "key_cards": [
                {
                    "card_id": card_id,
                    "name": self.graph.nodes[card_id].get("name", "Unknown"),
                    "metrics": metrics
                }
                for card_id, metrics in self.key_cards(10)
            ],
            "weak_links": [
                {
                    "card_id": card_id,
                    "name": self.graph.nodes[card_id].get("name", "Unknown")
                }
                for card_id in self.weak_links()
            ],
            "interaction_distribution": self.interaction_type_distribution(),
            "centrality": {
                "degree": self.degree_centrality(),
                "betweenness": self.betweenness_centrality(),
                "pagerank": self.pagerank()
            }
        }

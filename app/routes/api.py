"""REST API endpoints."""
from flask import Blueprint, request, jsonify

bp = Blueprint("api", __name__)


# =============================================================================
# Card Search API
# =============================================================================

@bp.route("/cards/search")
def search_cards():
    """Search for cards via Scryfall."""
    from core.services.scryfall import ScryfallClient
    
    query = request.args.get("q", "")
    if not query or len(query) < 2:
        return jsonify({"error": "Query too short", "cards": []}), 400
    
    client = ScryfallClient()
    cards = client.search_cards(query)
    return jsonify({"cards": cards})


@bp.route("/cards/<card_id>")
def get_card(card_id):
    """Get a specific card by ID."""
    from core.services.scryfall import ScryfallClient
    
    client = ScryfallClient()
    card = client.get_card_by_id(card_id)
    if card:
        return jsonify(card)
    return jsonify({"error": "Card not found"}), 404


# =============================================================================
# Deck CRUD API
# =============================================================================

@bp.route("/decks", methods=["GET"])
def list_decks():
    """List all saved decks."""
    from core.services.deck_storage import DeckStorage
    
    storage = DeckStorage()
    decks = storage.list_decks()
    return jsonify({"decks": decks})


@bp.route("/decks", methods=["POST"])
def create_deck():
    """Create a new deck."""
    from core.services.deck_storage import DeckStorage
    from core.models.deck import Deck
    
    data = request.get_json()
    deck = Deck(
        name=data.get("name", "Untitled Deck"),
        format=data.get("format", "commander"),
        commander=data.get("commander")
    )
    
    storage = DeckStorage()
    deck_id = storage.save_deck(deck)
    return jsonify({"id": deck_id, "deck": deck.to_dict()}), 201


@bp.route("/decks/import", methods=["POST"])
def import_deck():
    """Import a deck from text list."""
    from core.services.deck_storage import DeckStorage
    
    data = request.get_json()
    if not data or "text" not in data:
        return jsonify({"error": "Missing deck text"}), 400
        
    text = data.get("text", "")
    name = data.get("name", "Imported Deck")
    
    storage = DeckStorage()
    deck = storage.import_from_text(text, name)
    
    # Save the imported deck
    deck_id = storage.save_deck(deck)
    
    return jsonify({"id": deck_id, "deck": deck.to_dict()}), 201


@bp.route("/decks/<deck_id>", methods=["GET"])
def get_deck(deck_id):
    """Get a specific deck."""
    from core.services.deck_storage import DeckStorage
    
    storage = DeckStorage()
    deck = storage.load_deck(deck_id)
    if deck:
        return jsonify(deck.to_dict())
    return jsonify({"error": "Deck not found"}), 404


@bp.route("/decks/<deck_id>", methods=["PUT"])
def update_deck(deck_id):
    """Update an existing deck."""
    from core.services.deck_storage import DeckStorage
    from core.models.deck import Deck
    
    data = request.get_json()
    storage = DeckStorage()
    
    deck = storage.load_deck(deck_id)
    if not deck:
        return jsonify({"error": "Deck not found"}), 404
    
    # Update deck fields
    deck.name = data.get("name", deck.name)
    deck.format = data.get("format", deck.format)
    deck.commander = data.get("commander", deck.commander)
    if "cards" in data:
        from core.models.deck import DeckEntry
        deck.cards = {
            card_id: DeckEntry.from_dict(entry_data) if isinstance(entry_data, dict) else entry_data
            for card_id, entry_data in data["cards"].items()
        }
    
    storage.save_deck(deck, deck_id)
    return jsonify(deck.to_dict())


@bp.route("/decks/<deck_id>", methods=["DELETE"])
def delete_deck(deck_id):
    """Delete a deck."""
    from core.services.deck_storage import DeckStorage
    
    storage = DeckStorage()
    success = storage.delete_deck(deck_id)
    if success:
        return jsonify({"success": True})
    return jsonify({"error": "Deck not found"}), 404


# =============================================================================
# Graph Analysis API
# =============================================================================

@bp.route("/decks/<deck_id>/graph")
def get_deck_graph(deck_id):
    """Get graph representation of deck interactions."""
    from core.services.deck_storage import DeckStorage
    from core.graph.deck_graph import DeckGraph
    
    storage = DeckStorage()
    deck = storage.load_deck(deck_id)
    if not deck:
        return jsonify({"error": "Deck not found"}), 404
    
    graph = DeckGraph(deck)
    return jsonify(graph.to_cytoscape_format())


@bp.route("/decks/<deck_id>/visualize-html", methods=["POST"])
def generate_deck_visualization(deck_id):
    """Generate Pyvis interactive graph HTML."""
    from core.services.deck_storage import DeckStorage
    from core.graph.deck_graph import DeckGraph
    from core.graph.visualizer import GraphVisualizer
    
    storage = DeckStorage()
    deck = storage.load_deck(deck_id)
    if not deck:
        return jsonify({"error": "Deck not found"}), 404
    
    # Generate graph logic
    deck_graph = DeckGraph(deck)
    deck_graph.detect_interactions()
    
    # Create visualizer and generate HTML
    visualizer = GraphVisualizer()
    # Ensure filename is unique/consistent
    filename = f"{deck_id}.html"
    visualizer.generate_visualization(deck_graph, filename)
    
    # Return URL to the static file
    # Assuming app/static is served at /static
    return jsonify({
        "url": f"/static/graphs/{filename}",
        "path": filename
    })


@bp.route("/decks/<deck_id>/analysis")
def analyze_deck_graph(deck_id):
    """Get graph analysis metrics for a deck."""
    from core.services.deck_storage import DeckStorage
    from core.graph.deck_graph import DeckGraph
    from core.graph.analysis import GraphAnalyzer
    
    storage = DeckStorage()
    deck = storage.load_deck(deck_id)
    if not deck:
        return jsonify({"error": "Deck not found"}), 404
    
    graph = DeckGraph(deck)
    analyzer = GraphAnalyzer(graph)
    return jsonify(analyzer.full_analysis())


# =============================================================================
# Probability API
# =============================================================================

@bp.route("/probability/hypergeometric", methods=["POST"])
def calculate_hypergeometric():
    """Calculate hypergeometric probability."""
    from core.probability.hypergeometric import HypergeometricCalculator
    
    data = request.get_json()
    calc = HypergeometricCalculator(
        deck_size=data.get("deck_size", 99),
        copies=data.get("copies", 1),
        cards_drawn=data.get("cards_drawn", 7)
    )
    
    result = {
        "exactly": calc.exactly(data.get("successes", 1)),
        "at_least": calc.at_least(data.get("successes", 1)),
        "at_most": calc.at_most(data.get("successes", 1)),
        "distribution": calc.full_distribution()
    }
    return jsonify(result)


@bp.route("/probability/multivariate", methods=["POST"])
def calculate_multivariate():
    """Calculate multivariate hypergeometric probability."""
    from core.probability.multivariate import MultivariateCalculator
    
    data = request.get_json()
    calc = MultivariateCalculator(
        deck_size=data.get("deck_size", 99),
        card_counts=data.get("card_counts", []),  # [(copies1), (copies2), ...]
        cards_drawn=data.get("cards_drawn", 7)
    )
    
    result = calc.probability(data.get("successes", []))  # [need1, need2, ...]
    return jsonify({"probability": result})


# =============================================================================
# Monte Carlo API
# =============================================================================

@bp.route("/simulation/run", methods=["POST"])
def run_simulation():
    """Run Monte Carlo simulation."""
    from core.services.deck_storage import DeckStorage
    from core.simulation.monte_carlo import MonteCarloSimulator
    
    data = request.get_json()
    
    storage = DeckStorage()
    deck = storage.load_deck(data.get("deck_id"))
    if not deck:
        return jsonify({"error": "Deck not found"}), 404
    
    simulator = MonteCarloSimulator(deck)
    results = simulator.run(
        iterations=data.get("iterations", 10000),
        criteria=data.get("criteria", {})
    )
    
    return jsonify(results)

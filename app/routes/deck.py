"""Deck management routes."""
from flask import Blueprint, render_template, request, jsonify

bp = Blueprint("deck", __name__)


@bp.route("/")
def deck_list():
    """List all saved decks."""
    return render_template("deck_list.html")


@bp.route("/builder")
@bp.route("/builder/<deck_id>")
def deck_builder(deck_id=None):
    """Visual deck builder page."""
    return render_template("deck_builder.html", deck_id=deck_id)


@bp.route("/view/<deck_id>")
def deck_view(deck_id):
    """Deck visualization page."""
    return render_template("deck_view.html", deck_id=deck_id)


@bp.route("/graph/<deck_id>")
def graph_view(deck_id):
    """Card interaction graph visualization."""
    return render_template("graph_view.html", deck_id=deck_id)

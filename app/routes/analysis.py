"""Probability analysis routes."""
from flask import Blueprint, render_template

bp = Blueprint("analysis", __name__)


@bp.route("/")
@bp.route("/<deck_id>")
def probability_analysis(deck_id=None):
    """Probability analysis page."""
    return render_template("probability.html", deck_id=deck_id)

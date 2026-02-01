"""Monte Carlo simulation routes."""
from flask import Blueprint, render_template

bp = Blueprint("simulation", __name__)


@bp.route("/")
@bp.route("/<deck_id>")
def monte_carlo(deck_id=None):
    """Monte Carlo simulation page."""
    return render_template("simulation.html", deck_id=deck_id)

"""
Unit tests for Streamlit UI helper functions and color mapping.
"""

from src.ui.components import get_tier_color, render_score_badge, TIER_COLORS
from app import PUNE_SCENARIOS


def test_tier_color_mapping():
    """Verify tier color codes are mapped accurately."""
    assert get_tier_color("Exceptional Match") == "#10B981"
    assert get_tier_color("Strong Match") == "#3B82F6"
    assert get_tier_color("Moderate Match") == "#F59E0B"
    assert get_tier_color("Low / Marginal Match") == "#EF4444"
    assert get_tier_color("Unknown Tier") == "#6B7280"


def test_render_score_badge():
    """Verify HTML score badge string formatting."""
    badge_html = render_score_badge(85.5, "Exceptional Match")
    assert "85.5/100" in badge_html
    assert "Exceptional Match" in badge_html
    assert "#10B981" in badge_html


def test_pune_scenarios_presence():
    """Verify standard pre-configured Pune scenarios exist in app dictionary."""
    assert any("Kothrud" in k for k in PUNE_SCENARIOS.keys())
    assert any("Baner" in k for k in PUNE_SCENARIOS.keys())
    assert any("Hinjawadi" in k for k in PUNE_SCENARIOS.keys())

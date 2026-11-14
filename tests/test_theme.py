"""Theme colours come from the Øberg website and meet WCAG 2.2 AA contrast (issue #2)."""

import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
THEME = tomllib.loads((ROOT / ".streamlit" / "config.toml").read_text())["theme"]
CSS = (ROOT / "assets" / "style.css").read_text(encoding="utf-8")


def luminance(hex_colour: str) -> float:
    rgb = [int(hex_colour.lstrip("#")[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def contrast(a: str, b: str) -> float:
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def test_theme_configuration():
    assert THEME == {
        "base": "dark", "primaryColor": "#5aa9ff", "backgroundColor": "#0a1120",
        "secondaryBackgroundColor": "#151d2e", "textColor": "#e8eef7", "linkColor": "#8fc8ff",
        "borderColor": "#26324a", "baseRadius": "10px", "font": "sans-serif",
    }


def test_css_tokens_match_verified_palette():
    for token, value in {"--bg": "#0a1120", "--surface": "#151d2e", "--border": "#26324a", "--accent": "#5aa9ff",
                         "--accent-2": "#8fc8ff", "--accent-deep": "#2f6fd0", "--text": "#e8eef7",
                         "--text-muted": "#9fb0c8", "--on-accent": "#001226", "--radius": "18px"}.items():
        assert f"{token}: {value}" in CSS, token


def test_contrast_meets_wcag_aa():
    assert contrast(THEME["textColor"], THEME["backgroundColor"]) >= 4.5
    assert contrast(THEME["textColor"], THEME["secondaryBackgroundColor"]) >= 4.5
    assert contrast("#9fb0c8", THEME["backgroundColor"]) >= 4.5  # muted text
    assert contrast("#9fb0c8", "#1b2539") >= 4.5  # disabled button label
    assert contrast(THEME["primaryColor"], THEME["backgroundColor"]) >= 3.0  # focus ring / components
    assert contrast("#001226", THEME["primaryColor"]) >= 4.5  # text on primary buttons
    assert contrast("#001226", "#8fc8ff") >= 4.5  # text on hovered primary buttons


def test_css_avoids_generated_class_names_and_respects_reduced_motion():
    assert "prefers-reduced-motion" in CSS
    assert not re.search(r"\.(st-emotion-cache|css-)[\w-]+", CSS)

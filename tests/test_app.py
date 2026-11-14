"""The Streamlit page with a fake Claude client – no live API calls (issues #3, #6, #7, #9)."""

from pathlib import Path
from types import SimpleNamespace

import anthropic
try:  # newer Anthropic SDKs use httpx2, older ones httpx
    import httpx2 as httpx
except ImportError:  # pragma: no cover
    import httpx
import pytest
from streamlit.testing.v1 import AppTest

import uat.ai
from uat.ai import ClaudeClient, UATIdeasResponse
from uat.ui import copy_html, esc

from .conftest import FakeMessages, ideas_response

ROOT = Path(__file__).resolve().parent.parent
REQ = "The employee must be able to change a holiday request before it is approved."


@pytest.fixture
def env(tmp_path, monkeypatch):
    monkeypatch.chdir(ROOT)
    monkeypatch.setenv("UAT_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-not-real")
    monkeypatch.setenv("ANTHROPIC_MODEL", "test-model")
    return tmp_path


@pytest.fixture
def claude(env, monkeypatch):
    """Replace the real client factory; returns the fake's message log so tests can count API calls."""
    state = {"responses": [], "calls": []}

    def factory(settings):  # uses the app's real settings (quota, limits), only the transport is fake
        messages = FakeMessages(state["responses"])
        messages.responses = state["responses"]  # share remaining responses across clients
        messages.calls = state["calls"]
        return ClaudeClient(settings, client=SimpleNamespace(messages=messages))

    monkeypatch.setattr(uat.ai, "make_client", factory)
    return state


def run(lang=None):
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30)
    if lang:
        at.session_state["lang"] = lang
    at.run()
    return at


def texts(at):
    return " ".join(m.value for m in at.markdown) + " " + " ".join(c.value for c in at.caption)


def generate(at, requirement=REQ, key="generate"):
    if requirement is not None:
        at.text_area(key="requirement").input(requirement)
    at.button(key=key).click().run()
    return at


# ---------------------------------------------------------------- rendering and language

def test_english_is_default(claude):
    at = run()
    assert not at.exception
    assert at.text_area(key="requirement").label == "Enter your requirement"
    assert at.button(key="generate").label == "Generate Test Ideas"
    assert at.session_state["lang"] == "en"


def test_danish_interface(claude):
    at = run("da")
    assert at.text_area(key="requirement").label == "Indsæt dit krav"
    assert at.button(key="generate").label == "Generér testidéer"
    assert at.button(key="clear").label == "Ryd / Nyt krav"


def test_language_controls_ai_output(claude):
    at = generate(run("da"))
    assert "in Danish" in claude["calls"][0]["messages"][0]["content"]


def test_missing_configuration_shows_message_and_disables_generate(env, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY")
    monkeypatch.delenv("ANTHROPIC_MODEL")
    at = run()
    assert not at.exception
    warnings = " ".join(w.value for w in at.warning)
    assert "ANTHROPIC_API_KEY" in warnings and "ANTHROPIC_MODEL" in warnings
    assert at.button(key="generate").disabled


# ---------------------------------------------------------------- generation

def test_empty_requirement_is_rejected_without_api_call(claude):
    at = generate(run(), requirement="   ")
    assert claude["calls"] == []
    assert any("Please enter a requirement" in w.value for w in at.warning)


def test_too_long_requirement_is_rejected_without_api_call(claude, monkeypatch):
    monkeypatch.setenv("UAT_MAX_INPUT_CHARS", "100")
    at = generate(run(), requirement="x" * 150)
    assert claude["calls"] == []
    assert any("too long" in w.value for w in at.warning)


def test_generate_shows_numbered_ideas_and_note(claude):
    claude["responses"].append(UATIdeasResponse(ideas=["Verify A.", "Verify B.", "verify a"], note="Who approves?"))
    at = generate(run())
    assert not at.exception and len(claude["calls"]) == 1
    page = texts(at)
    assert "Generated UAT Test Ideas" in page
    assert "**1.** Verify A" in page and "**2.** Verify B" in page and "**3.**" not in page
    assert any("Who approves" in i.value for i in at.info)
    assert at.session_state["ideas"] == ["Verify A.", "Verify B."]


def test_reruns_do_not_call_the_api_again(claude):
    at = generate(run())
    at.run()
    at.run()
    assert len(claude["calls"]) == 1
    assert at.session_state["pending"] is None


def test_regenerate_calls_again_for_same_requirement(claude):
    claude["responses"] += [ideas_response(3), ideas_response(6)]
    at = generate(run())
    assert len(at.session_state["ideas"]) == 3
    generate(at, requirement=None, key="regenerate")
    assert len(claude["calls"]) == 2 and len(at.session_state["ideas"]) == 6
    assert REQ in claude["calls"][1]["messages"][0]["content"]


def test_clear_resets_everything_but_language(claude):
    claude["responses"].append(ideas_response(4, note="x"))
    at = generate(run("da"))
    at.button(key="clear").click().run()
    assert at.session_state["requirement"] == ""
    assert at.session_state["ideas"] == [] and at.session_state["note"] is None
    assert at.session_state["error"] is None and at.session_state["lang"] == "da"
    assert "Genererede UAT-testidéer" not in texts(at)


def test_api_error_is_friendly_and_keeps_requirement(claude):
    request = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
    claude["responses"].append(anthropic.APITimeoutError(request=request))
    at = generate(run())
    assert not at.exception
    assert any("did not answer in time" in e.value for e in at.error)
    assert at.text_area(key="requirement").value == REQ


def test_unexpected_error_shows_no_trace(claude):
    claude["responses"].append(RuntimeError("secret internals"))
    at = generate(run())
    assert not at.exception
    messages = " ".join(e.value for e in at.error)
    assert "unexpected" in messages and "secret internals" not in messages


def test_quota_exceeded_message(claude, monkeypatch):
    monkeypatch.setenv("UAT_MAX_CALLS_PER_DAY", "1")
    at = generate(run())
    generate(at, requirement=None)
    assert len(claude["calls"]) == 1
    assert any("limit of 1 Claude calls" in e.value for e in at.error)


# ---------------------------------------------------------------- safe rendering and clipboard

def test_ai_text_is_rendered_literally():
    assert esc("<img src=x onerror=alert(1)> [link](http://x)") == \
        "\\<img src=x onerror=alert\\(1\\)\\> \\[link\\]\\(http://x\\)"


def test_copy_component_never_embeds_text_as_html():
    idea = 'Verify "quotes" & </script><script>alert(1)</script> __LABEL__'
    html = copy_html(idea, "Copy", "Copied", "Failed", "Copy idea 1")
    assert "</script><script>alert" not in html
    assert html.count("</script>") == 1  # only the component's own closing tag
    assert "\\u003c/script\\u003e" in html and "__LABEL__" in html  # placeholder-like text left as data
    assert "navigator.clipboard.writeText(TEXT)" in html and 'execCommand("copy")' in html

"""Øberg UAT Test Ideas – one requirement, one button, useful UAT test ideas.

Single Streamlit page. The Claude call runs server-side (uat/ai.py); the browser only receives rendered UI.
"""

from __future__ import annotations

import logging
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from uat import ai  # noqa: E402  (after load_dotenv)
from uat.config import load_settings  # noqa: E402
from uat.i18n import DEFAULT_LANGUAGE, LANGUAGES, error_text, t  # noqa: E402
from uat.ui import copy_html, esc  # noqa: E402

ROOT = Path(__file__).parent
log = logging.getLogger("uat.app")

st.set_page_config(page_title="Øberg UAT Test Ideas", page_icon=str(ROOT / "assets" / "favicon.png"), layout="centered")
st.html(f"<style>{(ROOT / 'assets' / 'style.css').read_text(encoding='utf-8')}</style>")

# ---------------------------------------------------------------- session state (no database, no history)
STATE = {"lang": DEFAULT_LANGUAGE, "requirement": "", "ideas": [], "note": None, "error": None, "pending": None}
for key, default in STATE.items():
    if key not in st.session_state:
        st.session_state[key] = list(default) if isinstance(default, list) else default


def lang() -> str:
    return st.session_state.get("lang") or DEFAULT_LANGUAGE


def request_generation() -> None:
    """Button callback: mark one generation as pending. The call itself runs once, at the end of this run."""
    if st.session_state.pending is None:
        st.session_state.pending = "generate"
        st.session_state.error = None


def clear_all() -> None:
    """Clear / New requirement: everything except the selected language."""
    st.session_state.requirement = ""
    st.session_state.ideas = []
    st.session_state.note = None
    st.session_state.error = None
    st.session_state.pending = None


def copy_button(text: str, aria: str, label_key: str = "copy") -> None:
    html = copy_html(text, t(label_key, lang()), t("copied", lang()), t("copy_failed", lang()), aria)
    if hasattr(st, "iframe"):
        st.iframe(html, height=40)
    else:  # pragma: no cover – older Streamlit
        import streamlit.components.v1 as components

        components.html(html, height=40)


try:
    settings = load_settings()
    settings_error = None
except ValueError as e:  # invalid optional number setting – message names the variable, never a secret
    settings, settings_error = None, str(e)

busy = st.session_state.pending is not None

# ---------------------------------------------------------------- header
st.html(
    '<div class="uat-header"><span class="uat-mark" aria-hidden="true">Ø</span><div>'
    f'<h1>{t("title", lang())}</h1><p>{t("subtitle", lang())}</p>'
    f'<p class="uat-tagline">{t("tagline", lang())}</p></div></div>'
)

# ---------------------------------------------------------------- language + requirement
st.segmented_control(
    t("language", lang()), options=list(LANGUAGES), format_func=LANGUAGES.get, key="lang", required=True,
)

limit = settings.max_input_chars if settings else 4000
# Note: input widgets are never disabled while busy – changing `disabled` would reset their value in Streamlit.
# Duplicate calls are prevented by the `pending` flag and the disabled action buttons instead.
st.text_area(
    t("requirement_label", lang()), key="requirement", height=150,
    placeholder=t("requirement_placeholder", lang()),
)
st.caption(t("char_count", lang(), n=len((st.session_state.requirement or "").strip()), limit=limit))

if settings_error:
    st.error(settings_error)
elif not settings.ai_ready:
    for code in settings.problems():
        st.warning(error_text(code, lang()))

# ---------------------------------------------------------------- actions
ai_ready = bool(settings and settings.ai_ready)
with st.container(horizontal=True, key="actions"):
    st.button(t("generate", lang()), type="primary", key="generate", on_click=request_generation,
              disabled=busy or not ai_ready)
    if st.session_state.ideas:
        st.button(t("regenerate", lang()), key="regenerate", on_click=request_generation,
                  disabled=busy or not ai_ready)
    st.button(t("clear", lang()), key="clear", on_click=clear_all, disabled=busy)

status = st.empty()

if st.session_state.error:
    code, params = st.session_state.error
    (st.warning if code in ("empty", "too_long") else st.error)(error_text(code, lang(), **params))

# ---------------------------------------------------------------- results
ideas: list[str] = st.session_state.ideas
if ideas:
    st.markdown(f"### {t('results_title', lang())}")
    if st.session_state.note:
        st.info(f"**{t('note_label', lang())}:** {esc(st.session_state.note)}")
    for number, idea in enumerate(ideas, start=1):
        with st.container(border=True, key=f"idea_{number}"):
            text_col, copy_col = st.columns([5, 1.5], vertical_alignment="center")
            text_col.markdown(f"**{number}.** {esc(idea)}")
            with copy_col:
                copy_button(idea, t("copy_idea_aria", lang(), n=number))
    copy_button(ai.clipboard_text(ideas), t("copy_all", lang()), label_key="copy_all")

if ai_ready:
    remaining = ai.UsageTracker(settings.data_dir, settings.max_calls_per_day).remaining()
    st.caption(t("calls_left", lang(), n=remaining))
st.caption(t("privacy_note", lang()))

# ---------------------------------------------------------------- the single Claude call for this click
if busy:
    try:
        with status.container(), st.spinner(t("generating", lang())):
            text = ai.validate_requirement(st.session_state.requirement, limit)
            generation = ai.make_client(settings).generate(text, lang())
        st.session_state.ideas = generation.result.ideas
        st.session_state.note = generation.result.note
    except ai.AIError as e:
        st.session_state.error = (e.code, e.params)  # requirement and previous ideas are kept
    except Exception as e:  # never show stack traces, secrets or requirement text
        log.error("Unexpected error during generation: %s", type(e).__name__)
        st.session_state.error = ("unexpected", {})
    finally:
        st.session_state.pending = None
    st.rerun()

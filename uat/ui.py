"""Presentation helpers: safe text rendering and a small, isolated clipboard component."""

from __future__ import annotations

import json
import re

_MD_SPECIAL = "\\`*_{}[]<>()#+-.!|~$"


def esc(text: str) -> str:
    """Escape Markdown so user or AI text is shown literally (no links, images, HTML or formatting).

    Same approach as Øberg TestLab (views/common.py)."""
    return "".join("\\" + c if c in _MD_SPECIAL else c for c in str(text)).replace("\n", "  \n")


def _js(value: str) -> str:
    """A JavaScript string literal that cannot break out of <script>: <, >, & and line separators are escaped."""
    return (
        json.dumps(value, ensure_ascii=False)
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
        .replace(" ", "\\u2028")
        .replace(" ", "\\u2029")
    )


_COPY_TEMPLATE = """<!doctype html>
<html><head><meta charset="utf-8"><style>
  html, body { margin: 0; padding: 0; background: transparent; overflow: hidden; }
  body { display: flex; justify-content: flex-end; align-items: center; height: 100%;
         font-family: system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; }
  button { display: inline-flex; align-items: center; gap: 6px; cursor: pointer; white-space: nowrap;
           padding: 6px 14px; border-radius: 999px; font: 600 0.85rem/1.2 inherit;
           color: #e8eef7; background: rgba(255,255,255,0.02); border: 1px solid #26324a;
           transition: border-color .2s, color .2s; }
  button:hover { border-color: #5aa9ff; color: #fff; }
  button:focus-visible { outline: 2px solid #5aa9ff; outline-offset: 3px; }
  button.done { border-color: #55d48a; color: #55d48a; }
  svg { width: 14px; height: 14px; fill: none; stroke: currentColor; stroke-width: 2; }
  @media (prefers-reduced-motion: reduce) { button { transition: none; } }
</style></head><body>
<button type="button" id="b"><svg viewBox="0 0 24 24" aria-hidden="true"><rect x="9" y="9" width="11" height="11" rx="2"/>
<path d="M5 15V5a2 2 0 0 1 2-2h8"/></svg><span id="l"></span></button>
<script>
  const TEXT = __TEXT__, LABEL = __LABEL__, DONE = __DONE__, FAIL = __FAIL__, ARIA = __ARIA__;
  const b = document.getElementById("b"), l = document.getElementById("l");
  l.textContent = LABEL; b.setAttribute("aria-label", ARIA);
  function show(ok) {
    l.textContent = ok ? DONE + " \\u2713" : FAIL; b.classList.toggle("done", ok);
    setTimeout(() => { l.textContent = LABEL; b.classList.remove("done"); }, 1800);
  }
  function fallback() {
    const ta = document.createElement("textarea");
    ta.value = TEXT; ta.setAttribute("readonly", ""); ta.style.position = "fixed"; ta.style.opacity = "0";
    document.body.appendChild(ta); ta.select();
    let ok = false; try { ok = document.execCommand("copy"); } catch (e) { ok = false; }
    document.body.removeChild(ta); return ok;
  }
  b.addEventListener("click", async () => {
    try { await navigator.clipboard.writeText(TEXT); show(true); }
    catch (e) { show(fallback()); }
  });
</script></body></html>"""


def copy_html(text: str, label: str, done: str, fail: str, aria: str) -> str:
    """HTML for one copy button. Text is passed only as an escaped JS string and set via textContent/clipboard –
    it is never interpreted as HTML."""
    values = {"TEXT": text, "LABEL": label, "DONE": done, "FAIL": fail, "ARIA": aria}
    # One pass, so placeholder-like text inside the idea is never substituted again.
    return re.sub(r"__(TEXT|LABEL|DONE|FAIL|ARIA)__", lambda m: _js(values[m.group(1)]), _COPY_TEMPLATE)

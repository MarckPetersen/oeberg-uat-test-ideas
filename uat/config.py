"""Settings from environment variables (incl. Codespaces secrets), a local .env, then Streamlit secrets.

Pattern taken from Øberg TestLab (testlab/config.py). No Claude model identifier is hardcoded:
AI generation stays disabled with a clear message until ANTHROPIC_MODEL is set.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any


def secret(name: str) -> Any:
    """Read a setting without ever exposing it. Environment first, then Streamlit secrets."""
    value = os.environ.get(name)
    if value not in (None, ""):
        return value
    try:  # Streamlit secrets, only when running inside Streamlit with a secrets file
        import streamlit as st

        if name in st.secrets:
            return st.secrets[name]
    except Exception:  # no secrets file / not running in Streamlit
        pass
    return None


def _int(name: str, default: int, minimum: int = 1) -> int:
    raw = secret(name)
    if raw is None:
        return default
    try:
        value = int(raw)
    except (TypeError, ValueError):
        raise ValueError(f"{name} must be a whole number, got {raw!r}") from None
    if value < minimum:
        raise ValueError(f"{name} must be at least {minimum}, got {value}")
    return value


@dataclass(frozen=True)
class Settings:
    has_api_key: bool
    model: str | None
    data_dir: str
    max_calls_per_day: int
    max_input_chars: int
    max_output_tokens: int

    @property
    def ai_ready(self) -> bool:
        return self.has_api_key and bool(self.model)

    def problems(self) -> list[str]:
        """Error codes (see i18n) for missing configuration – never values."""
        codes = []
        if not self.has_api_key:
            codes.append("no_key")
        if not self.model:
            codes.append("no_model")
        return codes

    def __repr__(self) -> str:  # never show secrets
        return f"Settings(ai_ready={self.ai_ready}, model={self.model!r}, data_dir={self.data_dir!r})"


def load_settings() -> Settings:
    model = secret("ANTHROPIC_MODEL")
    return Settings(
        has_api_key=bool(secret("ANTHROPIC_API_KEY")),
        model=(str(model).strip() or None) if model else None,
        data_dir=str(secret("UAT_DATA_DIR") or ".uat"),
        max_calls_per_day=_int("UAT_MAX_CALLS_PER_DAY", 30),
        max_input_chars=_int("UAT_MAX_INPUT_CHARS", 4000, minimum=100),
        max_output_tokens=_int("UAT_MAX_OUTPUT_TOKENS", 2000, minimum=500),
    )


def config_check() -> str:
    """Report whether the secrets are present – names only, never values. Run: python -m uat.config"""
    lines = []
    for name in ("ANTHROPIC_API_KEY", "ANTHROPIC_MODEL"):
        lines.append(f"{name}: {'set' if secret(name) else 'MISSING'}")
    return "\n".join(lines)


if __name__ == "__main__":  # pragma: no cover
    from dotenv import load_dotenv

    load_dotenv()
    print(config_check())

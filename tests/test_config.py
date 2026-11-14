"""Settings, secrets and the Codespaces dev container (issues #1, #8)."""

import json
import re
from pathlib import Path

import pytest

from uat.config import config_check, load_settings

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for name in ("ANTHROPIC_API_KEY", "ANTHROPIC_MODEL", "UAT_MAX_CALLS_PER_DAY", "UAT_MAX_INPUT_CHARS",
                 "UAT_MAX_OUTPUT_TOKENS", "UAT_DATA_DIR"):
        monkeypatch.delenv(name, raising=False)


def test_defaults_without_configuration():
    s = load_settings()
    assert not s.ai_ready and s.problems() == ["no_key", "no_model"]
    assert s.max_calls_per_day == 30 and s.data_dir == ".uat"


def test_settings_from_environment_and_no_secret_in_repr(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-secret-value")
    monkeypatch.setenv("ANTHROPIC_MODEL", " some-model ")
    monkeypatch.setenv("UAT_MAX_CALLS_PER_DAY", "5")
    s = load_settings()
    assert s.ai_ready and s.model == "some-model" and s.max_calls_per_day == 5
    assert "sk-secret" not in repr(s) and "sk-secret" not in str(s)


def test_config_check_shows_names_not_values(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-secret-value")
    report = config_check()
    assert "ANTHROPIC_API_KEY: set" in report and "ANTHROPIC_MODEL: MISSING" in report
    assert "sk-secret" not in report


@pytest.mark.parametrize("value", ["abc", "0"])
def test_invalid_numbers_rejected(monkeypatch, value):
    monkeypatch.setenv("UAT_MAX_CALLS_PER_DAY", value)
    with pytest.raises(ValueError, match="UAT_MAX_CALLS_PER_DAY"):
        load_settings()


def test_env_file_is_ignored_and_example_is_blank():
    ignored = (ROOT / ".gitignore").read_text().splitlines()
    assert ".env" in ignored and "!.env.example" in ignored and ".uat/" in ignored
    example = (ROOT / ".env.example").read_text()
    assert re.search(r"^ANTHROPIC_API_KEY=$", example, re.M) and re.search(r"^ANTHROPIC_MODEL=$", example, re.M)


def _devcontainer():
    text = (ROOT / ".devcontainer" / "devcontainer.json").read_text(encoding="utf-8")
    return json.loads(re.sub(r"^\s*//.*$", "", text, flags=re.M)), text


def test_codespace_starts_app_on_private_port():
    cfg, _ = _devcontainer()
    assert "3.12" in cfg["image"]
    assert "streamlit run app.py" in cfg["postAttachCommand"]["app"]
    assert cfg["forwardPorts"] == [8501]
    assert "visibility" not in cfg["portsAttributes"]["8501"]  # Codespaces default = Private
    assert cfg["waitFor"] == "updateContentCommand" and "requirements.txt" in cfg["updateContentCommand"]


def test_secrets_requested_not_stored():
    cfg, text = _devcontainer()
    assert set(cfg["secrets"]) == {"ANTHROPIC_API_KEY", "ANTHROPIC_MODEL"}
    assert "sk-" not in text


def test_no_hardcoded_model_or_key_in_source():
    for path in [ROOT / "app.py", *(ROOT / "uat").glob("*.py")]:
        source = path.read_text(encoding="utf-8")
        assert not re.search(r"claude-[a-z]+-\d", source), path
        assert "sk-ant" not in source, path

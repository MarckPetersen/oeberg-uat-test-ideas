"""Danish / English texts (issue #3)."""

from uat.i18n import LANGUAGES, TEXTS, error_text, t

ERROR_CODES = ["empty", "too_long", "no_key", "no_model", "quota", "refusal", "truncated", "invalid_output", "auth",
               "permission", "model_not_found", "rate_limit", "timeout", "network", "bad_request", "api_error",
               "unexpected"]


def test_every_text_has_danish_and_english():
    for key, entry in TEXTS.items():
        assert set(entry) == {"en", "da"}, key
        assert all(v.strip() for v in entry.values()), key


def test_languages_offered():
    assert LANGUAGES == {"en": "English", "da": "Dansk"}


def test_english_interface_labels():
    assert t("title", "en") == "Øberg UAT Test Ideas"
    assert t("subtitle", "en") == "AI-Assisted UAT Test Ideas Generator"
    assert t("requirement_label", "en") == "Enter your requirement"
    assert t("generate", "en") == "Generate Test Ideas"
    assert t("results_title", "en") == "Generated UAT Test Ideas"


def test_danish_interface_labels():
    assert t("requirement_label", "da") == "Indsæt dit krav"
    assert t("generate", "da") == "Generér testidéer"
    assert t("results_title", "da") == "Genererede UAT-testidéer"


def test_every_error_code_is_translated():
    for code in ERROR_CODES:
        assert f"err_{code}" in TEXTS, code
    assert "4000" in error_text("too_long", "da", length=5000, limit=4000)
    assert error_text("something-new", "en") == t("err_unexpected", "en")


def test_formatting_tolerates_missing_params():
    assert t("err_quota", "en")  # no crash without params

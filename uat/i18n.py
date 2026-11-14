"""Danish / English interface texts. The selected language also controls the AI output language."""

from __future__ import annotations

LANGUAGES = {"en": "English", "da": "Dansk"}
DEFAULT_LANGUAGE = "en"

TEXTS: dict[str, dict[str, str]] = {
    "title": {"en": "Øberg UAT Test Ideas", "da": "Øberg UAT Test Ideas"},
    "subtitle": {"en": "AI-Assisted UAT Test Ideas Generator", "da": "AI-assisteret generator af UAT-testidéer"},
    "tagline": {"en": "AI suggests. Testers decide.", "da": "AI foreslår. Testere beslutter."},
    "language": {"en": "Language", "da": "Sprog"},
    "requirement_label": {"en": "Enter your requirement", "da": "Indsæt dit krav"},
    "requirement_placeholder": {
        "en": "e.g. The employee must be able to change a holiday request before it is approved.",
        "da": "F.eks. Medarbejderen skal kunne ændre en ferieanmodning, før den er godkendt.",
    },
    "char_count": {"en": "{n} / {limit} characters", "da": "{n} / {limit} tegn"},
    "generate": {"en": "Generate Test Ideas", "da": "Generér testidéer"},
    "regenerate": {"en": "Regenerate", "da": "Generér igen"},
    "clear": {"en": "Clear / New requirement", "da": "Ryd / Nyt krav"},
    "generating": {"en": "Claude is generating UAT test ideas …", "da": "Claude genererer UAT-testidéer …"},
    "results_title": {"en": "Generated UAT Test Ideas", "da": "Genererede UAT-testidéer"},
    "note_label": {"en": "Clarification", "da": "Afklaring"},
    "copy": {"en": "Copy", "da": "Kopiér"},
    "copy_all": {"en": "Copy all", "da": "Kopiér alle"},
    "copied": {"en": "Copied", "da": "Kopieret"},
    "copy_failed": {"en": "Copy failed", "da": "Kunne ikke kopiere"},
    "copy_idea_aria": {"en": "Copy idea {n}", "da": "Kopiér idé {n}"},
    "calls_left": {"en": "{n} Claude calls left today", "da": "{n} Claude-kald tilbage i dag"},
    "privacy_note": {
        "en": "Your requirement is sent to Anthropic's Claude API to generate ideas. Do not paste confidential "
        "requirements you are not allowed to share with a third-party processor.",
        "da": "Dit krav sendes til Anthropics Claude API for at generere idéer. Indsæt ikke fortrolige krav, som du "
        "ikke må dele med en tredjepartsbehandler.",
    },
    # errors (codes from uat.ai.AIError and Settings.problems)
    "err_empty": {"en": "Please enter a requirement first.", "da": "Indsæt venligst et krav først."},
    "err_too_long": {
        "en": "The requirement is too long ({length} characters, limit {limit}). Shorten it and try again.",
        "da": "Kravet er for langt ({length} tegn, grænse {limit}). Forkort det og prøv igen.",
    },
    "err_no_key": {
        "en": "Claude is not configured: ANTHROPIC_API_KEY is missing (Codespaces secret, or .env locally).",
        "da": "Claude er ikke sat op: ANTHROPIC_API_KEY mangler (Codespaces-secret eller .env lokalt).",
    },
    "err_no_model": {
        "en": "Claude is not configured: ANTHROPIC_MODEL is missing. Set a current Claude model ID.",
        "da": "Claude er ikke sat op: ANTHROPIC_MODEL mangler. Angiv et aktuelt Claude-model-ID.",
    },
    "err_quota": {
        "en": "Today's limit of {limit} Claude calls is used up. It resets tomorrow (or raise UAT_MAX_CALLS_PER_DAY).",
        "da": "Dagens grænse på {limit} Claude-kald er brugt. Den nulstilles i morgen (eller hæv UAT_MAX_CALLS_PER_DAY).",
    },
    "err_refusal": {"en": "Claude declined to process this requirement.", "da": "Claude afviste at behandle dette krav."},
    "err_truncated": {
        "en": "Claude's answer was cut off. Try again, or shorten the requirement.",
        "da": "Claudes svar blev afbrudt. Prøv igen, eller forkort kravet.",
    },
    "err_invalid_output": {
        "en": "Claude returned an answer that could not be used (tried twice). Please try again.",
        "da": "Claude returnerede et svar, der ikke kunne bruges (forsøgt to gange). Prøv venligst igen.",
    },
    "err_auth": {"en": "The API key was rejected. Check ANTHROPIC_API_KEY.", "da": "API-nøglen blev afvist. Tjek ANTHROPIC_API_KEY."},
    "err_permission": {
        "en": "The API key has no access to this model. Check ANTHROPIC_MODEL.",
        "da": "API-nøglen har ikke adgang til denne model. Tjek ANTHROPIC_MODEL.",
    },
    "err_model_not_found": {
        "en": "Model '{model}' was not found. Check ANTHROPIC_MODEL.",
        "da": "Modellen '{model}' blev ikke fundet. Tjek ANTHROPIC_MODEL.",
    },
    "err_rate_limit": {
        "en": "Claude's rate limit was reached. Wait a minute and try again.",
        "da": "Claudes hastighedsgrænse er nået. Vent et minut og prøv igen.",
    },
    "err_timeout": {"en": "Claude did not answer in time. Please try again.", "da": "Claude svarede ikke i tide. Prøv venligst igen."},
    "err_network": {
        "en": "Could not reach the Claude API. Check the network connection.",
        "da": "Kunne ikke få forbindelse til Claude API. Tjek netværksforbindelsen.",
    },
    "err_bad_request": {
        "en": "The request was rejected by the Claude API. Check the model configuration and try again.",
        "da": "Forespørgslen blev afvist af Claude API. Tjek modelopsætningen og prøv igen.",
    },
    "err_api_error": {"en": "Claude API error ({status}). Try again later.", "da": "Fejl fra Claude API ({status}). Prøv igen senere."},
    "err_unexpected": {
        "en": "Something unexpected went wrong. Your requirement is kept – please try again.",
        "da": "Der skete en uventet fejl. Dit krav er bevaret – prøv venligst igen.",
    },
}


def t(key: str, lang: str = DEFAULT_LANGUAGE, **params: object) -> str:
    entry = TEXTS[key]
    text = entry.get(lang) or entry[DEFAULT_LANGUAGE]
    try:
        return text.format(**params) if params else text
    except (KeyError, IndexError, ValueError):
        return text


def error_text(code: str, lang: str, **params: object) -> str:
    key = f"err_{code}"
    return t(key, lang, **params) if key in TEXTS else t("err_unexpected", lang)

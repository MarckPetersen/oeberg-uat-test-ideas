<p><img src="assets/logo.svg" alt="Øberg UAT Test Ideas" height="48"></p>

# Øberg UAT Test Ideas

**AI-Assisted UAT Test Ideas Generator** · *AI suggests. Testers decide.*

Enter **one** software requirement, click **Generate Test Ideas**, and Claude suggests a short numbered list of
User Acceptance Testing (UAT) ideas, usually 5–8 and fewer when the requirement is simple. Copy one idea or all of
them, regenerate, or clear and start over. The interface and the generated ideas are available in English and Danish.

One requirement. One button. Useful UAT test ideas.

The app is deliberately simple: there are no test techniques, priorities, risk scores, test steps or test management
features. It is a sibling of [Øberg TestLab](https://github.com/MarckPetersen/oeberg-testcase-generator) and uses
the same technology (Python + Streamlit + the Anthropic Python SDK) and the same Øberg visual identity.

## Run it in the browser (GitHub Codespaces)

No installation needed:

1. Make sure the Codespaces **user secrets** `ANTHROPIC_API_KEY` and `ANTHROPIC_MODEL` exist and have access to this
   repository (GitHub → Settings → Codespaces → Secrets).
2. On the repository page: **Code → Codespaces → Create codespace on main** (or open your existing codespace).
3. Wait 1–3 minutes the first time. The dependencies are installed and the app starts by itself. If no browser tab
   opens, open the **Ports** tab and click the globe icon next to **Øberg UAT Test Ideas (8501)**.
4. Enter a requirement and click **Generate Test Ideas**.

If the app did not start, run this in the codespace terminal:

```bash
streamlit run app.py
```

**Check that the secrets are available** without showing their values:

```bash
python -m uat.config
# ANTHROPIC_API_KEY: set
# ANTHROPIC_MODEL: set
```

Stop the codespace when you are done (it also stops by itself after 30 minutes of inactivity).

### Repository visibility ≠ app visibility

These are two separate controls:

- **Repository visibility** (public or private) decides who can read the *code*.
- **Codespaces port visibility** decides who can open the *running app*. Port 8501 is **Private** by default, so only
  you, signed in to GitHub, can open it.

A public repository does **not** make the running app public. **Never switch port 8501 to Public**, because your API key
pays for every Claude call. Other people who open a codespace from a public repository run their own copy with
their own secrets; they never get yours.

## Run it locally

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # add ANTHROPIC_API_KEY and ANTHROPIC_MODEL
streamlit run app.py
```

The app opens at http://localhost:8501. `.env` is git-ignored. Never commit your API key.

## Configuration

| Variable | Default | Purpose |
|---|---|---|
| `ANTHROPIC_API_KEY` | – | Required. Your Anthropic API key (Codespaces secret or `.env`) |
| `ANTHROPIC_MODEL` | – | Required. A current Claude model ID. No model is hardcoded; the app shows a message if it is missing |
| `UAT_MAX_CALLS_PER_DAY` | `30` | Daily Claude call quota |
| `UAT_MAX_INPUT_CHARS` | `4000` | Maximum requirement length |
| `UAT_MAX_OUTPUT_TOKENS` | `2000` | Output budget per call |
| `UAT_DATA_DIR` | `.uat` | Where the quota counter is stored (git-ignored) |

Settings are read from environment variables first (Codespaces secrets arrive as environment variables), then a local
`.env`, then Streamlit secrets (`.streamlit/secrets.toml`, git-ignored).

### Daily quota

Every Claude call counts against `UAT_MAX_CALLS_PER_DAY` (default 30). A **Generate** or **Regenerate** click is
normally one call; if Claude's answer can't be used, the app retries once, and the retry counts too. The counter is
stored in `.uat/usage.json` on the machine running the app and resets at midnight. The number of calls left is shown
under the buttons. When the limit is reached, the app shows a message and makes no more calls until the next day.
The quota protects against accidental overuse; access control comes from the private Codespaces port.

## Privacy

Your requirement text is **sent to Anthropic's Claude API** when you click Generate or Regenerate. Do not paste
confidential requirements that you are not allowed to share with a third-party processor. The app does not store or
log requirement text, keeps results only in your browser session (no database, no history), and never sends the API
key to the browser.

## How it works

```text
Browser ──(Streamlit websocket, rendered UI only)──▶ app.py (Streamlit, Python 3.12)
                                                      └─ uat/ai.py  ClaudeClient
                                                           └─ Anthropic API (key from env / Codespaces secret)
```

| Path | Purpose |
|---|---|
| `app.py` | The single page: header, language, requirement, actions, results |
| `uat/ai.py` | Claude client (structured output, retry, error mapping), UAT prompt, schema, deduplication, quota |
| `uat/config.py` | Settings and secrets (`python -m uat.config` checks them) |
| `uat/i18n.py` | Danish and English texts |
| `uat/ui.py` | Safe text rendering and the small copy-to-clipboard component |
| `assets/` | Øberg styling, logo and favicon |
| `.streamlit/config.toml` | Øberg theme |
| `.devcontainer/` | GitHub Codespaces setup |

Some details:

- **Prompt-injection resistance.** The requirement is sent inside `<requirement>` data tags, look-alike tags are
  neutralised, and the system prompt states that the data is never instructions.
- **Structured output.** Claude's answer is parsed into a Pydantic schema. Empty and duplicate ideas are removed,
  anything beyond 8 is cut, and nothing is invented.
- **One call per click.** A click marks one generation as pending; reruns never call the API again, and the action
  buttons are disabled while Claude is working.
- **Copy buttons** run in small isolated Streamlit iframes using the browser clipboard API, with a fallback. The idea
  text is passed only as escaped data and is never rendered as HTML.

## Run the tests

```bash
pytest
```

The tests never call the paid Claude API (Claude is replaced by a fake client). GitHub Actions runs them on every push
and Pull Request (`.github/workflows/ci.yml`).

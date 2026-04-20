# GuardianAI

GuardianAI is a Streamlit-based crisis support assistant that routes a user's message to a specialized Gemini-powered agent for fire, medical, safety threat, or emotional distress situations. It was built with Google ADK and Gemini for fast, calm, safety-focused guidance.

> GuardianAI is not a replacement for emergency services. If there is immediate danger, contact local emergency services first.

## What It Does

- Detects crisis category from a user's message.
- Estimates severity as `LOW`, `MODERATE`, or `CRITICAL`.
- Routes to a specialized agent when the situation is clear.
- Adds practical emergency steps from `guardian_resources.json`.
- Keeps a short active support session, then returns to general GuardianAI assistance.
- Supports Streamlit Cloud secrets for safe API key handling.

## Agent Routing

| Situation | Routed Agent | Example Triggers |
| --- | --- | --- |
| Fire or smoke | `FireAgent` | fire, smoke, gas leak, flames |
| Medical emergency | `MedicalAgent` | bleeding, overdose, chest pain, unconscious |
| Personal safety threat | `ThreatAgent` | following me, break-in, weapon, unsafe |
| Panic or distress | `EmotionalSupportAgent` | panic, anxious, overwhelmed, self-harm |
| Unknown/general | `GuardianAI` | fallback support |

## Project Structure

```text
GuardianAI/
├── guardian_app.py          # Streamlit chat UI
├── guardian_core.py         # Agent setup, routing, severity, and response logic
├── guardian_logic.py        # Backward-compatible Streamlit Cloud entrypoint
├── guardian_resources.json  # Emergency helplines and recommended steps
├── requirements.txt         # Streamlit Cloud dependencies
└── pyrightconfig.json       # Local editor/Pylance settings
```

## Local Setup

1. Create and activate a virtual environment.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies.

```powershell
python -m pip install -r requirements.txt
```

3. Add your local API key in an ignored `.env` file.

```env
GOOGLE_API_KEY="your_google_api_key_here"
```

4. Run the app.

```powershell
streamlit run guardian_app.py
```

## Streamlit Cloud Deployment

Set the app entry point to:

```text
guardian_app.py
```

Older deployments may still point to `guardian_logic.py`; this repository keeps that path working, but `guardian_app.py` is the preferred Streamlit entrypoint.

Add this in Streamlit Cloud secrets:

```toml
GOOGLE_API_KEY = "your_google_api_key_here"
```

After pushing changes to GitHub, Streamlit Cloud should redeploy automatically. If it does not, use **Reboot app** or **Deploy latest commit** from the Streamlit Cloud dashboard.

## Validation

Useful checks before pushing:

```powershell
python -m py_compile guardian_app.py guardian_logic.py
python -m json.tool guardian_resources.json
```

For editor diagnostics, this repository includes `pyrightconfig.json` so Pylance/Pyright can use the local `.venv` and focus on the deploy files.

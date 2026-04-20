import json
import os
import time
from functools import lru_cache
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
RESOURCES_PATH = BASE_DIR / "guardian_resources.json"
USER_ID = "guardian-user"
DEFAULT_SESSION_ID = "guardian-session"
DEFAULT_MODEL = os.getenv("GUARDIAN_MODEL", "gemini-2.5-flash-lite")
SPECIALIZED_CATEGORIES = {"fire", "medical", "threat", "emotional"}


def _load_local_env():
    try:
        from dotenv import load_dotenv
    except ImportError:
        return

    load_dotenv(BASE_DIR / ".env")


def _read_streamlit_secret(name):
    try:
        import streamlit as st

        value = st.secrets.get(name)
    except Exception:
        return None

    return str(value) if value else None


def configure_google_api_key():
    _load_local_env()

    api_key = os.getenv("GOOGLE_API_KEY") or _read_streamlit_secret("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GOOGLE_API_KEY is missing. Add it in Streamlit Cloud secrets or in a local .env file."
        )

    os.environ["GOOGLE_API_KEY"] = api_key
    return api_key


conversation_log = []


def log_interaction(user_message, severity, category, agent_name, response):
    conversation_log.append(
        {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "message": user_message,
            "severity": severity,
            "category": category,
            "agent": agent_name,
            "response": response[:200],
        }
    )


guardian_prompt = """
You are GuardianAI, a calm crisis support assistant.
Give short, direct safety guidance.
If there is immediate danger, tell the user to contact local emergency services now.
Do not claim that you have contacted emergency services.
"""

fire_prompt = """
You are FireAgent, specialized in fire and smoke emergencies.
Prioritize evacuation, avoiding elevators, staying low under smoke, and calling fire services.
Keep guidance short and step-by-step.
"""

medical_prompt = """
You are MedicalAgent, specialized in urgent medical guidance.
Encourage calling emergency medical services for serious symptoms.
Avoid diagnosis; give safe first-response steps while help is contacted.
"""

threat_prompt = """
You are ThreatAgent, specialized in personal safety threats.
Help the user move toward safety, avoid confrontation, contact authorities, and alert trusted people.
Keep the guidance discreet and practical.
"""

emotional_prompt = """
You are EmotionalSupportAgent.
Help the user slow down, breathe, and take one safe next step.
If the user mentions self-harm or suicide, urge immediate support from emergency services,
a crisis helpline, or a trusted nearby person.
"""


def create_agent(name, instruction, model=DEFAULT_MODEL):
    configure_google_api_key()

    from google.adk.agents import LlmAgent

    return LlmAgent(
        name=name,
        model=model,
        instruction=instruction,
    )


def get_emergency_numbers(country):
    emergency_numbers = {
        "india": {"police": "112", "medical": "102", "fire": "101"},
        "usa": {"general": "911"},
        "uk": {"general": "999"},
        "australia": {"general": "000"},
    }

    return emergency_numbers.get(country.lower(), {"general": "112"})


def load_crisis_resources():
    if not RESOURCES_PATH.exists():
        raise RuntimeError(f"Missing crisis resources file: {RESOURCES_PATH.name}")

    with RESOURCES_PATH.open(encoding="utf-8") as file:
        return json.load(file)


def create_runner(agent):
    from google.adk.apps.app import App
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService

    app = App(
        name=f"{agent.name}_App",
        root_agent=agent,
    )

    return Runner(
        app=app,
        session_service=InMemorySessionService(),
    )


AGENT_NAMES = {
    "unknown": "GuardianAI",
    "fire": "FireAgent",
    "medical": "MedicalAgent",
    "threat": "ThreatAgent",
    "emotional": "EmotionalSupportAgent",
}

AGENT_PROMPTS = {
    "unknown": ("GuardianAI", guardian_prompt),
    "fire": ("FireAgent", fire_prompt),
    "medical": ("MedicalAgent", medical_prompt),
    "threat": ("ThreatAgent", threat_prompt),
    "emotional": ("EmotionalAgent", emotional_prompt),
}

CATEGORY_KEYWORDS = {
    "fire": [
        "fire",
        "smoke",
        "burning",
        "flames",
        "gas leak",
        "explosion",
        "sparks",
    ],
    "medical": [
        "bleeding",
        "overdose",
        "unconscious",
        "chest pain",
        "not breathing",
        "can't breathe",
        "cannot breathe",
        "heart attack",
        "seizure",
        "stroke",
        "fainted",
        "injured",
    ],
    "threat": [
        "following me",
        "threat",
        "unsafe",
        "break in",
        "break-in",
        "attacked",
        "assault",
        "weapon",
        "stalker",
        "robbery",
        "violence",
    ],
    "emotional": [
        "panic",
        "panic attack",
        "anxious",
        "crying",
        "overwhelmed",
        "suicide",
        "suicidal",
        "self harm",
        "self-harm",
        "kill myself",
    ],
}

CRITICAL_KEYWORDS = [
    "not breathing",
    "can't breathe",
    "cannot breathe",
    "unconscious",
    "bleeding heavily",
    "overdose",
    "trapped",
    "heart attack",
    "stroke",
    "weapon",
    "suicide",
    "suicidal",
    "kill myself",
]


def detect_category(message):
    normalized_message = message.lower()

    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword in normalized_message for keyword in keywords):
            return category

    return "unknown"


def compute_severity(message, category):
    normalized_message = message.lower()

    if any(keyword in normalized_message for keyword in CRITICAL_KEYWORDS):
        return "CRITICAL"

    if category == "fire":
        return "CRITICAL"

    if category in {"medical", "threat"}:
        return "MODERATE"

    return "LOW"


def explain_decision(category):
    reasons = {
        "fire": "Fire, smoke, gas, or burning-related keywords were detected.",
        "medical": "Urgent medical symptoms or injury keywords were detected.",
        "threat": "Personal safety threat keywords were detected.",
        "emotional": "Panic, distress, or self-harm-related keywords were detected.",
    }

    return reasons.get(category, "No specialized crisis keywords were detected.")


def build_help_text(resources, category):
    resource_key_by_category = {
        "fire": "fire_hazard",
        "medical": "medical_emergency",
        "threat": "safety_threat",
        "emotional": "emotional_support",
    }

    resource_key = resource_key_by_category.get(category)
    if not resource_key:
        return ""

    help_info = resources.get(resource_key)
    if not help_info:
        return ""

    steps = "\n".join(f"- {step}" for step in help_info["steps"])

    return f"""
Emergency Helpline: {help_info['helpline']}

Recommended Steps:
{steps}
"""


async def ensure_session(runner, user_id, session_id):
    session_service = runner.session_service
    session = await session_service.get_session(
        user_id=user_id,
        session_id=session_id,
        app_name=runner.app.name,
    )

    if session is None:
        await session_service.create_session(
            user_id=user_id,
            session_id=session_id,
            app_name=runner.app.name,
        )


async def run_agent(runner, message, user_id, session_id):
    from google.genai.types import Content, Part

    response_text = ""

    async for event in runner.run_async(
        new_message=Content(role="user", parts=[Part(text=message)]),
        user_id=user_id,
        session_id=session_id,
    ):
        if hasattr(event, "content") and event.content:
            for part in event.content.parts:
                if part.text:
                    response_text += part.text

    return response_text.strip()


@lru_cache(maxsize=None)
def get_runner(category):
    agent_name, instruction = AGENT_PROMPTS.get(category, AGENT_PROMPTS["unknown"])
    agent = create_agent(agent_name, instruction)
    return create_runner(agent)


async def handle_message(
    message,
    forced_agent=None,
    session_id=DEFAULT_SESSION_ID,
    user_id=USER_ID,
):
    resources = load_crisis_resources()
    category = forced_agent if forced_agent in SPECIALIZED_CATEGORIES else detect_category(message)
    severity = compute_severity(message, category)
    reason = explain_decision(category)
    runner_to_use = get_runner(category)
    agent_name = AGENT_NAMES.get(category, "GuardianAI")

    await ensure_session(runner_to_use, user_id, session_id)
    response_text = await run_agent(runner_to_use, message, user_id, session_id)
    help_text = build_help_text(resources, category)

    resolution_prompt = """

If your situation is now under control or you are safe, please tell me "I am safe".
I will then close the crisis session.
"""

    log_interaction(
        message,
        severity,
        category,
        agent_name,
        response_text,
    )

    return {
        "severity": severity,
        "category": category,
        "agent": agent_name,
        "reason": reason,
        "response": f"{response_text}\n\n{help_text}{resolution_prompt}".strip(),
    }

# guardian_logic.py

import json
import os
import time
import asyncio

from google.genai.types import Content, Part
from google.adk.agents import LlmAgent
from google.adk.apps.app import App
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner


# -------------------------------------------------
# Load API KEY
# -------------------------------------------------

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in .env file")

# -------------------------------------------------
# Conversation Memory
# -------------------------------------------------

conversation_log = []


def log_interaction(user_message, severity, category, agent_name, response):

    entry = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "message": user_message,
        "severity": severity,
        "category": category,
        "agent": agent_name,
        "response": response[:200],
    }

    conversation_log.append(entry)


# -------------------------------------------------
# System Prompts
# -------------------------------------------------

guardian_prompt = """
You are GuardianAI, a calm crisis support assistant.
Provide clear, short safety guidance.
Encourage contacting emergency services if necessary.
"""

fire_prompt = """
You are FireAgent specialized in fire emergencies.
Tell the user to evacuate immediately and call fire services.
Give short step-by-step instructions.
"""

medical_prompt = """
You are MedicalAgent specialized in medical emergencies.
Stay calm and guide the user safely.
Encourage contacting ambulance services.
"""

threat_prompt = """
You are ThreatAgent specialized in safety threats.
Help the user move to a safe place and contact authorities.
"""

emotional_prompt = """
You are EmotionalSupportAgent.
Help calm the user during panic or distress.
Suggest breathing and grounding techniques.
"""


# -------------------------------------------------
# Agents
# -------------------------------------------------

guardian_agent = LlmAgent(
    name="GuardianAI",
    model="gemini-2.5-pro",
    instruction=guardian_prompt
)

fire_agent = LlmAgent(
    name="FireAgent",
    model="gemini-2.5-pro",
    instruction=fire_prompt
)

MedicalAgent = LlmAgent(
    name="MedicalAgent",
    model="gemini-2.5-pro",
    instruction=medical_prompt
)

ThreatAgent = LlmAgent(
    name="ThreatAgent",
    model="gemini-2.5-pro",
    instruction=threat_prompt
)

EmotionalAgent = LlmAgent(
    name="EmotionalAgent",
    model="gemini-2.5-pro",
    instruction=emotional_prompt
)

# -----------------------------------------
# Location Detection (placeholder)
# -----------------------------------------
def get_emergency_numbers(country):

    EMERGENCY_NUMBERS = {
        "india": {"police": "112", "medical": "102", "fire": "101"},
        "usa": {"general": "911"},
        "uk": {"general": "999"},
        "australia": {"general": "000"},
    }

    return EMERGENCY_NUMBERS.get(country.lower(), {"general": "112"})

# -----------------------------------------
# Json Parsing (placeholder)
# -----------------------------------------

def load_crisis_resources():

    with open("guardian_resources.json") as f:
        return json.load(f)

# -------------------------------------------------
# Runner Setup
# -------------------------------------------------

def create_runner(agent):

    app = App(
        name=f"{agent.name}_App",
        root_agent=agent
    )

    session_service = InMemorySessionService()

    runner = Runner(
        app=app,
        session_service=session_service
    )

    return runner


guardian_runner = create_runner(guardian_agent)
fire_runner = create_runner(fire_agent)
medical_runner = create_runner(MedicalAgent)
threat_runner = create_runner(ThreatAgent)
emotional_runner = create_runner(EmotionalAgent)


USER_ID = "guardian-user"
SESSION_ID = "guardian-session"


# -------------------------------------------------
# Category Detection
# -------------------------------------------------

def detect_category(message):

    msg = message.lower()

    if any(x in msg for x in ["fire", "smoke", "burning", "flames", "gas"]):
        return "fire"

    if any(x in msg for x in ["bleeding", "overdose", "unconscious", "chest pain"]):
        return "medical"

    if any(x in msg for x in ["following me", "threat", "unsafe", "break in"]):
        return "threat"

    if any(x in msg for x in ["panic", "anxious", "crying", "overwhelmed"]):
        return "emotional"

    return "unknown"


# -------------------------------------------------
# Severity Detection
# -------------------------------------------------

def compute_severity(message, category):

    msg = message.lower()

    critical_words = [
        "not breathing",
        "unconscious",
        "bleeding heavily",
        "overdose",
        "trapped"
    ]

    if category == "fire":
        return "CRITICAL"

    if any(x in msg for x in critical_words):
        return "CRITICAL"

    if category in ["medical", "threat"]:
        return "MODERATE"

    if category == "emotional":
        return "LOW"

    return "LOW"


# -------------------------------------------------
# Decision Explanation
# -------------------------------------------------

def explain_decision(category):

    if category == "fire":
        return "Smoke or fire keywords detected."

    if category == "medical":
        return "Medical emergency indicators detected."

    if category == "threat":
        return "Safety threat keywords detected."

    if category == "emotional":
        return "Emotional distress indicators detected."

    return "No crisis keywords detected."


# -------------------------------------------------
# Agent Router
# -------------------------------------------------

agent_map = {
    "fire": fire_runner,
    "medical": medical_runner,
    "threat": threat_runner,
    "emotional": emotional_runner
}

# -------------------------------------------------
# Main Orchestrating Logic
# -------------------------------------------------

async def handle_message(message, forced_agent=None):

    resources = load_crisis_resources()

    # -----------------------------
    # Routing logic
    # -----------------------------

    if forced_agent:
        category = forced_agent
    else:
        category = detect_category(message)

    severity = compute_severity(message, category)
    reason = explain_decision(category)

    runner_to_use = agent_map.get(category, guardian_runner)

    agent_name = category.capitalize() + "Agent" if category in agent_map else "GuardianAI"

    # -----------------------------
    # Ensure ADK session exists
    # -----------------------------

    session_service = runner_to_use.session_service

    session = await session_service.get_session(
        user_id=USER_ID,
        session_id=SESSION_ID,
        app_name=runner_to_use.app.name
    )

    if session is None:
        await session_service.create_session(
            user_id=USER_ID,
            session_id=SESSION_ID,
            app_name=runner_to_use.app.name
        )

    # -----------------------------
    # Run agent
    # -----------------------------

    response_text = ""

    async for event in runner_to_use.run_async(
        new_message=Content(role="user", parts=[Part(text=message)]),
        user_id=USER_ID,
        session_id=SESSION_ID
    ):
        if hasattr(event, "content") and event.content:
            for part in event.content.parts:
                if part.text:
                    response_text += part.text

    # -----------------------------
    # Emergency protocol guidance
    # -----------------------------

    help_text = ""

    if category == "fire":
        help_info = resources["fire_hazard"]

    elif category == "medical":
        help_info = resources["medical_emergency"]

    elif category == "threat":
        help_info = resources["safety_threat"]

    elif category == "emotional":
        help_info = resources["emotional_support"]

    else:
        help_info = None

    if help_info:

        steps = "\n".join([f"- {s}" for s in help_info["steps"]])

        help_text = f"""

Emergency Helpline: {help_info['helpline']}

Recommended Steps:
{steps}
"""

    # -----------------------------
    # Session resolution prompt
    # -----------------------------

    resolution_prompt = """

If your situation is now under control or you are safe, please tell me "I am safe".
I will then close the crisis session.
"""

    log_interaction(
        message,
        severity,
        category,
        agent_name,
        response_text
    )

    return {
        "severity": severity,
        "category": category,
        "agent": agent_name,
        "reason": reason,
        "response": response_text + help_text + resolution_prompt
    }

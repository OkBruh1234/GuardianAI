# #guardian_logic.py

# import os
# import json
# import time
# import asyncio
# from dotenv import load_dotenv

# from google.genai.types import Content, Part
# from google.adk.agents import LlmAgent
# from google.adk.apps.app import App
# from google.adk.sessions import InMemorySessionService
# from google.adk.runners import Runner

# # ---------------------------------------------------
# # Load API key
# # ---------------------------------------------------

# load_dotenv()

# GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# if not GOOGLE_API_KEY:
#   raise ValueError("❌ GOOGLE_API_KEY not found in .env file")

# # ---------------------------------------------------
# # Conversation memory
# # ---------------------------------------------------

# conversation_log = []

# def log_interaction(user_message, severity, category, agent_name, response_text):

# entry = {
#     "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
#     "user_message": user_message,
#     "severity": severity,
#     "category": category,
#     "agent_used": agent_name,
#     "response": response_text[:200]
# }

# conversation_log.append(entry)
# # ---------------------------------------------------
# # System Prompts
# # ---------------------------------------------------

# guardian_prompt = """
# You are GuardianAI — a compassionate crisis support assistant.

# Your goals:

# Stay calm and supportive

# Provide clear step-by-step guidance

# Encourage contacting emergency services when needed

# Never diagnose medical conditions
# """

# fire_prompt = """
# You are FireAgent specialized in fire emergencies.

# Provide immediate evacuation guidance.
# Be calm but urgent.
# Give 3-6 short actionable steps.
# """

# medical_prompt = """
# You are MedicalAgent specialized in medical emergencies.

# Guide the user calmly and recommend contacting emergency services.
# """

# threat_prompt = """
# You are ThreatAgent specialized in safety threats.

# Help the user move to safety and contact authorities.
# """

# emotional_prompt = """
# You are EmotionalSupportAgent.

# Help calm the user during panic or distress.
# Encourage breathing and grounding techniques.
# """

# # ---------------------------------------------------
# # Agent Creation
# # ---------------------------------------------------

# guardian_agent = LlmAgent(
# name="GuardianAI",
# model="gemini-2.5-flash-lite",
# instruction=guardian_prompt
# )

# fire_agent = LlmAgent(
# name="FireAgent",
# model="gemini-2.5-flash-lite",
# instruction=fire_prompt
# )

# MedicalAgent = LlmAgent(
# name="MedicalAgent",
# model="gemini-2.5-flash-lite",
# instruction=medical_prompt
# )

# ThreatAgent = LlmAgent(
# name="ThreatAgent",
# model="gemini-2.5-flash-lite",
# instruction=threat_prompt
# )

# EmotionalAgent = LlmAgent(
# name="EmotionalAgent",
# model="gemini-2.5-flash-lite",
# instruction=emotional_prompt
# )

# # ---------------------------------------------------
# # Runner Setup
# # ---------------------------------------------------

# def create_runner(agent):

# app = App(
#     name=f"{agent.name}-App",
#     root_agent=agent
# )

# session_service = InMemorySessionService()

# runner = Runner(
#     app=app,
#     session_service=session_service
# )

# return runner

# guardian_runner = create_runner(guardian_agent)
# fire_runner = create_runner(fire_agent)
# medical_runner = create_runner(MedicalAgent)
# threat_runner = create_runner(ThreatAgent)
# emotional_runner = create_runner(EmotionalAgent)

# USER_ID = "guardian-user"
# SESSION_ID = "guardian-session"

# # ---------------------------------------------------
# # Crisis Detection
# # ---------------------------------------------------

# def detect_category(message: str) -> str:

# msg = message.lower()

# if any(x in msg for x in ["fire", "smoke", "burning", "flames", "gas"]):
#     return "fire"

# if any(x in msg for x in ["bleeding", "unconscious", "overdose", "chest pain"]):
#     return "medical"

# if any(x in msg for x in ["following me", "threat", "unsafe", "break in"]):
#     return "threat"

# if any(x in msg for x in ["panic", "anxious", "crying", "overwhelmed"]):
#     return "emotional"

# return "unknown"
# # ---------------------------------------------------
# # Severity Logic
# # ---------------------------------------------------

# def compute_severity(message: str, category: str) -> str:

# msg = message.lower()

# critical_keywords = [
#     "unconscious",
#     "not breathing",
#     "bleeding heavily",
#     "trapped",
#     "overdose"
# ]

# if category == "fire":
#     return "CRITICAL"

# if any(word in msg for word in critical_keywords):
#     return "CRITICAL"

# if category in ["medical", "threat"]:
#     return "MODERATE"

# if category == "emotional":
#     return "LOW"

# return "LOW"
# # ---------------------------------------------------
# # Explain Decision
# # ---------------------------------------------------

# def explain_decision(message: str, category: str):

# if category == "fire":
#     return "Fire or smoke keywords detected."

# if category == "medical":
#     return "Medical emergency indicators detected."

# if category == "threat":
#     return "Safety threat indicators detected."

# if category == "emotional":
#     return "Emotional distress indicators detected."

# return "No crisis keywords detected."
# # ---------------------------------------------------
# # Agent Map
# # ---------------------------------------------------

# agent_map = {
# "fire": fire_runner,
# "medical": medical_runner,
# "threat": threat_runner,
# "emotional": emotional_runner
# }

# # ---------------------------------------------------
# # Main Handler
# # ---------------------------------------------------

# async def handle_message(message: str):

# category = detect_category(message)
# severity = compute_severity(message, category)

# reason = explain_decision(message, category)

# print(f"\n[Severity: {severity}]")
# print(f"[Category: {category}]")
# print(f"[Decision Reason: {reason}]\n")

# runner_to_use = agent_map.get(category, guardian_runner)

# agent_name = category.capitalize() + "Agent" if category in agent_map else "GuardianAI"

# print(f"[Assigned Agent: {agent_name}]\n")

# response_text = ""

# async for event in runner_to_use.run_async(
#     new_message=Content(role="user", parts=[Part(text=message)]),
#     user_id=USER_ID,
#     session_id=SESSION_ID
# ):
#     if hasattr(event, "content") and event.content:
#         for part in event.content.parts:
#             if part.text:
#                 print(part.text, end="", flush=True)
#                 response_text += part.text

# log_interaction(
#     message,
#     severity,
#     category,
#     agent_name,
#     response_text
# )

# return response_text


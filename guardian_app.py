import streamlit as st
import asyncio
from guardian_logic import handle_message

st.set_page_config(page_title="GuardianAI", page_icon="🚨")

st.title("🚨 GuardianAI Crisis Assistant")
st.write("Describe your situation and GuardianAI will guide you.")

# -----------------------------
# Session State
# -----------------------------

if "messages" not in st.session_state:
    st.session_state.messages = []

if "active_agent" not in st.session_state:
    st.session_state.active_agent = None

if "agent_turns" not in st.session_state:
    st.session_state.agent_turns = 0

if "resolution_attempts" not in st.session_state:
    st.session_state.resolution_attempts = 0


# -----------------------------
# Show previous messages
# -----------------------------

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


user_input = st.chat_input("Describe what is happening...")


if user_input:

    with st.chat_message("user"):
        st.markdown(user_input)

    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })


    # -----------------------------
    # Crisis resolution detection
    # -----------------------------

    resolution_keywords = [
        "i am safe",
        "safe now",
        "i'm safe",
        "resolved",
        "it's resolved"
    ]

    if any(k in user_input.lower() for k in resolution_keywords):

        st.success("✅ Glad you are safe. Crisis session closed.")

        st.session_state.active_agent = None
        st.session_state.agent_turns = 0
        st.session_state.resolution_attempts = 0

        st.stop()


    # -----------------------------
    # Call backend
    # -----------------------------

    if st.session_state.active_agent:

        result = asyncio.run(
            handle_message(
                user_input,
                forced_agent=st.session_state.active_agent
            )
        )

    else:

        result = asyncio.run(handle_message(user_input))

        st.session_state.active_agent = result["category"]


    response_text = f"""
Severity: {result['severity']}

Category: {result['category']}

Agent: {result['agent']}

Decision Reason: {result['reason']}

Response:

{result['response']}
"""

    with st.chat_message("assistant"):
        st.markdown(response_text)

    st.session_state.messages.append({
        "role": "assistant",
        "content": response_text
    })


    # -----------------------------
    # Turn tracking
    # -----------------------------

    st.session_state.agent_turns += 1
    st.session_state.resolution_attempts += 1


    if st.session_state.agent_turns >= 3:

        st.warning("🔁 Returning to GuardianAI general assistance.")

        st.session_state.active_agent = None
        st.session_state.agent_turns = 0


    if st.session_state.resolution_attempts >= 3:

        st.info("If the situation is resolved please tell me 'I am safe' so I can close the session.")


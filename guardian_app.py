import asyncio
import uuid

import streamlit as st

from guardian_core import SPECIALIZED_CATEGORIES, handle_message


RESOLUTION_KEYWORDS = [
    "i am safe",
    "i'm safe",
    "safe now",
    "resolved",
    "it's resolved",
    "under control",
]

QUICK_PROMPTS = {
    "Fire": "There is fire or smoke near me.",
    "Medical": "Someone needs urgent medical help.",
    "Threat": "I feel unsafe and someone may be threatening me.",
    "Panic": "I am panicking and need help calming down.",
    "Other": "I need general safety guidance.",
}


def init_session_state():
    defaults = {
        "messages": [],
        "active_agent": None,
        "agent_turns": 0,
        "resolution_attempts": 0,
        "session_id": f"guardian-{uuid.uuid4()}",
        "last_result": None,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_session():
    st.session_state.messages = []
    st.session_state.active_agent = None
    st.session_state.agent_turns = 0
    st.session_state.resolution_attempts = 0
    st.session_state.session_id = f"guardian-{uuid.uuid4()}"
    st.session_state.last_result = None


def run_handler(user_input):
    return asyncio.run(
        handle_message(
            user_input,
            forced_agent=st.session_state.active_agent,
            session_id=st.session_state.session_id,
        )
    )


def build_response(result):
    return f"""
**Severity:** {result['severity']}

**Category:** {result['category']}

**Agent:** {result['agent']}

**Decision reason:** {result['reason']}

{result['response']}
"""


def close_crisis_session():
    response_text = "Glad you are safe. Crisis session closed."

    with st.chat_message("assistant"):
        st.success(response_text)

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": response_text,
        }
    )
    st.session_state.active_agent = None
    st.session_state.agent_turns = 0
    st.session_state.resolution_attempts = 0
    st.session_state.last_result = None


def render_app():
    st.set_page_config(page_title="GuardianAI", page_icon="G")
    init_session_state()

    st.title("GuardianAI Crisis Assistant")
    st.caption("If this is an immediate emergency, contact local emergency services now.")

    with st.sidebar:
        st.subheader("Session")
        current_agent = st.session_state.active_agent or "GuardianAI"
        st.write(f"Active support: {current_agent}")

        if st.session_state.last_result:
            st.write(f"Last severity: {st.session_state.last_result['severity']}")
            st.write(f"Last category: {st.session_state.last_result['category']}")

        st.button("Reset chat", on_click=reset_session, use_container_width=True)

    if not st.session_state.messages:
        with st.chat_message("assistant"):
            st.markdown(
                "Tell me what is happening. I will route you to fire, medical, safety, "
                "or emotional support guidance and keep the steps short."
            )

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    quick_prompt = None
    if not st.session_state.messages:
        quick_cols = st.columns(len(QUICK_PROMPTS))
        for column, (label, prompt) in zip(quick_cols, QUICK_PROMPTS.items()):
            if column.button(label, use_container_width=True):
                quick_prompt = prompt

    typed_input = st.chat_input("Describe what is happening...")
    user_input = typed_input or quick_prompt

    if not user_input:
        return

    with st.chat_message("user"):
        st.markdown(user_input)

    st.session_state.messages.append(
        {
            "role": "user",
            "content": user_input,
        }
    )

    if any(keyword in user_input.lower() for keyword in RESOLUTION_KEYWORDS):
        close_crisis_session()
        st.stop()

    try:
        with st.spinner("GuardianAI is assessing the situation..."):
            result = run_handler(user_input)
    except RuntimeError as exc:
        st.error(str(exc))
        st.info(
            'Add GOOGLE_API_KEY to Streamlit Cloud secrets as GOOGLE_API_KEY = "your-key". '
            "For local runs, keep it in your ignored .env file."
        )
        st.stop()
        raise
    except Exception as exc:
        st.error("GuardianAI could not complete the response.")
        with st.expander("Technical details"):
            st.code(str(exc))
        st.stop()
        raise

    st.session_state.last_result = result

    if result["category"] in SPECIALIZED_CATEGORIES:
        st.session_state.active_agent = result["category"]
    else:
        st.session_state.active_agent = None

    response_text = build_response(result)

    with st.chat_message("assistant"):
        if result["severity"] == "CRITICAL":
            st.error("Critical situation detected. Contact emergency services now if you can.")
        st.markdown(response_text)

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": response_text,
        }
    )

    st.session_state.agent_turns += 1
    st.session_state.resolution_attempts += 1

    if st.session_state.agent_turns >= 3:
        st.info("Returning to GuardianAI general assistance.")
        st.session_state.active_agent = None
        st.session_state.agent_turns = 0

    if st.session_state.resolution_attempts >= 3:
        st.info('If you are safe now, tell me "I am safe" so I can close the session.')


if __name__ == "__main__":
    render_app()

import streamlit as st
import os
from dotenv import load_dotenv
import google.generativeai as genai

# -----------------------------
# Load Gemini API
# -----------------------------
load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    st.error("GOOGLE_API_KEY not found. Check your .env file.")
    st.stop()

genai.configure(api_key=api_key)

model = genai.GenerativeModel("gemini-2.5-flash")

# -----------------------------
# Page Configuration
# -----------------------------
st.set_page_config(
    page_title="Ziggy AI",
    page_icon="🤖",
    layout="wide"
)

# -----------------------------
# Sidebar
# -----------------------------
with st.sidebar:
    st.title("🤖 Ziggy AI")

    st.markdown("---")

    if st.button("🆕 New Chat"):
        st.session_state.messages = []
        st.rerun()

    if st.button("🗑 Clear Chat"):
        st.session_state.messages = []
        st.rerun()

    st.markdown("---")

    st.subheader("About")
    st.write(
        """
Welcome to **Ziggy AI**!

Your professional AI assistant powered by Google's Gemini model.

Version **1.0**
"""
    )

# -----------------------------
# Main Page
# -----------------------------
st.title("🤖 Ziggy AI")
st.caption("Build. Learn. Create.")

# -----------------------------
# Chat History
# -----------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# -----------------------------
# Chat Input
# -----------------------------
prompt = st.chat_input("Ask me anything...")

if prompt:

    with st.chat_message("user"):
        st.markdown(prompt)

    st.session_state.messages.append(
        {"role": "user", "content": prompt}
    )

    system_prompt = f"""
You are Ziggy AI.

You are friendly, professional and helpful.

Rules:
- If the user says hi, hello or hey, greet them briefly.
- If the user says thank you, reply politely.
- Keep answers concise unless more detail is requested.
- Explain AI and programming topics clearly with examples.
- Never introduce yourself as Gemini. Always say you are Ziggy AI.

User:
{prompt}
"""

    with st.chat_message("assistant"):
        with st.spinner("🤖 Ziggy is thinking..."):
            response = model.generate_content(system_prompt)
            ai_response = response.text
            st.markdown(ai_response)

    st.session_state.messages.append(
        {"role": "assistant", "content": ai_response}
    )
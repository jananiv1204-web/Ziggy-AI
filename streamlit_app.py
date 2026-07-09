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
# Initialize Chat History
# -----------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

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

    st.write("""
Welcome to **Ziggy AI**!

Your professional AI assistant powered by Google's Gemini.

Version **1.0**
""")

# -----------------------------
# Main Page
# -----------------------------
st.title("🤖 Ziggy AI")
st.caption("Build • Learn • Create")

# -----------------------------
# Welcome Screen
# -----------------------------
if len(st.session_state.messages) == 0:
    st.markdown("""
# 👋 Welcome to Ziggy AI

### Your Personal AI Assistant

Ask me anything about:

- 🤖 Artificial Intelligence
- 💻 Programming
- 🐍 Python
- 📊 Machine Learning
- 🚀 Career Guidance

---

💡 **Try asking:**

- What is Artificial Intelligence?
- Explain Machine Learning.
- Help me write Python code.
- Teach me Git and GitHub.
""")

# -----------------------------
# Display Chat History
# -----------------------------
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# -----------------------------
# Chat Input
# -----------------------------
prompt = st.chat_input("Ask me anything...")

if prompt:

    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)

    st.session_state.messages.append(
        {
            "role": "user",
            "content": prompt
        }
    )

    # AI Prompt
    system_prompt = f"""
You are Ziggy AI.

You are a friendly, professional AI assistant.

Rules:
- Greet users briefly if they say hi, hello or hey.
- Reply politely when they say thank you.
- Explain AI, Python and programming clearly.
- Keep answers concise unless they ask for details.
- Never say you are Gemini.
- Always introduce yourself as Ziggy AI.

User:
{prompt}
"""

    # AI Response
    try:
        with st.chat_message("assistant"):
            with st.spinner("🤖 Ziggy is thinking..."):
                response = model.generate_content(system_prompt)
                ai_response = response.text
                st.markdown(ai_response)

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": ai_response
            }
        )

    except Exception:
        st.error("⚠️ Ziggy AI is temporarily unavailable or the API quota has been exceeded. Please try again later.")
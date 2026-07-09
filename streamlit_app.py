import streamlit as st
from pdf_helper import read_pdf
import os
import json
import glob
from datetime import datetime

from dotenv import load_dotenv
import google.generativeai as genai
import streamlit.components.v1 as components


# ---------------------------------------
# Load Environment Variables
# ---------------------------------------
load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    st.error("GOOGLE_API_KEY not found in .env file.")
    st.stop()

genai.configure(api_key=api_key)

model = genai.GenerativeModel("gemini-2.5-flash")


# ---------------------------------------
# Page Configuration
# ---------------------------------------
st.set_page_config(
    page_title="Ziggy AI",
    page_icon="🤖",
    layout="wide"
)


# ---------------------------------------
# Session State
# ---------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "pdf_text" not in st.session_state:
    st.session_state.pdf_text = ""
    # ---------------------------------------
# Sidebar
# ---------------------------------------
with st.sidebar:

    st.title("🤖 Ziggy AI")

    st.markdown("---")

    # New Chat
    if st.button("🆕 New Chat"):

        st.session_state.messages = []
        st.rerun()

    # Clear Chat
    if st.button("🗑️ Clear Chat"):

        st.session_state.messages = []
        st.rerun()

    st.markdown("---")

    # Download Chat
    if st.session_state.messages:

        chat_text = ""

        for msg in st.session_state.messages:

            sender = "👤 User" if msg["role"] == "user" else "🤖 Ziggy AI"

            chat_text += f"{sender} ({msg['time']})\n"
            chat_text += f"{msg['content']}\n\n"

        st.download_button(
            label="📄 Download Chat",
            data=chat_text,
            file_name="ziggy_chat.txt",
            mime="text/plain",
        )

        if st.button("💾 Save Chat"):

            os.makedirs("chat_history", exist_ok=True)

            filename = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

            with open(f"chat_history/{filename}.json", "w") as file:

                json.dump(st.session_state.messages, file, indent=4)

            st.success("✅ Chat Saved!")

    st.markdown("---")

    # Saved Chats
    st.subheader("📚 Saved Chats")

    os.makedirs("chat_history", exist_ok=True)

    saved_files = sorted(
        glob.glob("chat_history/*.json"),
        reverse=True
    )

    if saved_files:

        for i, file in enumerate(saved_files):

            chat_name = os.path.basename(file).replace(".json", "")

            if st.button(f"📄 {chat_name}", key=f"chat_{i}"):

                with open(file, "r") as f:

                    st.session_state.messages = json.load(f)

                st.rerun()

    else:

        st.caption("No saved chats yet.")

    st.markdown("---")

    # AI Tools
    st.subheader("📂 AI Tools")

    uploaded_pdf = st.file_uploader(
        "Upload PDF",
        type=["pdf"]
    )

    if uploaded_pdf:

        pdf_text = read_pdf(uploaded_pdf)

        st.session_state.pdf_text = pdf_text

        st.success("✅ PDF Loaded!")

        with st.expander("📄 Preview PDF"):

            st.write(pdf_text[:1000])

    st.markdown("---")

    # About
    st.subheader("ℹ️ About")

    st.write("""
**Welcome to Ziggy AI**

Professional AI Assistant

Version **2.0**
""")
    # ---------------------------------------
# Main Header
# ---------------------------------------
col1, col2 = st.columns([1, 6])

with col1:
    st.image("assets/logo.png", width=80)

with col2:
    st.title("🤖 Ziggy AI")
    st.caption("Build • Learn • Create")


# ---------------------------------------
# PDF Status
# ---------------------------------------
if st.session_state.pdf_text:

    st.info("📄 PDF Loaded Successfully!")

    with st.expander("Preview PDF"):

        st.write(st.session_state.pdf_text[:1000])


# ---------------------------------------
# Welcome Screen
# ---------------------------------------
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
- 📄 PDF Documents

---

💡 **Try asking:**

- What is Artificial Intelligence?
- Explain Machine Learning.
- Help me write Python code.
- Teach me Git and GitHub.
- Summarize this PDF.

---

✨ Ziggy AI can help you learn, build and create amazing projects.
""")


# ---------------------------------------
# Display Chat History
# ---------------------------------------
for message in st.session_state.messages:

    avatar = "👤" if message["role"] == "user" else "🤖"

    with st.chat_message(message["role"], avatar=avatar):

        st.markdown(message["content"])

        if "time" in message:
            st.caption(f"🕒 {message['time']}")
            # ---------------------------------------
# Chat Input
# ---------------------------------------
prompt = st.chat_input("💬 Ask me anything...")

if prompt:

    current_time = datetime.now().strftime("%I:%M %p")

    # Display User Message
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)
        st.caption(f"🕒 {current_time}")

    # Save User Message
    st.session_state.messages.append(
        {
            "role": "user",
            "content": prompt,
            "time": current_time
        }
    )

    # Add PDF Context (if available)
    pdf_context = ""

    if st.session_state.pdf_text:
        pdf_context = f"""

PDF CONTENT:
{st.session_state.pdf_text[:12000]}
"""

    # System Prompt
    system_prompt = f"""
You are Ziggy AI.

You are a friendly, professional AI assistant.

Rules:
- Never introduce yourself as Gemini.
- Always say you are Ziggy AI.
- Be clear and helpful.
- If PDF content is available, answer using it first.
- If the answer is not in the PDF, use your general knowledge.

{pdf_context}

User Question:
{prompt}
"""

    try:

        with st.chat_message("assistant", avatar="🤖"):

            with st.spinner("🤖 Ziggy is thinking..."):

                response = model.generate_content(system_prompt)

                ai_response = response.text

                ai_time = datetime.now().strftime("%I:%M %p")

                st.markdown(ai_response)

                st.caption(f"🕒 {ai_time}")

                components.html(
                    f"""
                    <button
                        style="
                        background:#262730;
                        color:white;
                        border:none;
                        padding:10px;
                        border-radius:8px;
                        cursor:pointer;
                        "
                        onclick="
                        navigator.clipboard.writeText(`{ai_response}`);
                        this.innerHTML='✅ Copied!';
                        ">
                        📋 Copy Response
                    </button>
                    """,
                    height=55,
                )

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": ai_response,
                "time": ai_time
            }
        )

    except Exception as e:

      if "429" in str(e):

        st.warning("""
⚠️ Ziggy AI has reached the Gemini API free quota.

Please wait a little while and try again.
""")

    else:

        st.error("⚠️ Something went wrong. Please try again.")
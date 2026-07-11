from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io
from rag.pdf_loader import load_pdf
import streamlit as st
import google.generativeai as genai
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

# Try Streamlit Secrets first, then .env
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
except Exception:
    api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    st.error("❌ GOOGLE_API_KEY not found.")
    st.info("Local: Add it to your .env file.")
    st.info("Streamlit Cloud: Add it in Settings → Secrets.")
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
    
def create_pdf(chat_text):
    buffer = io.BytesIO()

    pdf = canvas.Canvas(buffer, pagesize=letter)

    pdf.setFont("Helvetica", 12)

    y = 750

    for line in chat_text.split("\n"):

        pdf.drawString(40, y, line)

        y -= 20

        if y < 40:
            pdf.showPage()
            pdf.setFont("Helvetica", 12)
            y = 750

    pdf.save()

    buffer.seek(0)

    return buffer
   
# ---------------------------------------
# Sidebar
# ---------------------------------------
with st.sidebar:

    st.title("🤖 Ziggy AI")

    st.markdown("---")

    # ---------------------------------------
    # AI Mode
    # ---------------------------------------
    st.subheader("🤖 AI Mode")

    ai_mode = st.selectbox(
        "Choose Mode",
        [
            "General Assistant",
            "Coding Assistant",
            "Career Coach",
            "Study Assistant",
            "PDF Assistant"
        ]
    )

    st.markdown("---")

    # ---------------------------------------
    # Clear Chat
    # ---------------------------------------
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()

    st.markdown("---")

    # ---------------------------------------
    # Download & Save Chat
    # ---------------------------------------
    if st.session_state.messages:

        chat_text = ""

        for msg in st.session_state.messages:

            sender = "👤 User" if msg["role"] == "user" else "🤖 Ziggy AI"

            chat_text += f"{sender} ({msg['time']})\n"
            chat_text += f"{msg['content']}\n"
            chat_text += "-" * 40 + "\n\n"

        pdf_file = create_pdf(chat_text) 

        st.download_button(
            label="📄 Download Chat (TXT)",
            data=chat_text,
            file_name="ziggy_chat.txt",
            mime="text/plain",
        )

        st.download_button(
            label="📕 Download Chat (PDF)",
            data=pdf_file,
            file_name="ziggy_chat.pdf",
            mime="application/pdf",
        )

        if st.button("💾 Save Chat"):

            os.makedirs("chat_history", exist_ok=True)

            filename = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

            with open(f"chat_history/{filename}.json", "w") as file:
                json.dump(st.session_state.messages, file, indent=4)

            st.success("✅ Chat Saved Successfully!")

    st.markdown("---")

    # ---------------------------------------
    # New Chat
    # ---------------------------------------
    if st.button("🆕 New Chat"):
        st.session_state.messages = []
        st.rerun()

    st.markdown("---")

    # ---------------------------------------
    # Saved Chats
    # ---------------------------------------
    st.subheader("📚 Saved Chats")

    search_chat = st.text_input(
        "🔍 Search Chats",
        placeholder="Type chat name..."
    )

    os.makedirs("chat_history", exist_ok=True)

    saved_files = sorted(
        glob.glob("chat_history/*.json"),
        reverse=True
    )

    found_chat = False

    if saved_files:

        for i, file in enumerate(saved_files):

            chat_name = os.path.basename(file).replace(".json", "")
            display_name = chat_name.replace("_", " ")

            if search_chat:
                if search_chat.lower() not in display_name.lower():
                    continue

            found_chat = True

            if st.button(f"📄 {display_name}", key=f"chat_{i}"):

                with open(file, "r") as f:
                    st.session_state.messages = json.load(f)

                st.rerun()

        if search_chat and not found_chat:
            st.info("🔍 No chats found.")

    else:
        st.caption("No saved chats yet.")

    st.markdown("---")

    # ---------------------------------------
    # AI Tools
    # ---------------------------------------
    st.subheader("📂 AI Tools")

    uploaded_pdf = st.file_uploader(
        "Upload PDF",
        type=["pdf"]
    )

    if uploaded_pdf:

        pdf_text = load_pdf(uploaded_pdf)

        st.session_state.pdf_text = pdf_text

        st.success("✅ PDF Loaded!")

        with st.expander("📄 Preview PDF"):   

         st.markdown("---")

    # ---------------------------------------
    # About
    # ---------------------------------------
    st.subheader("ℹ️ About")

    st.markdown("""
    ## 🤖 Ziggy AI

    Professional AI Assistant

    ### 📦 Version
    **2.0**

    ---

    ### 🛠 Built With

    - 🐍 Python
    - 🎈 Streamlit
    - 🤖 Google Gemini API
    - 📄 ReportLab

    ---

    ### 👩‍💻 Developer

    **Janani V**

    ---

    ### 📜 License

    MIT License

    ---

    Made with ❤️ using Python & Streamlit.
    """)
    # ---------------------------------------
    # Settings
    # ---------------------------------------
    st.markdown("---")
    st.subheader("⚙️ Settings")
    theme = st.selectbox(
    "🌙 Theme",
    ["System", "Light", "Dark"],
    key="theme_select"
)
    default_ai_mode = st.selectbox(
    "🤖 Default AI Mode",
    [
        "General Assistant",
        "Coding Assistant",
        "Career Coach",
        "Study Assistant",
        "PDF Assistant"
    ],
    key="default_ai_mode"
)
    # ---------------------------------------
    # Chat Preferences
    # ---------------------------------------

    show_timestamps = st.checkbox(
      "💬 Show Timestamps",
      value=True,
      key="show_timestamps"
)

    show_avatars = st.checkbox(
    "👤 Show Avatars",
    value=True,
    key="show_avatars"
)

    enable_animations = st.checkbox(
      "✨ Enable Animations",
      value=True,
      key="enable_animations"
)
    # ---------------------------------------
# Main Header
# ---------------------------------------
col1, col2 = st.columns([1, 6])

with col1:
    st.image("assets/logo.png", width=80)

with col2:
    st.title("🤖 Ziggy AI")
    st.caption("Build • Learn • Create")

st.markdown("---")

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


# -----------------------------
# Display Previous Messages
# -----------------------------
for message in st.session_state.messages:

    if show_avatars:
        avatar = "👤" if message["role"] == "user" else "🤖"
    else:
        avatar = None

    with st.chat_message(message["role"], avatar=avatar):

        st.markdown(message["content"])

        if show_timestamps:
            st.caption(f"🕒 {message['time']}")
            
# ---------------------------------------
# Chat Input
# ---------------------------------------
prompt = st.chat_input("💬 Ask me anything...")

if prompt:

    current_time = datetime.now().strftime("%I:%M %p")

    # Display User Message
    with st.chat_message(
        "user",
        avatar="👤" if show_avatars else None
    ):
        st.markdown(prompt)

        if show_timestamps:
            st.caption(f"🕒 {current_time}")

    # Save User Message
    st.session_state.messages.append(
        {
            "role": "user",
            "content": prompt,
            "time": current_time
        }
    )

    # PDF Context
    pdf_context = ""

    if st.session_state.pdf_text:
        pdf_context = f"""

PDF CONTENT:
{st.session_state.pdf_text[:12000]}
"""

    # System Prompt
    system_prompt = f"""
You are Ziggy AI.

You are a friendly professional AI assistant.

Rules:
- Never introduce yourself as Gemini.
- Always introduce yourself as Ziggy AI.
- Be clear and helpful.
- If PDF content exists, answer using it first.
- Otherwise answer normally.

{pdf_context}

User Question:
{prompt}
"""

    # AI Response
    try:

        with st.chat_message(
            "assistant",
            avatar="🤖" if show_avatars else None
        ):

            with st.spinner("🤖 Ziggy is thinking..."):

                response = model.generate_content(system_prompt)

                ai_response = response.text

                ai_time = datetime.now().strftime("%I:%M %p")

                st.markdown(ai_response)

                if show_timestamps:
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

        # Save AI Message
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
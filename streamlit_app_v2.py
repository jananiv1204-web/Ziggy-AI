import os
import io
import json
import glob

from datetime import datetime

import streamlit as st
import streamlit.components.v1 as components

from dotenv import load_dotenv

import google.generativeai as genai

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

from image_helper import load_image
from rag.pdf_loader import load_pdf
from rag.chunking import split_text
from rag.vector_store import create_vector_store
from rag.retrieval import retrieve_chunks
# =====================================
# PAGE CONFIG
# =====================================

st.set_page_config(
    page_title="🤖 Ziggy AI",
    page_icon="🤖",
    layout="wide"
)
# =====================================
# LOAD ENVIRONMENT
# =====================================

load_dotenv()

try:
    api_key = st.secrets["GOOGLE_API_KEY"]
except Exception:
    api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    st.error("❌ GOOGLE_API_KEY not found.")
    st.stop()

genai.configure(api_key=api_key)

model = genai.GenerativeModel("gemini-2.5-flash")
# =====================================
# SESSION STATE
# =====================================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "pdf_text" not in st.session_state:
    st.session_state.pdf_text = ""

if "vector_store" not in st.session_state:
    st.session_state.vector_store = None

if "ai_mode" not in st.session_state:
    st.session_state.ai_mode = "General Assistant"

if "theme" not in st.session_state:
    st.session_state.theme = "System"

if "show_timestamps" not in st.session_state:
    st.session_state.show_timestamps = True

if "show_avatars" not in st.session_state:
    st.session_state.show_avatars = True
# =====================================
# CREATE PDF FUNCTION
# =====================================

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
# =====================================
# SIDEBAR
# =====================================

with st.sidebar:

    st.title("🤖 Ziggy AI")
    st.caption("Your Personal AI Assistant")

    st.markdown("---")

    # ===========================
    # AI MODE
    # ===========================

    st.subheader("🤖 AI Mode")

    st.session_state.ai_mode = st.selectbox(
        "Choose Mode",
        [
            "General Assistant",
            "Coding Assistant",
            "Career Coach",
            "Study Assistant",
            "PDF Assistant"
        ],
        index=[
            "General Assistant",
            "Coding Assistant",
            "Career Coach",
            "Study Assistant",
            "PDF Assistant"
        ].index(st.session_state.ai_mode)
    )

    st.markdown("---")

    # ===========================
    # CHAT BUTTONS
    # ===========================

    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()

    if st.button("🆕 New Chat"):
        st.session_state.messages = []
        st.rerun()

    st.markdown("---")

    # ===========================
    # DOWNLOAD CHAT
    # ===========================

    if st.session_state.messages:

        chat_text = ""

        for msg in st.session_state.messages:

            sender = "👤 User" if msg["role"] == "user" else "🤖 Ziggy AI"

            chat_text += f"{sender} ({msg['time']})\n"
            chat_text += msg["content"] + "\n"
            chat_text += "-" * 40 + "\n"

        pdf = create_pdf(chat_text)

        st.download_button(
            "📄 Download Chat (TXT)",
            chat_text,
            "ziggy_chat.txt"
        )

        st.download_button(
            "📕 Download Chat (PDF)",
            pdf,
            "ziggy_chat.pdf"
        )

        if st.button("💾 Save Chat"):

            os.makedirs("chat_history", exist_ok=True)

            filename = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

            with open(f"chat_history/{filename}.json", "w") as f:
                json.dump(st.session_state.messages, f, indent=4)

            st.success("✅ Chat Saved!")

    st.markdown("---")

    # ===========================
    # SAVED CHATS
    # ===========================

    st.subheader("📚 Saved Chats")

    search = st.text_input(
        "🔍 Search Chats",
        placeholder="Type chat name..."
    )

    os.makedirs("chat_history", exist_ok=True)

    files = sorted(
        glob.glob("chat_history/*.json"),
        reverse=True
    )

    found = False

    for i, file in enumerate(files):

        display = os.path.basename(file).replace(".json", "")

        if search.lower() not in display.lower():
            continue

        found = True

        if st.button(f"📄 {display}", key=f"chat{i}"):

            with open(file) as f:
                st.session_state.messages = json.load(f)

            st.rerun()

    if search and not found:
        st.info("No chats found.")

    st.markdown("---")

    # ===========================
    # PDF ASSISTANT
    # ===========================

    st.subheader("📄 PDF Assistant ")

    uploaded_files = st.file_uploader(
        "Upload PDF Files",
        type=["pdf"],
        accept_multiple_files=True,
        key="pdf_upload"
    )
    st.markdown("### 🖼 Upload Image")

    uploaded_image = st.file_uploader(
        "Choose an image",
        type=["png", "jpg", "jpeg"],
        key="image_uploader"
)
    if uploaded_image is not None:
        st.session_state.uploaded_image = uploaded_image
    if "uploaded_image" not in st.session_state:
        st.session_state.uploaded_image = None
    if uploaded_image is not None:

        image = load_image(uploaded_image)

        st.image(
        image,
        caption="Uploaded Image",
        use_container_width=True
    )
    st.success("✅ Image uploaded successfully!")
    image = load_image(uploaded_image)
    
    if image is not None:
        st.image(
            image,
            caption="Uploaded Image",
            use_container_width=True
    )
    if uploaded_files:

        all_text = ""

        for pdf in uploaded_files:

            try:
                all_text += load_pdf(pdf) + "\n\n"

            except Exception as e:
                st.error(f"{pdf.name}: {e}")

        st.session_state.pdf_text = all_text

        chunks = split_text(all_text)

        st.session_state.vector_store = create_vector_store(chunks)

        st.success(f"✅ {len(uploaded_files)} PDF(s) Loaded!")

        with st.expander("📄 Preview PDF"):

            st.write(all_text[:2500])

        if st.button("🗑️ Clear PDFs"):

            st.session_state.pdf_text = ""

            st.session_state.vector_store = None

            st.rerun()

    st.markdown("---")

    # ===========================
    # SETTINGS
    # ===========================

    st.subheader("⚙️ Settings")

    st.session_state.theme = st.selectbox(
        "🌙 Theme",
        ["System", "Light", "Dark"]
    )

    st.session_state.ai_mode = st.selectbox(
        "🤖 Default AI Mode",
        [
            "General Assistant",
            "Coding Assistant",
            "Career Coach",
            "Study Assistant",
            "PDF Assistant"
        ],
        index=[
            "General Assistant",
            "Coding Assistant",
            "Career Coach",
            "Study Assistant",
            "PDF Assistant"
        ].index(st.session_state.ai_mode),
        key="default_ai_mode"
    )

    st.session_state.show_timestamps = st.checkbox(
        "💬 Show Timestamps",
        value=st.session_state.show_timestamps
    )

    st.session_state.show_avatars = st.checkbox(
        "👤 Show Avatars",
        value=st.session_state.show_avatars
    )

    st.checkbox(
        "✨ Enable Animations",
        value=True
    )

    st.markdown("---")

    # ===========================
    # ABOUT
    # ===========================

    st.subheader("ℹ️ About")

    st.markdown("""

## 🤖 Ziggy AI

Professional AI Assistant

### 📦 Version
**2.1**

---

### 🛠 Built With

- 🐍 Python
- 🎈 Streamlit
- 🤖 Google Gemini API
- 📄 ReportLab
- 🧠 RAG (FAISS)

---

### 👩‍💻 Developer

**Janani V**

---

### 📜 License

MIT License

---

Made with ❤️ using Python & Streamlit.

""")
# =====================================
# MAIN HEADER
# =====================================

col1, col2 = st.columns([1, 6], vertical_alignment="center")

with col1:

    if os.path.exists("assets/logo.png"):
        st.image("assets/logo.png", width=90)
    else:
        st.markdown("## 🤖")

with col2:

    st.title("🤖 Ziggy AI")
    st.caption("Build • Learn • Create with AI")

st.markdown("---")

# =====================================
# PDF STATUS
# =====================================

if st.session_state.pdf_text:

    st.success("📄 PDF Knowledge Base Ready")

else:

    st.info("Upload one or more PDFs to enable RAG.")
# =====================================
# WELCOME SCREEN
# =====================================

if len(st.session_state.messages) == 0:

    st.markdown("""
# 👋 Welcome to Ziggy AI

### Your Intelligent AI Assistant

I'm here to help you with:

- 🤖 Artificial Intelligence
- 💻 Programming
- 🐍 Python
- 📄 PDF Question Answering (RAG)
- 📊 Machine Learning
- 🎓 Study Support
- 🚀 Career Guidance

---

### 🌟 Try asking:

• Explain Python decorators.

• Help me prepare for an interview.

• Summarize my uploaded PDF.

• Create a C++ program.

• Explain AI in simple words.

---

💜 Upload a PDF and ask questions directly from it!

Built with ❤️ using Python, Streamlit & Google Gemini.
""")
# =====================================
# DISPLAY CHAT HISTORY
# =====================================

for message in st.session_state.messages:

    avatar = None

    if st.session_state.show_avatars:

        avatar = "👤" if message["role"] == "user" else "🤖"

    with st.chat_message(
        message["role"],
        avatar=avatar
    ):

        st.markdown(message["content"])

        if st.session_state.show_timestamps:

            st.caption(f"🕒 {message['time']}")
ZIGGY_PERSONALITY = """
You are Ziggy AI.

You are friendly, warm, professional and supportive.

Your personality:

• Always greet users naturally.
• Talk like a real AI assistant.
• Never sound robotic.
• Be encouraging.
• Explain things clearly.
• Use emojis occasionally 😊
• Remember the conversation naturally.
• If someone simply says "Hi", "Hello", "Hey", introduce yourself warmly.
• If the user uploads PDFs, use them as your main knowledge source.
• If the answer is not found inside the PDF, politely say you couldn't find it.
• Never invent facts.

Your name is Ziggy AI.
"""
# =====================================
# CHAT INPUT
# =====================================

prompt = st.chat_input("💬 Ask Ziggy AI anything...")

if prompt:

    current_time = datetime.now().strftime("%I:%M %p")

    # ----------------------------
    # Show User Message
    # ----------------------------

    with st.chat_message("user", avatar="👤"):

        st.markdown(prompt)

        if st.session_state.show_timestamps:

            st.caption(f"🕒 {current_time}")

    st.session_state.messages.append(
        {
            "role": "user",
            "content": prompt,
            "time": current_time
        }
    )
# =====================================
# AI MODE PROMPTS
# =====================================
ai_mode = st.session_state.ai_mode
mode_instruction = ""

if ai_mode == "General Assistant":

    mode_instruction = """
You are Ziggy AI, a friendly and intelligent personal assistant.
Answer naturally, warmly and conversationally.
"""

elif ai_mode == "Coding Assistant":

    mode_instruction = """
You are an expert software engineer.

Help with:

• Python
• C
• C++
• Java
• HTML
• CSS
• JavaScript
• SQL
• AI & Machine Learning

Always explain code step-by-step.

Write clean, professional code.
"""

elif ai_mode == "Career Coach":

    mode_instruction = """
You are an experienced career mentor.

Help users with:

• Resume building
• LinkedIn profile
• Placements
• Internship guidance
• Interview preparation
• Career roadmap

Be motivating and supportive.
"""

elif ai_mode == "Study Assistant":

    mode_instruction = """
You are an excellent teacher.

Explain concepts in simple language.

Teach step-by-step.

Use examples wherever possible.

Encourage the student to keep learning.
"""

elif ai_mode == "PDF Assistant":

    mode_instruction = """
You are a PDF Assistant.

Answer ONLY using the uploaded PDF whenever possible.

If the answer is not present inside the PDF, politely say:

"I couldn't find that information in the uploaded PDF."

Never make up information.
"""
# =====================================
# PDF CONTEXT
# =====================================

context = ""

if st.session_state.vector_store is not None:

    try:
        context = retrieve_chunks(
            st.session_state.vector_store,
            prompt
        )

    except Exception:
        context = ""
# =====================================
# BUILD CONVERSATION HISTORY
# =====================================

history = ""

for msg in st.session_state.messages[-4:]:

    speaker = "User" if msg["role"] == "user" else "Ziggy AI"

    history += f"{speaker}: {msg['content']}\n"

# =====================================
# SYSTEM PROMPT
# =====================================

system_prompt = f"""
{ZIGGY_PERSONALITY}

Current AI Mode:
{ai_mode}

Mode Instructions:
{mode_instruction}

Conversation History:
{history}

Document Context:
{context}

Current User Question:
{prompt}

Uploaded Image:
{"Yes" if st.session_state.uploaded_image else "No"}

Instructions:

1. Answer naturally and conversationally.
2. Maintain Ziggy AI's friendly personality.
3. Use emojis naturally when appropriate.
4. If AI Mode is Coding Assistant, behave like a senior software engineer.
5. If AI Mode is Career Coach, behave like an experienced mentor.
6. If AI Mode is Study Assistant, explain topics step-by-step.
7. If AI Mode is PDF Assistant and document context exists, answer ONLY from the PDF.
8. If the answer is not present in the uploaded PDF, respond exactly:

"I couldn't find that information in the uploaded PDF."

9. Never fabricate information.
10. Keep responses clear, helpful and engaging.
"""
# =====================================
# GENERATE RESPONSE
# =====================================

with st.chat_message("assistant", avatar="🤖"):

    with st.spinner("🧠 Ziggy is analyzing your request..."):

        try:
            if st.session_state.uploaded_image is not None:

                image = load_image(st.session_state.uploaded_image)

                response = model.generate_content(
                    [
                        system_prompt,
                        image
                    ]
                )

            else:

                response = model.generate_content(system_prompt)

            if hasattr(response, "text") and response.text:
                ai_response = response.text
            else:
                ai_response = "⚠️ I couldn't generate a response. Please try again."

        except Exception as e:

            error = str(e)

            if "ResourceExhausted" in error or "429" in error:
                ai_response = """
⚠️ **Gemini API usage limit reached**

The free Google Gemini API quota has been exceeded.

Please wait a while and try again later.
"""

            else:
                ai_response = f"⚠️ Unexpected Error:\n\n{error}"

    st.markdown(ai_response)

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

    ai_time = datetime.now().strftime("%I:%M %p")

    if st.session_state.show_timestamps:
        st.caption(f"🕒 {ai_time}")

st.session_state.messages.append(
    {
        "role": "assistant",
        "content": ai_response,
        "time": ai_time
    }
)
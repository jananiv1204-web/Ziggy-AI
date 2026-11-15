import os
import io
import json
import glob
import textwrap

from datetime import datetime

import streamlit as st
import streamlit.components.v1 as components

from speech_to_text import save_audio
from text_to_speech import text_to_speech
from streamlit_mic_recorder import mic_recorder
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, ".env")

load_dotenv(ENV_PATH, override=True)

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

# Safety net: these always exist, so NameError cannot happen
ai_response = ""
audio_file = None

# =====================================
# LOAD ENVIRONMENT
# =====================================

load_dotenv()

try:
    api_key = st.secrets["GOOGLE_API_KEY"]
except Exception:
    api_key = os.getenv("GOOGLE_API_KEY")
    st.write("DEBUG: .env path:", ENV_PATH)
    st.write("DEBUG: API key loaded:", bool(api_key))

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

if "pdf_signature" not in st.session_state:
    st.session_state.pdf_signature = None

if "ai_mode" not in st.session_state:
    st.session_state.ai_mode = "General Assistant"

if "theme" not in st.session_state:
    st.session_state.theme = "System"

if "show_timestamps" not in st.session_state:
    st.session_state.show_timestamps = True

if "show_avatars" not in st.session_state:
    st.session_state.show_avatars = True

if "voice_status" not in st.session_state:
    st.session_state.voice_status = "Idle"

# =====================================
# IMAGE SESSION STATE
# =====================================

if "uploaded_image" not in st.session_state:
    st.session_state.uploaded_image = None

if "uploaded_image_file" not in st.session_state:
    st.session_state.uploaded_image_file = None

# =====================================
# AI MODE LIST + SYNC CALLBACKS
# =====================================

AI_MODES = [
    "General Assistant",
    "Coding Assistant",
    "Career Coach",
    "Study Assistant",
    "PDF Assistant"
]


def sync_mode_from_main():
    st.session_state.ai_mode = st.session_state["main_mode_select"]
    st.session_state["default_ai_mode"] = st.session_state.ai_mode


def sync_mode_from_default():
    st.session_state.ai_mode = st.session_state["default_ai_mode"]
    st.session_state["main_mode_select"] = st.session_state.ai_mode


# =====================================
# CREATE PDF FUNCTION
# =====================================

def create_pdf(chat_text):

    buffer = io.BytesIO()

    pdf = canvas.Canvas(buffer, pagesize=letter)

    pdf.setFont("Helvetica", 12)

    y = 750

    for raw_line in chat_text.split("\n"):

        # Remove characters Helvetica cannot draw (emojis etc.)
        clean_line = raw_line.encode("latin-1", "ignore").decode("latin-1")

        wrapped_lines = textwrap.wrap(clean_line, width=90) or [""]

        for line in wrapped_lines:

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
    st.markdown("### 🎤 Voice Assistant")

    st.info(f"Status: {st.session_state.voice_status}")

    st.selectbox(
        "Choose Mode",
        AI_MODES,
        index=AI_MODES.index(st.session_state.ai_mode),
        key="main_mode_select",
        on_change=sync_mode_from_main
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
            "ziggy_chat.pdf",
            mime="application/pdf"
        )

        if st.button("💾 Save Chat"):

            os.makedirs("chat_history", exist_ok=True)

            filename = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

            with open(
                f"chat_history/{filename}.json", "w", encoding="utf-8"
            ) as f:
                json.dump(
                    st.session_state.messages,
                    f,
                    indent=4,
                    ensure_ascii=False
                )

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

            with open(file, encoding="utf-8") as f:
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

    uploaded_image = st.file_uploader(
        "🖼 Upload Image",
        type=["png", "jpg", "jpeg"],
        key="image_upload"
    )

    st.markdown("---")
    st.subheader("🎤 Voice Input")

    st.session_state.voice_status = "🎤 Listening..."

    audio = mic_recorder(
        start_prompt="🎤 Start Recording",
        stop_prompt="⏹ Stop Recording",
        key="voice_recorder"
    )

    if audio:

        st.session_state.voice_status = "🧠 Thinking..."

        audio_path = save_audio(audio)

        st.success("✅ Voice recorded successfully!")

        st.write(audio_path)

        st.info("🎤 Click Start Recording and speak clearly.")

        st.success("✅ Response completed")

        st.markdown("## 🧠 Thinking...")

    if uploaded_image is not None:

        image = load_image(uploaded_image)

        st.session_state.uploaded_image = image
        st.session_state.uploaded_image_file = uploaded_image

        st.image(
            image,
            caption="Uploaded Image",
            use_container_width=True
        )

    if st.button("🗑️ Clear Image"):

        st.session_state.uploaded_image = None

        st.rerun()

    if uploaded_files:

        signature = [(f.name, f.size) for f in uploaded_files]

        # Only rebuild the vector store when the PDFs change
        if st.session_state.pdf_signature != signature:

            all_text = ""

            for pdf_file in uploaded_files:

                try:
                    all_text += load_pdf(pdf_file) + "\n\n"

                except Exception as e:
                    st.error(f"{pdf_file.name}: {e}")

            st.session_state.pdf_text = all_text

            chunks = split_text(all_text)

            st.session_state.vector_store = create_vector_store(chunks)

            st.session_state.pdf_signature = signature

        st.success(f"✅ {len(uploaded_files)} PDF(s) Loaded!")

        with st.expander("📄 Preview PDF"):

            st.write(st.session_state.pdf_text[:2500])

        if st.button("🗑️ Clear PDFs"):

            st.session_state.pdf_text = ""

            st.session_state.vector_store = None

            st.session_state.pdf_signature = None

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

    st.selectbox(
        "🤖 Default AI Mode",
        AI_MODES,
        index=AI_MODES.index(st.session_state.ai_mode),
        key="default_ai_mode",
        on_change=sync_mode_from_default
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

# =====================================
# ZIGGY PERSONALITY
# =====================================

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

    # PDF Assistant Check
    if (
        st.session_state.ai_mode == "PDF Assistant"
        and st.session_state.vector_store is None
    ):
        st.warning("📄 Please upload a PDF first.")
        st.stop()

    # Image Check
    if (
        "image" in prompt.lower()
        and st.session_state.uploaded_image is None
    ):
        st.warning("🖼 Please upload an image first.")
        st.stop()

    current_time = datetime.now().strftime("%I:%M %p")

    # Show User Message
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

        if st.session_state.show_timestamps:
            st.caption(f"🕒 {current_time}")

    st.session_state.messages.append({
        "role": "user",
        "content": prompt,
        "time": current_time
    })

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
        Python, C, C++, Java, HTML, CSS, JavaScript,
        SQL, AI and Machine Learning.

        Always explain code step-by-step.
        Write clean, professional code.
        """

    elif ai_mode == "Career Coach":

        mode_instruction = """
        You are an experienced career mentor.

        Help users with:
        Resume building, LinkedIn profiles, placements,
        internship guidance, interview preparation
        and career roadmaps.

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

        Answer ONLY using the uploaded PDF.

        If the answer is not present inside the PDF, say:

        I couldn't find that information in the uploaded PDF.

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
        except Exception as e:
            st.warning(f"PDF retrieval error: {e}")

    # =====================================
    # BUILD CONVERSATION HISTORY
    # =====================================

    history = ""

    for msg in st.session_state.messages[-6:]:

        speaker = (
            "User" if msg["role"] == "user"
            else "Ziggy AI"
        )

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

    Instructions:

    1. Answer naturally and conversationally.
    2. Maintain Ziggy AI's friendly personality.
    3. Use emojis naturally when appropriate.
    4. For Coding Assistant, behave like a senior software engineer.
    5. For Career Coach, behave like an experienced mentor.
    6. For Study Assistant, explain topics step-by-step.
    7. For PDF Assistant, answer only from the PDF.
    8. If information is missing from the PDF, say:
       "I couldn't find that information in the uploaded PDF."
    9. Never fabricate information.
    10. Keep responses clear and helpful.
    """

    # =====================================
    # GENERATE RESPONSE
    # =====================================

    # Always defined BEFORE the try block
    ai_response = "⚠️ Ziggy couldn't generate a response. Please try again."

    audio_file = None

    with st.chat_message("assistant", avatar="🤖"):

        with st.spinner("🤖 Ziggy AI is thinking..."):

            try:

                # IMAGE + TEXT GENERATION
                if st.session_state.uploaded_image is not None:

                    image = st.session_state.uploaded_image

                    response = model.generate_content(
                        [system_prompt, image]
                    )

                # TEXT GENERATION
                else:

                    response = model.generate_content(
                        system_prompt
                    )

                # EXTRACT AI RESPONSE
                if hasattr(response, "text") and response.text:

                    ai_response = response.text

                else:

                    ai_response = (
                        "⚠️ Gemini returned an empty response. "
                        "Please try again."
                    )

                # TEXT TO SPEECH
                try:

                    audio_file = text_to_speech(ai_response)

                    st.session_state.voice_status = "🔊 Speaking..."

                except Exception as speech_error:

                    st.warning(
                        f"Text-to-speech error: {speech_error}"
                    )

            except Exception as e:

                error = str(e)

                if "ResourceExhausted" in error or "429" in error:

                    ai_response = """
                    ⚠️ **Gemini API usage limit reached**

                    Please wait a while and try again later.
                    """

                else:

                    ai_response = (
                        f"⚠️ Unexpected Error:\n\n{error}"
                    )

        # SAVE RESPONSE
        st.session_state["ai_response"] = ai_response

        # DISPLAY RESPONSE
        st.markdown(ai_response)

        # PLAY AUDIO
        if audio_file:

            st.audio(audio_file)

    # SAVE ASSISTANT MESSAGE
    response_time = datetime.now().strftime("%I:%M %p")

    st.session_state.messages.append({
        "role": "assistant",
        "content": ai_response,
        "time": response_time
    })

    st.session_state.voice_status = "✅ Idle"
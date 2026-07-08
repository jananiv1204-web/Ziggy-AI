print("Hello AI Engineer!")
import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Read API key
api_key = os.getenv("GOOGLE_API_KEY")

# Configure Gemini
genai.configure(api_key=api_key)

# Create model
model = genai.GenerativeModel("gemini-2.5-flash")

print("🤖 AI Chatbot Started!")
print("Type 'exit' to stop.\n")

while True:
    user_input = input("You: ").strip()

    if user_input.lower() == "exit":
        print("Goodbye!")
        break

    if not user_input:
        print("Please type a question.")
        continue

    if user_input.lower() == "thank you":
        print("AI: You're welcome! 😊")
        continue

    if user_input.lower() in ["hi", "hello", "hey"]:
        print("AI: Hello! How can I help you today? 👋")
        continue

    response = model.generate_content(user_input)
    print("AI:", response.text)
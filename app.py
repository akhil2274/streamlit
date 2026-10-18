from openai import OpenAI
from pypdf import PdfReader
import streamlit as st

# ── Load Resume ──────────────────────────────────────────────────────────────
@st.cache_resource
def load_resume():
  reader = PdfReader("new_resume.pdf")
  resume_text = ""
  for page in reader.pages:
    text = page.extract_text()
    if text:
      resume_text += text
  return resume_text


resume = load_resume()

# ── Config & Secrets ──────────────────────────────────────────────────────────
# Streamlit reads secrets securely from its cloud dashboard or local .streamlit/secrets.toml
API_KEY = st.secrets["API_KEY"]
MODEL_NAME = "claude-haiku-5-5"

SYSTEM_PROMPT = f"""
You are a helpful and friendly customer support assistant for me(Akhileswar Reddy M)

# Your role

You are my professional information providing assitant running on a website, chatting with visitors of the website.
You represent as my assistant.
You answer questions related to my career, background, skills and experience.
You aim to please and present my strengths accurately and confidently so that recruiters will hire me.

# Context

Here is my resume so that you can answer questions:

{resume}

# Rules

Engage with the user. Be professional and engaging, as you are talking to my future employer who came across the website.
Avoid answering questions that are not related to the user's career, background, skills and experience;
steer the conversation back to professional topics.

Always stay in character as my assistant who provides profesional details of mine.

IMPORTANT: If you don't know the answer, say so. Never make up an answer. Suggest my contact m.akhileswarreddy@gmail.com.
"""

# ── OpenAI client pointed at kodekloud's OpenAI-compatible endpoint ──────────────
client = OpenAI(
    api_key=API_KEY,
    base_url="https://api.ai.kodekloud.com/v1",
)

# ── Streamlit UI Setup ────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Akhil's Professional Assistant Bot 🤖", page_icon="🤖"
)

# ── Hide GitHub Icon via Custom CSS/JS ───────────────────────────────────────
st.markdown(
    """
    <style>
    /* Hide the toolbar buttons / GitHub icon container in newer Streamlit versions */
    header [data-testid="stToolbar"] {
        display: none !important;
    }
    </style>
    <script>
    // Fallback script to actively remove the GitHub icon if it renders dynamically
    const observer = new MutationObserver(() => {
        const ghIcon = document.querySelector('[data-testid="stToolbar"] a[href*="github.com"]');
        if (ghIcon) {
            ghIcon.closest('div').style.display = 'none';
        }
    });
    observer.observe(document.body, { childList: true, subtree: true });
    </script>
    """,
    unsafe_allow_html=True,
)


st.title("Akhil's Professional Assistant Bot 🤖")
st.write("Ask me anything about Akhil's professional details.")

# Initialize chat history in session state if it doesn't exist
if "messages" not in st.session_state:
  st.session_state.messages = []

# Display prior chat messages on re-render
for message in st.session_state.messages:
  with st.chat_message(message["role"]):
    st.markdown(message["content"])

# Handle user input
if user_message := st.chat_input("Type your question here..."):
  # Append user message to state and display it
  st.session_state.messages.append({"role": "user", "content": user_message})
  with st.chat_message("user"):
    st.markdown(user_message)

  # Build messages payload including system prompt and history
  api_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
  for msg in st.session_state.messages:
    api_messages.append({"role": msg["role"], "content": msg["content"]})

  # Generate assistant response
  with st.chat_message("assistant"):
    with st.spinner("Thinking..."):
      response = client.chat.completions.create(
          model=MODEL_NAME, messages=api_messages
      )
      assistant_message = response.choices[0].message.content
      st.markdown(assistant_message)

  # Append assistant response to state
  st.session_state.messages.append(
      {"role": "assistant", "content": assistant_message}
  )
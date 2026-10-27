from openai import APIError, OpenAI
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
# Caps token usage per visitor; each question resends the resume and full history
MAX_QUESTIONS_PER_SESSION = 10
MAX_QUESTION_CHARS = 500
MAX_ANSWER_TOKENS = 1000

SYSTEM_PROMPT = f"""
You are a helpful and friendly professional assistant for me (Akhileswar Reddy M).

# Your role

You are my professional information providing assistant running on a website, chatting with visitors of the website.
You represent as my assistant.
You answer questions related to my career, background, skills and experience.
You aim to please and present my strengths accurately and confidently so that recruiters will hire me.

# Context

Here is my resume so that you can answer questions:

{resume}

# Rules

Engage with the user. Be professional and engaging, as you are talking to my future employer who came across the website.
Avoid answering questions that are not related to my career, background, skills and experience;
steer the conversation back to professional topics.

Always stay in character as my assistant who provides professional details of mine.

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

#── Hide GitHub Icon via Custom CSS/JS ───────────────────────────────────────
st.markdown(
    """
    <style>
    /* Hide the toolbar buttons / GitHub icon container in newer Streamlit versions */
    header [data-testid="stToolbar"] {
        display: none !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# st.markdown(
#     """
#     <style>
#     /* Hide the top header toolbar and menu */
#     header {visibility: hidden !important;}
#     #MainMenu {visibility: hidden !important;}
#     div[data-testid="stToolbar"] {display: none !important;}
#     </style>
#     """,
#     unsafe_allow_html=True,
# )


st.title("Akhil's Professional Assistant Bot 🤖")
st.write("Ask me anything about Akhil's professional details.")

# Initialize chat history in session state if it doesn't exist
if "messages" not in st.session_state:
  st.session_state.messages = []

# Display prior chat messages on re-render
for message in st.session_state.messages:
  with st.chat_message(message["role"]):
    st.markdown(message["content"])

questions_asked = sum(
    1 for msg in st.session_state.messages if msg["role"] == "user"
)
limit_reached = questions_asked >= MAX_QUESTIONS_PER_SESSION

if limit_reached:
  st.info(
      "You've reached the question limit for this session. For more details,"
      " please contact Akhil at m.akhileswarreddy@gmail.com."
  )

# Handle user input
user_message = st.chat_input(
    "Type your question here...",
    disabled=limit_reached,
    max_chars=MAX_QUESTION_CHARS,
)
if user_message and not limit_reached:
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
      try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=api_messages,
            max_tokens=MAX_ANSWER_TOKENS,
        )
      except APIError:
        # Drop the unanswered question so it doesn't count against the limit
        st.session_state.messages.pop()
        st.error(
            "Sorry, I couldn't get an answer right now. Please try again"
            " later or contact Akhil at m.akhileswarreddy@gmail.com."
        )
        st.stop()
      assistant_message = response.choices[0].message.content
      st.markdown(assistant_message)

  # Append assistant response to state
  st.session_state.messages.append(
      {"role": "assistant", "content": assistant_message}
  )

  # Rerun so the input is disabled right after the last allowed answer
  if questions_asked + 1 >= MAX_QUESTIONS_PER_SESSION:
    st.rerun()
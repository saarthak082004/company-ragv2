import streamlit as st
import os
import time
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone
from groq import Groq

from database import (
    signup_user,
    login_user,
    create_new_chat,
    get_user_chats,
    get_chat_messages,
    save_message,
    update_chat_title
)

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="Company Knowledge Assistant",
    page_icon="🏢",
    layout="wide"
)

# ---------------- LOAD ENV ----------------
load_dotenv()
pinecone_key = os.getenv("PINECONE_API_KEY")
groq_key = os.getenv("GROQ_API_KEY")

# ---------------- SYSTEM PROMPT ----------------
def load_system_prompt():
    try:
        with open("prompts/system_prompt.txt", "r", encoding="utf-8") as f:
            return f.read()
    except:
        return "You are a professional company knowledge assistant."

system_prompt = load_system_prompt()

# ---------------- AUTO COMPANY DETECTION ----------------
def detect_company(email):
    email = email.lower().strip()

    if email.endswith("@synise.com"):
        return "Synise"
    elif email.endswith("@publiccounsel.org"):
        return "Public Counsel"
    else:
        return None

# ---------------- LOAD MODELS ----------------
@st.cache_resource
def load_models():
    embed_model = SentenceTransformer("all-mpnet-base-v2")
    groq_client = Groq(api_key=groq_key)
    return embed_model, groq_client

embed_model, groq_client = load_models()

# ---------------- DYNAMIC INDEX LOADER ----------------
def get_company_index(company):
    pc = Pinecone(api_key=pinecone_key)

    if company == "Synise":
        return pc.Index("syniseindex")
    elif company == "Public Counsel":
        return pc.Index("publiccounselindex")
    else:
        return None

# ---------------- SESSION INIT ----------------
for key, default in {
    "logged_in": False,
    "user_email": "",
    "user_name": "",
    "company": "",
    "current_chat": None,
    "messages": [],
    "model": "llama-3.3-70b-versatile"
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ---------------- AUTH SCREEN ----------------
if not st.session_state.logged_in:

    col1, col2, col3 = st.columns([1, 1, 1])

    with col2:
        st.title("🏢 Company AI Assistant")

        tab1, tab2 = st.tabs(["Login", "Signup"])

        # ---------------- LOGIN ----------------
        with tab1:
            email_l = st.text_input("Work Email", key="login_email")
            password_l = st.text_input("Password", type="password", key="login_password")

            if st.button("Login", use_container_width=True):
                user = login_user(email_l, password_l)

                if user:
                    detected_company = detect_company(email_l)

                    if not detected_company:
                        st.error("Invalid company email domain.")
                    elif detected_company != user[1]:
                        st.error("Company mismatch detected.")
                    else:
                        st.session_state.logged_in = True
                        st.session_state.user_email = email_l
                        st.session_state.user_name = user[0]
                        st.session_state.company = user[1]

                        chats = get_user_chats(email_l)
                        if chats:
                            st.session_state.current_chat = chats[0][0]
                            st.session_state.messages = get_chat_messages(chats[0][0])
                        else:
                            st.session_state.current_chat = create_new_chat(
                                email_l,
                                user[1]
                            )
                            st.session_state.messages = []

                        st.rerun()
                else:
                    st.error("Invalid credentials")

        # ---------------- SIGNUP ----------------
        with tab2:
            name_s = st.text_input("Full Name", key="signup_name")
            email_s = st.text_input("Work Email", key="signup_email")
            password_s = st.text_input("Password", type="password", key="signup_password")

            if st.button("Create Account", use_container_width=True):

                detected_company = detect_company(email_s)

                if not detected_company:
                    st.error("Only official company emails allowed.")
                elif signup_user(name_s, email_s, password_s, detected_company):
                    st.session_state.logged_in = True
                    st.session_state.user_email = email_s
                    st.session_state.user_name = name_s
                    st.session_state.company = detected_company
                    st.session_state.current_chat = create_new_chat(
                        email_s,
                        detected_company
                    )
                    st.session_state.messages = []
                    st.rerun()
                else:
                    st.error("Email already registered")

    st.stop()

# ---------------- SIDEBAR ----------------
st.sidebar.markdown(f"## 👤 {st.session_state.user_name}")
st.sidebar.markdown(f"🏢 Company: **{st.session_state.company}**")

st.sidebar.selectbox(
    "Choose AI Model",
    [
        "llama-3.3-70b-versatile",
        "openai/gpt-oss-120b",
        "llama-3.1-8b-instant"
    ],
    key="model"
)

if st.sidebar.button("➕ New Chat"):
    chat_id = create_new_chat(
        st.session_state.user_email,
        st.session_state.company
    )
    st.session_state.current_chat = chat_id
    st.session_state.messages = []
    st.rerun()

st.sidebar.markdown("### 💬 Chats")

chats = get_user_chats(st.session_state.user_email)
for chat_id, title in chats[:15]:
    if st.sidebar.button(title, key=f"chat_{chat_id}"):
        st.session_state.current_chat = chat_id
        st.session_state.messages = get_chat_messages(chat_id)
        st.rerun()

if st.sidebar.button("Logout"):
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    st.rerun()

# ---------------- CHAT AREA ----------------
st.title(f"Welcome {st.session_state.user_name} 👋")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        if msg["role"] == "assistant":
            if msg.get("response_time"):
                st.caption(f"⏱ {msg['response_time']} sec")
            else:
                st.caption(f"Model: {msg.get('model')}")

# ---------------- CHAT INPUT ----------------
query = st.chat_input("Ask your question...")

if query:

    if len(get_chat_messages(st.session_state.current_chat)) == 0:
        update_chat_title(st.session_state.current_chat, query[:50])

    # Show user instantly
    st.session_state.messages.append({
        "role": "user",
        "content": query,
        "model": "user"
    })

    save_message(
        st.session_state.current_chat,
        st.session_state.user_email,
        st.session_state.company,
        "user",
        query,
        "user",
        None
    )

    with st.chat_message("user"):
        st.write(query)

    # Assistant Response
    with st.chat_message("assistant"):
        with st.spinner("Analyzing company documents..."):

            start_time = time.time()

            query_vector = embed_model.encode(query).tolist()
            index = get_company_index(st.session_state.company)

            if not index:
                answer = "Company index not found."
                total_time = None
                st.error(answer)
            else:
                results = index.query(
                    vector=query_vector,
                    top_k=6,
                    include_metadata=True
                )

                context_text = "\n\n".join(
                    [match["metadata"]["text"] for match in results["matches"]]
                )

                response = groq_client.chat.completions.create(
                    model=st.session_state.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Context:\n{context_text}\n\nQuestion:\n{query}"}
                    ],
                    temperature=0.2
                )

                answer = response.choices[0].message.content.strip()

                end_time = time.time()
                total_time = round(end_time - start_time, 2)

                st.write(answer)
                st.caption(f"Model Used: {st.session_state.model}")
                st.caption(f"⏱ Response Time: {total_time} sec")

    # Save assistant message
    st.session_state.messages.append({
        "role": "assistant",
        "content": answer,
        "model": st.session_state.model,
        "response_time": total_time
    })

    save_message(
        st.session_state.current_chat,
        st.session_state.user_email,
        st.session_state.company,
        "assistant",
        answer,
        st.session_state.model,
        total_time
    )
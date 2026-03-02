import warnings
warnings.filterwarnings("ignore")

from transformers import logging
logging.set_verbosity_error()

import os
from dotenv import load_dotenv
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer
from groq import Groq

# ==========================================
# CONFIG
# ==========================================
INDEX_NAME = "companyragv2"
TOP_K = 6
MODEL_NAME = "llama-3.3-70b-versatile"
TEMPERATURE = 0.2

# ==========================================
# LOAD ENV
# ==========================================
load_dotenv()

pinecone_key = os.getenv("PINECONE_API_KEY")
groq_key = os.getenv("GROQ_API_KEY")

pc = Pinecone(api_key=pinecone_key)
index = pc.Index(INDEX_NAME)

embed_model = SentenceTransformer("all-mpnet-base-v2")
groq_client = Groq(api_key=groq_key)

# ==========================================
# LOAD SYSTEM PROMPT
# ==========================================
with open("prompts/system_prompt.txt", "r", encoding="utf-8") as f:
    system_prompt = f.read()

print("\n Company Knowledge Assistant Ready")
print("Type 'exit' to stop.\n")

# ==========================================
# CHAT LOOP
# ==========================================
while True:

    query = input("Ask your question: ").strip()

    if query.lower() == "exit":
        break

    if not query:
        continue

    # -----------------------------
    # EMBEDDING
    # -----------------------------
    query_vector = embed_model.encode(query).tolist()

    # -----------------------------
    # SEARCH BOTH FILES
    # -----------------------------
    results = index.query(
        vector=query_vector,
        top_k=TOP_K,
        include_metadata=True
    )

    if not results.get("matches"):
        print("No relevant data found.\n")
        continue

    # -----------------------------
    # GROUP CONTEXT BY SOURCE
    # -----------------------------
    context_by_source = {}

    for match in results["matches"]:
        source = match["metadata"].get("source", "Unknown Source")
        text = match["metadata"].get("text", "")

        if source not in context_by_source:
            context_by_source[source] = []

        context_by_source[source].append(text)

    # -----------------------------
    # GENERATE ANSWER FOR EACH FILE
    # -----------------------------
    for source, chunks in context_by_source.items():

        context_text = "\n\n".join(chunks)

        user_prompt = f"""
Context:
{context_text}

Question:
{query}
"""

        response = groq_client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=TEMPERATURE
        )

        answer = response.choices[0].message.content.strip()

        print("\n=======================================")
        print(f" ANSWER FROM: {source}")
        print("=======================================\n")
        print(answer)
        print("\n=======================================\n")
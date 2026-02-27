import os
from dotenv import load_dotenv
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer

# -------------------------
# CONFIG
# -------------------------
INDEX_NAME = "companyragv2"   # Must match ingestion
TOP_K = 5

# -------------------------
# LOAD API KEY
# -------------------------
load_dotenv()
api_key = os.getenv("PINECONE_API_KEY")

# -------------------------
# CONNECT TO PINECONE
# -------------------------
print("Connecting to Pinecone...")
pc = Pinecone(api_key=api_key)
index = pc.Index(INDEX_NAME)

# -------------------------
# LOAD SAME EMBEDDING MODEL
# -------------------------
print("Loading embedding model (MPNet 768)...")
model = SentenceTransformer("all-mpnet-base-v2")

# -------------------------
# TAKE USER QUESTION
# -------------------------
query = input("\nAsk your question: ")

# -------------------------
# CONVERT QUESTION → EMBEDDING
# -------------------------
print("Converting question to embedding...")
query_vector = model.encode(query).tolist()

# -------------------------
# SEARCH IN PINECONE (NO FILTER → BOTH FILES)
# -------------------------
print("Searching across ALL company documents...")

results = index.query(
    vector=query_vector,
    top_k=TOP_K,
    include_metadata=True
)

# -------------------------
# PROCESS RESULTS
# -------------------------
contexts_by_source = {}

for match in results["matches"]:
    source = match["metadata"]["source"]
    text = match["metadata"]["text"]
    score = match["score"]

    if source not in contexts_by_source:
        contexts_by_source[source] = []

    contexts_by_source[source].append(
        f"(Score: {score:.4f})\n{text}"
    )

# -------------------------
# PRINT CLEAN OUTPUT
# -------------------------
print("\n================ RETRIEVED CONTEXT ================\n")

final_context = ""

for source, chunks in contexts_by_source.items():
    print(f"\n📂 SOURCE: {source}\n")
    combined = "\n\n".join(chunks)
    print(combined)
    final_context += f"\n\nSOURCE: {source}\n{combined}"

print("\n================ USER QUESTION ================\n")
print(query)

print("\n================ COMBINED CONTEXT FOR LLM ================\n")
print(final_context)
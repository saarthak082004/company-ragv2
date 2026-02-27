import os
import re
from dotenv import load_dotenv
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone
from langchain_text_splitters import TokenTextSplitter

# -------------------------
# CONFIG
# -------------------------
COMPANY_NAME = "Synise"
INDEX_NAME = "syniseindex"
PDF_PATH = "../data/synise/synise_handbook.pdf"

CHUNK_SIZE = 250
CHUNK_OVERLAP = 50

# -------------------------
# LOAD ENV
# -------------------------
load_dotenv()
pinecone_key = os.getenv("PINECONE_API_KEY")

# -------------------------
# LOAD EMBEDDING MODEL
# -------------------------
print("Loading embedding model...")
embed_model = SentenceTransformer("all-mpnet-base-v2")

# -------------------------
# LOAD PDF
# -------------------------
def load_pdf(path):
    print("Reading PDF...")
    reader = PdfReader(path)
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + " "
    return text

# -------------------------
# CLEAN TEXT
# -------------------------
def clean_text(text):
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

# -------------------------
# SPLIT INTO CHUNKS
# -------------------------
def split_text(text):
    splitter = TokenTextSplitter(
        encoding_name="cl100k_base",
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP
    )
    return splitter.split_text(text)

# -------------------------
# MAIN INGESTION
# -------------------------
def main():

    raw_text = load_pdf(PDF_PATH)
    cleaned_text = clean_text(raw_text)
    chunks = split_text(cleaned_text)

    print(f"Total chunks created: {len(chunks)}")

    pc = Pinecone(api_key=pinecone_key)
    index = pc.Index(INDEX_NAME)

    vectors = []

    for i, chunk in enumerate(chunks):
        embedding = embed_model.encode(chunk).tolist()

        vectors.append({
            "id": f"synise-{i}",
            "values": embedding,
            "metadata": {
                "text": chunk,
                "company": COMPANY_NAME
            }
        })

    index.upsert(vectors)
    print("Synise ingestion complete.")

if __name__ == "__main__":
    main()
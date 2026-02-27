import warnings
warnings.filterwarnings("ignore")

from transformers import logging
logging.set_verbosity_error()

import re
import os
from dotenv import load_dotenv
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone
from langchain_text_splitters import TokenTextSplitter

# -------------------------
# CONFIG
# -------------------------
DATA_FOLDER = "data"   # Load all PDFs from this folder
CHUNK_TOKENS = 250
OVERLAP_TOKENS = 50
INDEX_NAME = "companyragv2"

# -------------------------
# LOAD EMBEDDING MODEL
# -------------------------
print("Loading embedding model...")
embed_model = SentenceTransformer("all-mpnet-base-v2")

# -------------------------
# STEP 1: LOAD PDF
# -------------------------
def load_pdf(pdf_path):
    print(f"Reading PDF: {pdf_path}")
    reader = PdfReader(pdf_path)
    text = ""

    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + " "

    return text


# -------------------------
# STEP 2: CLEAN TEXT
# -------------------------
def clean_text(text):
    text = re.sub(r'\n+', ' ', text)
    text = re.sub(r'\t+', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)

    return text.strip()


# -------------------------
# STEP 3: TOKEN CHUNKING
# -------------------------
def split_into_chunks(text):
    splitter = TokenTextSplitter(
        encoding_name="cl100k_base",
        chunk_size=CHUNK_TOKENS,
        chunk_overlap=OVERLAP_TOKENS
    )

    chunks = splitter.split_text(text)

    chunked_data = []
    for i, chunk in enumerate(chunks):
        chunk = chunk.strip()
        if chunk:
            chunked_data.append((i, chunk))

    return chunked_data


# -------------------------
# STEP 4: GENERATE EMBEDDINGS
# -------------------------
def generate_embeddings(chunks, source_name):
    print(f"\nGenerating embeddings for {source_name}...")

    embedded_chunks = []

    for chunk_id, chunk_text in chunks:

        if len(chunk_text) > 1500:
            chunk_text = chunk_text[:1500]

        embedding = embed_model.encode(chunk_text).tolist()

        embedded_chunks.append({
            "id": f"{source_name}-chunk-{chunk_id}",
            "values": embedding,
            "metadata": {
                "text": chunk_text,
                "chunk_id": chunk_id,
                "source": source_name
            }
        })

    print("Total embeddings created:", len(embedded_chunks))
    return embedded_chunks


# -------------------------
# STEP 5: UPLOAD TO PINECONE
# -------------------------
def upload_to_pinecone(vectors):
    print("\nConnecting to Pinecone...")

    load_dotenv()
    api_key = os.getenv("PINECONE_API_KEY")

    pc = Pinecone(api_key=api_key)
    index = pc.Index(INDEX_NAME)

    print("Uploading to Pinecone...")
    index.upsert(vectors)

    print("UPLOAD COMPLETE!")


# -------------------------
# MAIN PIPELINE
# -------------------------
def main():

    all_vectors = []

    # Loop through all PDFs in data folder
    for file in os.listdir(DATA_FOLDER):
        if file.endswith(".pdf"):

            pdf_path = os.path.join(DATA_FOLDER, file)
            source_name = file.replace(".pdf", "").replace(" ", "_")

            raw_text = load_pdf(pdf_path)
            cleaned_text = clean_text(raw_text)

            chunks = split_into_chunks(cleaned_text)
            print(f"Total chunks from {file}:", len(chunks))

            embedded_chunks = generate_embeddings(chunks, source_name)

            all_vectors.extend(embedded_chunks)

    upload_to_pinecone(all_vectors)

    print("\n✅ ALL PDFs INGESTED SUCCESSFULLY!")


# -------------------------
# RUN
# -------------------------
if __name__ == "__main__":
    main()
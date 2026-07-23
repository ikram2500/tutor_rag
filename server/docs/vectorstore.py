# PDF -> CHUNKING
#     ->MONGODB(FULL TEXT STORAGE)
#     -> PINECONE (EMBEDDING+METADATA)

import os
import asyncio
from pathlib import Path
from dotenv import load_dotenv

from pinecone import Pinecone
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from config.db import chunk_collection

ENV_FILE = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(ENV_FILE)

GOOGLE_API_KEY=os.getenv("GOOGLE_API_KEY")
PINECONE_API_KEY=os.getenv("PINECONE_API_KEY")
PINECONE_ENV=os.getenv("PINECONE_ENV","us-east-1")
PINECONE_INDEX_NAME=os.getenv("PINECONE_INDEX_NAME","tutor-rags")

if GOOGLE_API_KEY:
    os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY


UPLOAD_DIR = Path(__file__).resolve().parent / ".upload_docs"
UPLOAD_DIR.mkdir(exist_ok=True)

# pinecone global upsert fucntion

pc=None
index=None

def get_pinecone_index():
    global pc,index
    if index is None:
        if not PINECONE_API_KEY:
            raise RuntimeError("PINECONE_API_KEY is not configured in server/.env")
        pc=Pinecone(api_key=PINECONE_API_KEY)
        index=pc.Index(PINECONE_INDEX_NAME)
    return index



async  def load_vectorstore(uploaded_files,role:str,doc_id:str,grade:int):
    # initilize emedding model
    if not GOOGLE_API_KEY:
        raise RuntimeError("GOOGLE_API_KEY is not configured in server/.env")
    embed_model=GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
    # get pinecone index
    pinecone_index=get_pinecone_index()
    # loop through uploaded files
    for file in uploaded_files:
        # 1. save raw file
        filename = Path(file.filename or "upload.pdf").name
        save_path = UPLOAD_DIR / filename
        with open(save_path,"wb") as f:
            f.write(await file.read())
        # 2. load pdf text
        loader=PyPDFLoader(str(save_path))
        documents=loader.load()
        # 3. chunk text 
        splitter=RecursiveCharacterTextSplitter(chunk_size=500,chunk_overlap=50)
        chunks=splitter.split_documents(documents)
        # 4. guard condition
        if not chunks:
            raise ValueError(f"No text could be extracted from {filename}")
        # 5. dual storing
        # 5.1 store full text in mongodb
        chunk_docs=[]
        for i,chunk in enumerate(chunks):
            chunk_docs.append({
                "chunk_id":f"{doc_id}-{i}",
                "doc_id":doc_id,
                "text":chunk.page_content,
                "page":int(chunk.metadata.get("page",0)),
                "source":filename,
                "grade":grade,
                "role":role,
            })
        # 5.2 create embeddings
        texts=[chunk.page_content for chunk in chunks]
        embeddings= await asyncio.to_thread(embed_model.embed_documents,texts)
        if len(embeddings) != len(chunks):
            raise RuntimeError("Embedding count does not match the number of PDF chunks")
        # upsert pinecone
        ids=[f"{doc_id}-{i}" for i in range(len(embeddings))]

        metadatas=[
            {
                "doc_id":doc_id,
                "page":int(chunks[i].metadata.get("page",0)),
                "source":filename,
                "grade":grade,
                "role":role,
            }
            for i in range(len(embeddings))
        ]

        upsert_result = await asyncio.to_thread(
            pinecone_index.upsert,
            vectors=list(zip(ids, embeddings, metadatas)),
        )
        upserted_count = getattr(upsert_result, "upserted_count", None)
        if upserted_count is None and isinstance(upsert_result, dict):
            upserted_count = upsert_result.get("upserted_count")
        if upserted_count is not None and upserted_count != len(ids):
            raise RuntimeError(
                f"Pinecone confirmed {upserted_count} of {len(ids)} vector upserts"
            )

        chunk_collection.insert_many(chunk_docs)
        print(
            f"Pinecone indexed {len(ids)} vectors for {filename} "
            f"in index '{PINECONE_INDEX_NAME}' (default namespace)."
        )

    print(f"Successfully indexed {len(uploaded_files)} file(s).")

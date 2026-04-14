# src/data/ingest.py

from typing import List
import chromadb
from chromadb.utils import embedding_functions

from src.config import settings
from src.data.schemas import DocumentRecord
from src.data.chunking import chunk_document


def ingest_documents(docs: List[DocumentRecord]) -> int:
    """
    Ingest documents into Chroma vector store.

    Parameters
    ----------
    docs : List[DocumentRecord]
        Documents to ingest.

    Returns
    -------
    int
        Number of chunks ingested.
    """
    client = chromadb.PersistentClient(path=settings.chroma_persist_dir)

    embedding_fn = embedding_functions.OpenAIEmbeddingFunction(
        api_key=settings.openai_api_key,
        model_name=settings.openai_embedding_model,
    )

    collection = client.get_or_create_collection(
        name="macra_docs",
        embedding_function=embedding_fn,
    )

    ids = []
    documents = []
    metadatas = []

    for doc in docs:
        chunks = chunk_document(doc)

        for chunk in chunks:
            ids.append(chunk.chunk_id)
            documents.append(chunk.chunk_text)

            metadatas.append(
                {
                    "doc_id": chunk.doc_id,
                    "title": chunk.title,
                    "category": chunk.category,
                    "source_url": chunk.source_url,
                    "language": chunk.language,
                    **chunk.metadata,
                }
            )

    if ids:
        collection.upsert(ids=ids, documents=documents, metadatas=metadatas)

    return len(ids)
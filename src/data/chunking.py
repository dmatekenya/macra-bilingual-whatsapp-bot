from typing import List
from src.data.schemas import DocumentRecord, ChunkRecord


def simple_chunk_text(text: str, chunk_size: int = 1000, overlap: int = 150) -> List[str]:
    chunks = []
    start = 0
    text = text.strip()

    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap

    return chunks


def chunk_document(doc: DocumentRecord) -> List[ChunkRecord]:
    chunk_texts = simple_chunk_text(doc.text)

    chunks = []
    for i, chunk_text in enumerate(chunk_texts, start=1):
        chunks.append(
            ChunkRecord(
                chunk_id=f"{doc.doc_id}_chunk_{i}",
                doc_id=doc.doc_id,
                chunk_text=chunk_text,
                title=doc.title,
                category=doc.category,
                source_url=doc.source_url,
                language=doc.language,
                metadata=doc.metadata,
            )
        )
    return chunks
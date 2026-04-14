# scripts/ingest_docs.py

from src.data.loaders import load_jsonl_documents
from src.data.ingest import ingest_documents


def main() -> None:
    docs = load_jsonl_documents("data/raw/macra_docs.jsonl")
    n_chunks = ingest_documents(docs)
    print(f"Ingested {n_chunks} chunks.")


if __name__ == "__main__":
    main()
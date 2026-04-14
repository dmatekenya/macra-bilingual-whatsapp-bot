from typing import List, Dict, Any
import chromadb
from chromadb.utils import embedding_functions
from src.config import settings
from src.data.schemas import RetrievalResult


class Retriever:
    def __init__(self) -> None:
        self.client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
        self.embedding_fn = embedding_functions.OpenAIEmbeddingFunction(
            api_key=settings.openai_api_key,
            model_name=settings.openai_embedding_model,
        )
        self.collection = self.client.get_or_create_collection(
            name="macra_docs",
            embedding_function=self.embedding_fn,
        )

    def search(self, query: str, n_results: int = 4) -> RetrievalResult:
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
        )

        documents: List[str] = results.get("documents", [[]])[0]
        metadatas: List[Dict[str, Any]] = results.get("metadatas", [[]])[0]

        return RetrievalResult(
            answer_contexts=documents,
            metadatas=metadatas,
        )
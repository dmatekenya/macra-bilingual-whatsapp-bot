from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List


class DocumentRecord(BaseModel):
    doc_id: str
    title: str
    source_url: Optional[str] = None
    text: str
    language: Optional[str] = None
    category: str = "other"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ChunkRecord(BaseModel):
    chunk_id: str
    doc_id: str
    chunk_text: str
    title: str
    category: str = "other"
    source_url: Optional[str] = None
    language: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class IncomingMessage(BaseModel):
    from_number: str
    message_text: str
    profile_name: Optional[str] = None
    media_url: Optional[str] = None
    media_content_type: Optional[str] = None


class RouteDecision(BaseModel):
    route: str
    confidence: float = 0.5
    reason: Optional[str] = None


class RetrievalResult(BaseModel):
    answer_contexts: List[str]
    metadatas: List[Dict[str, Any]]
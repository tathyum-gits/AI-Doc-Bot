from dataclasses import dataclass
from typing import List, Dict, Optional

@dataclass
class ChatResponse:
    """Response model for chat interactions."""
    answer: str
    sources: List[Dict[str, any]]
    confidence_score: float
    model_used: str

@dataclass
class SearchResult:
    """Model for search results from embeddings."""
    text: str
    document_id: str
    page_number: int
    similarity_score: float

@dataclass
class ProcessingResult:
    """Model for document processing results."""
    success: bool
    message: str
    document_id: Optional[str] = None
    error: Optional[Exception] = None
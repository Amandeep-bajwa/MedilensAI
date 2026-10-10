from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

class RAGCitation(BaseModel):
    chunk_id: str = Field(..., description="Unique ID of the cited document chunk")
    page_number: Optional[str] = Field("1", description="Report page number containing the citation")
    snippet: str = Field(..., description="Exact context snippet from the clinical document")
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="Normalized relevance/similarity score")

class RAGQueryRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=500, description="Patient query grounded in the report")
    top_k: int = Field(3, ge=1, le=10, description="Maximum number of relevant chunks to retrieve")

class RAGQueryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    query_id: str
    report_id: str
    question: str
    answer: str
    citations: List[RAGCitation] = Field(default_factory=list, description="Source citations supporting the answer")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Calculated retrieval confidence score")
    is_grounded: bool = Field(True, description="Whether the answer is grounded in retrieved report chunks")
    disclaimer: str = Field(..., description="Mandatory medical and clinical safety disclaimer")
    created_at: datetime

class RAGIndexStatusResponse(BaseModel):
    report_id: str
    total_chunks: int
    indexed_chunks: int
    status: str = Field(..., description="Index status: Indexed, Pending, or Empty")
    algorithm: str = Field("hybrid_dense_semantic_v1", description="Retrieval indexing algorithm")
    last_indexed_at: Optional[datetime] = None

class RAGReindexResponse(BaseModel):
    report_id: str
    indexed_count: int
    message: str

class RAGHistoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    interaction_id: str
    question: str
    response: str
    created_at: datetime

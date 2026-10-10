from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.entities import User
from app.schemas.rag import (
    RAGQueryRequest,
    RAGQueryResponse,
    RAGIndexStatusResponse,
    RAGReindexResponse,
    RAGHistoryItem
)
from app.services.rag import (
    query_rag_engine,
    get_rag_index_status,
    reindex_report_chunks,
    get_rag_history
)

router = APIRouter(prefix="/reports", tags=["Report-Grounded RAG Q&A Engine"])

@router.post(
    "/{report_id}/rag/query",
    response_model=RAGQueryResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute grounded clinical question answering with page citations"
)
def run_rag_query(
    report_id: str,
    request: RAGQueryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Submits a natural language clinical inquiry against the specific medical document.
    Uses hybrid dense-sparse semantic retrieval over document chunks and constructs
    citations with page numbers, relevance scores, and mandatory safety disclaimers.
    """
    return query_rag_engine(
        report_id=report_id,
        request=request,
        current_user=current_user,
        db=db
    )

@router.get(
    "/{report_id}/rag/status",
    response_model=RAGIndexStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve semantic indexing status for report chunks"
)
def get_index_status(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Returns chunk counts, indexing status, and algorithm metadata."""
    return get_rag_index_status(
        report_id=report_id,
        current_user=current_user,
        db=db
    )

@router.post(
    "/{report_id}/rag/reindex",
    response_model=RAGReindexResponse,
    status_code=status.HTTP_200_OK,
    summary="Re-index semantic chunks and refresh embeddings for report"
)
def reindex_chunks(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Forces re-extraction and semantic indexing of all chunks for this report."""
    return reindex_report_chunks(
        report_id=report_id,
        current_user=current_user,
        db=db
    )

@router.get(
    "/{report_id}/rag/history",
    response_model=List[RAGHistoryItem],
    status_code=status.HTTP_200_OK,
    summary="Retrieve grounded Q&A history for this report"
)
def get_history(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieves previous questions and grounded answers for this document."""
    return get_rag_history(
        report_id=report_id,
        current_user=current_user,
        db=db
    )

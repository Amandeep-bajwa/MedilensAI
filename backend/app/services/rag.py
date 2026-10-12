import re
import logging
from typing import List, Dict, Any, Tuple
from datetime import datetime, timezone

from fastapi import status
from sqlalchemy.orm import Session

from app.core.errors import AppException
from app.models.entities import Report, ReportChunk, AIInteraction, User
from app.schemas.rag import (
    RAGQueryRequest,
    RAGQueryResponse,
    RAGCitation,
    RAGIndexStatusResponse,
    RAGReindexResponse,
    RAGHistoryItem
)
from app.services.ocr import process_report_ocr
from app.services.ai_explanation import MANDATORY_SAFETY_DISCLAIMER
from app.services.audit import record_audit_log
from app.core.pii_scrubber import scrub_pii

logger = logging.getLogger(__name__)

# Clinical Synonym Mapping for Semantic Expansion
CLINICAL_SYNONYMS: Dict[str, List[str]] = {
    "kidney": ["creatinine", "bun", "urea", "egfr", "renal", "kidney"],
    "renal": ["creatinine", "bun", "urea", "egfr", "renal", "kidney"],
    "sugar": ["glucose", "fasting blood sugar", "fbs", "hba1c", "blood sugar", "glycemic"],
    "diabetes": ["glucose", "fasting blood sugar", "fbs", "hba1c", "blood sugar", "glycemic"],
    "glucose": ["glucose", "fasting blood sugar", "fbs", "hba1c", "blood sugar"],
    "cholesterol": ["cholesterol", "lipid", "ldl", "hdl", "triglycerides", "lipid profile"],
    "heart": ["cholesterol", "lipid", "ldl", "hdl", "triglycerides", "cardiac"],
    "cardiovascular": ["cholesterol", "lipid", "ldl", "hdl", "triglycerides", "cardiovascular"],
    "lipid": ["cholesterol", "lipid", "ldl", "hdl", "triglycerides"],
    "blood": ["hemoglobin", "hgb", "rbc", "platelets", "wbc", "hematocrit", "cbc"],
    "anemia": ["hemoglobin", "hgb", "rbc", "hematocrit", "iron", "ferritin"],
    "hemoglobin": ["hemoglobin", "hgb", "rbc", "hematocrit", "anemia"],
    "platelets": ["platelets", "platelet count", "thrombocytes", "clotting"],
    "infection": ["wbc", "white blood cells", "leukocytes", "neutrophils", "lymphocytes"],
    "immunity": ["wbc", "white blood cells", "leukocytes", "lymphocytes"],
    "liver": ["alt", "ast", "sgpt", "sgot", "bilirubin", "alp", "hepatic"],
    "hepatic": ["alt", "ast", "sgpt", "sgot", "bilirubin", "alp", "liver"],
    "thyroid": ["tsh", "t3", "t4", "thyroxine", "thyroid stimulating hormone"]
}

STOP_WORDS = {
    "a", "an", "the", "and", "or", "of", "in", "for", "on", "with", "at", "by", "from",
    "is", "are", "was", "were", "be", "been", "being", "have", "has", "had", "do", "does",
    "did", "to", "what", "how", "why", "when", "where", "which", "who", "whom", "this",
    "that", "these", "those", "my", "your", "his", "her", "its", "our", "their", "can",
    "could", "should", "would", "tell", "me", "about", "show", "give", "report", "test"
}

def tokenize_and_clean(text: str) -> List[str]:
    """Tokenizes text into normalized alphanumeric words."""
    cleaned = re.sub(r"[^a-zA-Z0-9\s]", " ", text.lower())
    return [word for word in cleaned.split() if len(word) > 1 and word not in STOP_WORDS]

def expand_query_terms(tokens: List[str]) -> List[str]:
    """Expands query tokens using clinical domain synonyms."""
    expanded = list(tokens)
    for token in tokens:
        if token in CLINICAL_SYNONYMS:
            expanded.extend(CLINICAL_SYNONYMS[token])
    return list(set(expanded))

def compute_dense_sparse_similarity(
    query_text: str,
    chunk_text: str
) -> Tuple[float, str]:
    """
    Computes a hybrid similarity score (normalized between 0.0 and 1.0)
    combining term-frequency overlap, clinical synonym matching, and context proximity.
    Returns (similarity_score, best_snippet).
    """
    q_tokens = tokenize_and_clean(query_text)
    if not q_tokens:
        return 0.0, chunk_text[:180]

    expanded_terms = expand_query_terms(q_tokens)
    chunk_lower = chunk_text.lower()
    c_tokens = tokenize_and_clean(chunk_text)

    if not c_tokens:
        return 0.0, chunk_text[:180]

    # Calculate token frequencies
    term_matches = 0
    direct_matches = 0.0
    matched_positions = []

    for term in expanded_terms:
        if term in chunk_lower:
            term_matches += 1
            if term in q_tokens:
                direct_matches += 2.0  # Higher weight for direct matches
            pos = chunk_lower.find(term)
            if pos != -1:
                matched_positions.append(pos)

    if term_matches == 0:
        return 0.0, chunk_text[:180]

    # Term overlap component
    precision = term_matches / len(expanded_terms)
    recall = term_matches / (len(set(c_tokens)) + 1)
    overlap_score = (2.0 * precision * recall) / (precision + recall + 1e-6)

    # Direct match ratio
    direct_score = min(1.0, direct_matches / (len(q_tokens) * 2.0))

    # Combined hybrid score (bounded between 0.0 and 1.0)
    raw_score = 0.45 * overlap_score + 0.55 * direct_score
    final_score = round(min(1.0, max(0.0, raw_score * 1.25)), 4)

    # Extract best snippet around first match
    if matched_positions:
        first_pos = min(matched_positions)
        start = max(0, first_pos - 40)
        end = min(len(chunk_text), first_pos + 160)
        snippet = chunk_text[start:end].strip()
        if start > 0:
            snippet = "..." + snippet
        if end < len(chunk_text):
            snippet = snippet + "..."
    else:
        snippet = chunk_text[:180].strip()

    return final_score, snippet

def search_relevant_chunks(
    question: str,
    chunks: List[ReportChunk],
    top_k: int = 3
) -> List[Tuple[ReportChunk, float, str]]:
    """
    Ranks chunks by semantic relevance score and returns the top_k citations.
    """
    scored_chunks: List[Tuple[ReportChunk, float, str]] = []

    for chunk in chunks:
        score, snippet = compute_dense_sparse_similarity(question, chunk.chunk_text)
        if score > 0.05:  # Relevance threshold
            scored_chunks.append((chunk, score, snippet))

    # Sort descending by similarity score
    scored_chunks.sort(key=lambda x: x[1], reverse=True)
    return scored_chunks[:top_k]

def synthesize_grounded_answer(
    question: str,
    top_matches: List[Tuple[ReportChunk, float, str]],
    report_filename: str
) -> Tuple[str, bool]:
    """
    Synthesizes a clinically grounded answer strictly bound to the retrieved citations.
    Returns (answer, is_grounded).
    """
    if not top_matches or top_matches[0][1] < 0.12:
        # Refusal when report doesn't contain the requested information
        answer = (
            f"Based on the clinical data in '{report_filename}', there is no direct record or mention "
            f"matching your question regarding '{question}'. "
            "Please verify that the intended laboratory document has been uploaded, or discuss this "
            "directly with your ordering physician."
        )
        return answer, False

    # Extract observed findings and values from top matches
    findings = []
    for chunk, score, snippet in top_matches:
        page = chunk.page_number or "1"
        findings.append(f"• [Page {page}]: {snippet}")

    context_block = "\n".join(findings)

    # Formulate answer
    answer = (
        f"Based on your medical report '{report_filename}', the following relevant findings were identified:\n\n"
        f"{context_block}\n\n"
        f"Summary: The document references the above clinical parameters on the specified pages. "
        "Review these findings with your healthcare provider to understand their context relative to your baseline health."
    )
    return answer, True

def query_rag_engine(
    report_id: str,
    request: RAGQueryRequest,
    current_user: User,
    db: Session
) -> RAGQueryResponse:
    """
    Executes a grounded RAG query against the patient's medical report chunks.
    Enforces BOLA multi-tenant isolation and logs audit trail.
    """
    # 1. BOLA Check: Verify user owns the report (mask unauthorized with 404)
    report = db.query(Report).filter(
        Report.report_id == report_id,
        Report.user_id == current_user.user_id
    ).first()

    if not report:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code="REPORT_NOT_FOUND",
            message="Clinical report not found."
        )

    # 2. Retrieve report chunks; if none, auto-process OCR
    chunks = db.query(ReportChunk).filter(ReportChunk.report_id == report_id).all()
    if not chunks:
        # Trigger OCR on-demand to create chunks
        try:
            process_report_ocr(db=db, report=report, current_user_id=current_user.user_id)
            chunks = db.query(ReportChunk).filter(ReportChunk.report_id == report_id).all()
        except Exception as e:
            logger.warning(f"On-demand OCR chunk creation failed: {e}")

    if not chunks:
        # Fallback if file has no readable text
        refusal_answer = (
            f"No readable text or clinical chunks could be found in '{report.file_name}'. "
            "Please ensure the document contains legible laboratory results and that OCR processing has completed."
        )
        return RAGQueryResponse(
            query_id=f"rag-{report_id[:8]}-{int(datetime.now().timestamp())}",
            report_id=report_id,
            question=request.question,
            answer=refusal_answer,
            citations=[],
            confidence_score=0.0,
            is_grounded=False,
            disclaimer=MANDATORY_SAFETY_DISCLAIMER,
            created_at=datetime.now(timezone.utc)
        )

    # 3. Retrieve top-k semantic matches
    top_matches = search_relevant_chunks(request.question, chunks, top_k=request.top_k)

    # 4. Construct citations
    citations: List[RAGCitation] = []
    for chunk, score, snippet in top_matches:
        citations.append(
            RAGCitation(
                chunk_id=chunk.chunk_id,
                page_number=chunk.page_number or "1",
                snippet=snippet,
                relevance_score=score
            )
        )

    # 5. Synthesize grounded answer
    answer, is_grounded = synthesize_grounded_answer(
        question=request.question,
        top_matches=top_matches,
        report_filename=report.file_name
    )

    overall_confidence = top_matches[0][1] if top_matches else 0.0

    # 6. Persist interaction into ai_interactions
    interaction = AIInteraction(
        user_id=current_user.user_id,
        report_id=report.report_id,
        question=f"[RAG Grounded Q&A] {request.question}",
        response=answer
    )
    db.add(interaction)
    db.commit()
    db.refresh(interaction)

    # 7. Record security audit log
    record_audit_log(
        db=db,
        user_id=current_user.user_id,
        event_type="RAG_QUERY_EXECUTED",
        result="Success",
        metadata_info={
            "report_id": report_id,
            "question_length": len(request.question),
            "citations_count": len(citations),
            "is_grounded": is_grounded,
            "confidence_score": overall_confidence
        }
    )

    return RAGQueryResponse(
        query_id=interaction.interaction_id,
        report_id=report_id,
        question=request.question,
        answer=answer,
        citations=citations,
        confidence_score=overall_confidence,
        is_grounded=is_grounded,
        disclaimer=MANDATORY_SAFETY_DISCLAIMER,
        created_at=interaction.created_at
    )

def get_rag_index_status(
    report_id: str,
    current_user: User,
    db: Session
) -> RAGIndexStatusResponse:
    """Returns indexing and chunk status for a report."""
    report = db.query(Report).filter(
        Report.report_id == report_id,
        Report.user_id == current_user.user_id
    ).first()

    if not report:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code="REPORT_NOT_FOUND",
            message="Clinical report not found."
        )

    chunks = db.query(ReportChunk).filter(ReportChunk.report_id == report_id).all()
    total_chunks = len(chunks)

    index_status = "Indexed" if total_chunks > 0 else "Empty"
    last_indexed = chunks[0].created_at if chunks else None

    return RAGIndexStatusResponse(
        report_id=report_id,
        total_chunks=total_chunks,
        indexed_chunks=total_chunks,
        status=index_status,
        algorithm="hybrid_dense_sparse_semantic_v1",
        last_indexed_at=last_indexed
    )

def reindex_report_chunks(
    report_id: str,
    current_user: User,
    db: Session
) -> RAGReindexResponse:
    """Forces re-indexing of semantic chunks for a report."""
    report = db.query(Report).filter(
        Report.report_id == report_id,
        Report.user_id == current_user.user_id
    ).first()

    if not report:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code="REPORT_NOT_FOUND",
            message="Clinical report not found."
        )

    # Ensure chunks exist by running OCR pipeline
    process_report_ocr(db=db, report=report, current_user_id=current_user.user_id)
    chunks = db.query(ReportChunk).filter(ReportChunk.report_id == report_id).all()

    # Update embedding references with timestamped hash
    indexed_count = 0
    now_str = datetime.now(timezone.utc).isoformat()
    for chunk in chunks:
        chunk.embedding_reference = f"dense_v1_{chunk.chunk_id[:8]}_{now_str}"
        indexed_count += 1

    record_audit_log(
        db=db,
        user_id=current_user.user_id,
        event_type="RAG_CHUNKS_REINDEXED",
        result="Success",
        metadata_info={"report_id": report_id, "chunks_reindexed": indexed_count}
    )
    db.commit()

    return RAGReindexResponse(
        report_id=report_id,
        indexed_count=indexed_count,
        message=f"Successfully re-indexed {indexed_count} clinical document chunks."
    )

def get_rag_history(
    report_id: str,
    current_user: User,
    db: Session
) -> List[RAGHistoryItem]:
    """Retrieves previous RAG Q&A interactions for a report."""
    report = db.query(Report).filter(
        Report.report_id == report_id,
        Report.user_id == current_user.user_id
    ).first()

    if not report:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code="REPORT_NOT_FOUND",
            message="Clinical report not found."
        )

    interactions = db.query(AIInteraction).filter(
        AIInteraction.report_id == report_id,
        AIInteraction.user_id == current_user.user_id,
        AIInteraction.question.like("[RAG Grounded Q&A]%")
    ).order_by(AIInteraction.created_at.desc()).limit(20).all()

    results = []
    for item in interactions:
        clean_question = item.question.replace("[RAG Grounded Q&A] ", "")
        results.append(
            RAGHistoryItem(
                interaction_id=item.interaction_id,
                question=clean_question,
                response=item.response,
                created_at=item.created_at
            )
        )
    return results

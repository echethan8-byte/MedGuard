"""
rag/retriever.py — Similarity search + reranking pipeline.
"""
import logging
from typing import List, Dict, Any, Optional
from django.conf import settings
from core.utils import similarity_search

logger = logging.getLogger('medguard')


def retrieve_policy_chunks(
    query: str,
    k: int = None,
    where_filter: Optional[Dict] = None,
) -> List[Dict[str, Any]]:
    """
    Retrieve top-k policy chunks from ChromaDB for a given query.
    """
    k = k or settings.RAG_TOP_K_RETRIEVE
    logger.debug(f"Retrieving top-{k} chunks for query: {query[:80]}…")

    results = similarity_search(
        collection_name=settings.CHROMA_POLICY_COLLECTION,
        query=query,
        k=k,
        where=where_filter,
        embedding_model=settings.EMBEDDING_MODEL,
    )
    logger.info(f"Retrieved {len(results)} policy chunks")
    return results


def retrieve_document_chunks(
    query: str,
    doc_id: str,
    k: int = None,
) -> List[Dict[str, Any]]:
    """
    Retrieve chunks from a specific hospital document.
    """
    k = k or settings.RAG_TOP_K_RETRIEVE
    results = similarity_search(
        collection_name=settings.CHROMA_DOCUMENTS_COLLECTION,
        query=query,
        k=k,
        where={"doc_id": str(doc_id)},
        embedding_model=settings.EMBEDDING_MODEL,
    )
    logger.info(f"Retrieved {len(results)} document chunks for doc_id={doc_id}")
    return results


def rerank_chunks(
    query: str,
    chunks: List[Dict[str, Any]],
    top_k: int = None,
) -> List[Dict[str, Any]]:
    """
    Rerank retrieved chunks using FlashRank cross-encoder.
    Falls back to score-based sorting if FlashRank unavailable.
    """
    top_k = top_k or settings.RAG_TOP_K_RERANK

    if not chunks:
        return []

    try:
        from flashrank import Ranker, RerankRequest
        ranker = Ranker(model_name="ms-marco-MiniLM-L-12-v2", cache_dir="/tmp/flashrank_cache")
        passages = [{"id": i, "text": c["text"]} for i, c in enumerate(chunks)]
        request = RerankRequest(query=query, passages=passages)
        results = ranker.rerank(request)

        reranked = []
        for r in results[:top_k]:
            original = chunks[r["id"]]
            reranked.append({
                **original,
                "rerank_score": r["score"],
            })

        logger.info(f"Reranked {len(chunks)} → {len(reranked)} chunks")
        return reranked

    except ImportError:
        logger.warning("FlashRank not available, falling back to score-based sort")
        sorted_chunks = sorted(chunks, key=lambda x: x.get("score", 0), reverse=True)
        return sorted_chunks[:top_k]

    except Exception as e:
        logger.error(f"Reranking failed: {e}, falling back to top-k by score")
        sorted_chunks = sorted(chunks, key=lambda x: x.get("score", 0), reverse=True)
        return sorted_chunks[:top_k]


def build_context_string(chunks: List[Dict[str, Any]], max_chars: int = 12000) -> str:
    """
    Format retrieved chunks into a structured context string for the LLM prompt.
    """
    parts = []
    total_chars = 0

    for i, chunk in enumerate(chunks, 1):
        meta = chunk.get("metadata", {})
        source = meta.get("source", "Unknown Source")
        reg_id = meta.get("regulation_id", "")
        section = meta.get("section", "")

        header = f"[CHUNK {i}]"
        if source:
            header += f" Source: {source}"
        if reg_id:
            header += f" | Reg: {reg_id}"
        if section:
            header += f" | Section: {section}"

        chunk_str = f"{header}\n{chunk['text']}\n"

        if total_chars + len(chunk_str) > max_chars:
            logger.debug(f"Context truncated at chunk {i} (max_chars={max_chars})")
            break

        parts.append(chunk_str)
        total_chars += len(chunk_str)

    return "\n".join(parts)

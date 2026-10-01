"""
Unit Tests: RAG Ingestion, Chunking, and Semantic Search
"""
import pytest
from backend.app.rag.knowledge_indexer import knowledge_indexer


def test_chunking_and_metadata():
    assert len(knowledge_indexer.chunks) > 0, "Vector store should have ingested chunks"
    first_chunk = knowledge_indexer.chunks[0]
    assert "doc_title" in first_chunk
    assert "section" in first_chunk
    assert "text" in first_chunk


def test_semantic_retrieval_bearing():
    results = knowledge_indexer.search("bearing vibration overheating grease spalling", top_k=2)
    assert len(results) > 0
    top = results[0]
    assert "Bearing" in top["doc_title"] or "Vibration" in top["doc_title"]
    assert top["similarity_score"] > 0.40


def test_semantic_retrieval_overload():
    results = knowledge_indexer.search("motor overload full load current slip trip", top_k=2)
    assert len(results) > 0
    top = results[0]
    assert "Overload" in top["doc_title"] or "Maintenance" in top["doc_title"]

"""
P_311 RAG Pipeline: Document Ingestion, Semantic Chunking, and Vector Indexing
Uses local CPU-only MiniLM-L6-v2 embeddings with a lightweight persistent vector index.
"""
import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List
import numpy as np
from sentence_transformers import SentenceTransformer

from backend.app.core.config import settings

logger = logging.getLogger("rag")


class KnowledgeIndexer:
    def __init__(
        self,
        knowledge_dir: Path = settings.KNOWLEDGE_BASE_DIR,
        vector_store_dir: Path = settings.VECTOR_STORE_PATH,
        model_name: str = settings.EMBEDDING_MODEL_NAME,
    ):
        self.knowledge_dir = Path(knowledge_dir)
        self.vector_store_dir = Path(vector_store_dir)
        self.model_name = model_name

        self.vector_store_dir.mkdir(parents=True, exist_ok=True)
        self.chunks_file = self.vector_store_dir / "chunks.json"
        self.embeddings_file = self.vector_store_dir / "embeddings.npy"

        # Lazy load model on demand to save memory on fast startup
        self._model: SentenceTransformer | None = None
        self.chunks: List[Dict[str, Any]] = []
        self.embeddings: np.ndarray | None = None

        self._load_existing_index()

    @property
    def model(self) -> SentenceTransformer:
        if self._model is None:
            logger.info("Loading local embedding model: %s on CPU...", self.model_name)
            self._model = SentenceTransformer(self.model_name, device="cpu")
            logger.info("Embedding model loaded successfully.")
        return self._model

    def _load_existing_index(self):
        """Loads cached chunks and vector embeddings if present on disk."""
        if self.chunks_file.exists() and self.embeddings_file.exists():
            try:
                with open(self.chunks_file, "r", encoding="utf-8") as f:
                    self.chunks = json.load(f)
                self.embeddings = np.load(str(self.embeddings_file))
                logger.info("Loaded %d knowledge chunks from cached vector store.", len(self.chunks))
            except Exception as e:
                logger.warning("Could not load cached vector index: %s", e)
                self.chunks = []
                self.embeddings = None

    def chunk_markdown_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Parses a markdown file by sections and splits into semantic chunks."""
        text = file_path.read_text(encoding="utf-8")
        filename = file_path.name

        # Extract document title (first H1)
        doc_title_match = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
        doc_title = doc_title_match.group(1).strip() if doc_title_match else filename.replace("_", " ").title()

        # Split into sections by H2 headers
        sections = re.split(r"\n(?=##\s+)", text)
        chunks = []

        for sec in sections:
            sec = sec.strip()
            if not sec:
                continue

            sec_header_match = re.search(r"^##\s+(.+)$", sec, re.MULTILINE)
            section_title = sec_header_match.group(1).strip() if sec_header_match else "General"

            # Clean markdown header line from content
            content = re.sub(r"^##\s+.+$", "", sec, flags=re.MULTILINE).strip()
            # Remove H1 if present
            content = re.sub(r"^#\s+.+$", "", content, flags=re.MULTILINE).strip()
            if not content:
                continue

            # Sub-chunk if section is large (>600 characters)
            paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
            current_chunk = ""

            for p in paragraphs:
                if len(current_chunk) + len(p) < 550:
                    current_chunk += "\n" + p if current_chunk else p
                else:
                    if current_chunk:
                        formatted_text = f"[{doc_title} > {section_title}]\n{current_chunk.strip()}"
                        chunks.append({
                            "doc_title": doc_title,
                            "filename": filename,
                            "section": section_title,
                            "text": formatted_text,
                            "raw_text": current_chunk.strip()
                        })
                    current_chunk = p

            if current_chunk:
                formatted_text = f"[{doc_title} > {section_title}]\n{current_chunk.strip()}"
                chunks.append({
                    "doc_title": doc_title,
                    "filename": filename,
                    "section": section_title,
                    "text": formatted_text,
                    "raw_text": current_chunk.strip()
                })

        return chunks

    def ingest_all(self) -> int:
        """Ingests all technical manuals in knowledge_base/ into the vector index."""
        logger.info("Starting knowledge base ingestion from %s...", self.knowledge_dir)
        md_files = list(self.knowledge_dir.glob("*.md"))
        if not md_files:
            logger.warning("No markdown files found in %s", self.knowledge_dir)
            return 0

        all_chunks = []
        for mf in md_files:
            chunks = self.chunk_markdown_file(mf)
            all_chunks.extend(chunks)

        logger.info("Extracted %d chunks across %d documents.", len(all_chunks), len(md_files))

        # Generate embeddings
        texts = [c["text"] for c in all_chunks]
        vectors = self.model.encode(texts, batch_size=16, normalize_embeddings=True, show_progress_bar=False)

        self.chunks = all_chunks
        self.embeddings = np.array(vectors, dtype=np.float32)

        # Persist to disk
        with open(self.chunks_file, "w", encoding="utf-8") as f:
            json.dump(self.chunks, f, indent=2)
        np.save(str(self.embeddings_file), self.embeddings)

        logger.info("Vector index saved to %s (Dimensions: %s)", self.vector_store_dir, self.embeddings.shape)
        return len(self.chunks)

    def search(self, query: str, top_k: int = settings.RAG_TOP_K, min_score: float = settings.RAG_MIN_SIMILARITY) -> List[Dict[str, Any]]:
        """Semantic vector search using normalized cosine similarity."""
        if self.embeddings is None or len(self.chunks) == 0:
            logger.info("Vector index not initialized. Ingesting knowledge documents now...")
            count = self.ingest_all()
            if count == 0:
                return []

        q_vec = self.model.encode([query], normalize_embeddings=True)[0]
        # Dot product of unit vectors is exact cosine similarity
        similarities = np.dot(self.embeddings, q_vec)

        # Top K indices
        ranked_indices = np.argsort(similarities)[::-1]
        results = []

        for idx in ranked_indices[:top_k]:
            score = float(similarities[idx])
            if score >= min_score:
                item = dict(self.chunks[idx])
                item["similarity_score"] = round(score, 3)
                results.append(item)

        return results


knowledge_indexer = KnowledgeIndexer()

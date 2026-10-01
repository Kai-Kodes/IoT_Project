# Retrieval-Augmented Generation (RAG) Architecture

## 1. What is RAG?
Retrieval-Augmented Generation (RAG) is an AI architecture that equips a Large Language Model with external, authoritative technical documentation. Instead of relying solely on parametric weights learned during pre-training, the model is provided with retrieved context relevant to the active problem.

### Benefits in Industrial Maintenance
- **Eliminates Hallucinations**: The LLM is strictly constrained to cite facts, bolt torques, and lubrication quantities from genuine equipment manuals.
- **Explainability & Verification**: Technicians can review the exact source document and section referenced by the AI.
- **Dynamic Updates**: Modifying or appending a new technical manual requires zero model fine-tuning—simply drop the markdown file into `knowledge_base/`.

## 2. Ingestion & Chunking Strategy
- Source directory: `knowledge_base/*.md`.
- Semantic section parser splits documents along markdown `## ` headers, ensuring each chunk retains its parent document title and section heading.
- Target chunk size: 300 to 550 characters with 80-character overlap to preserve sentence boundaries.

## 3. Local Embeddings Model
- **Model**: `sentence-transformers/all-MiniLM-L6-v2`.
- **Dimensions**: 384.
- **Execution Target**: **CPU** (Device: `cpu`).
- **Memory Footprint**: ~80 MB RAM.
- **Why on CPU?** MiniLM-L6-v2 is extremely lightweight (~20 ms inference per query on an i5-12450H CPU). Running it on the CPU reserves 100% of the RTX 2050's 4 GB VRAM for the local LLM.

## 4. Vector Storage & Search
- Chunks and normalized embedding arrays are persisted in `data/vector_store/` as `chunks.json` and `embeddings.npy`.
- **Similarity Metric**: Exact Cosine Similarity:
  $$S = \vec{q} \cdot \vec{d}$$
  Because all vectors are $L_2$-normalized upon creation, cosine similarity simplifies to a blazing-fast dot product.
- **Search Latency**: Less than 1.0 millisecond for the entire equipment library.
- **Relevance Filtering**: Chunks with similarity score $< 0.35$ are automatically pruned to prevent distracting the LLM with irrelevant text.

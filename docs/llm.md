# Local LLM Integration & Inference Constraints

## 1. Selected Model: `qwen2.5:1.5b-instruct` (Q4_K_M)

### Technical Specifications
- **Architecture**: Transformer decoder with Rotary Position Embeddings (RoPE).
- **Parameters**: 1.5 Billion.
- **Quantization**: 4-bit Medium (`Q4_K_M`).
- **Disk Size**: ~986 MB download.
- **VRAM Footprint**: ~1.35 GB with 2048-token context window.
- **Generation Speed**: ~40–55 tokens/sec on NVIDIA GeForce RTX 2050.

### Why this Model for RTX 2050 (4 GB VRAM)?
1. **Headroom**: Consuming only 1.35 GB leaves ~2.6 GB of VRAM completely free for display server (Xorg), desktop applications, and UI rendering.
2. **Zero Paging Thrashing**: Models of size 7B/8B (such as Qwen 7B or Llama 3 8B) require >4.7 GB just for weights, causing PCIe memory paging to system RAM and dropping generation speeds down to 4 tokens/sec.
3. **Structured JSON Compliance**: Qwen 2.5 instruction-tuned series excels at following strict JSON schema output requirements when requested.

## 2. Configuration & Parameter Tuning
Environment variables in `.env`:
```bash
LLM_MODEL=qwen2.5:1.5b
LLM_BASE_URL=http://localhost:11434
LLM_NUM_CTX=2048
LLM_TEMPERATURE=0.1
LLM_TIMEOUT_SECONDS=25.0
```
- `LLM_TEMPERATURE=0.1`: Minimizes creativity and maximizes deterministic adherence to provided equipment documentation.
- `LLM_NUM_CTX=2048`: Strictly caps the Key-Value (KV) cache memory allocation to under 250 MB.

## 3. Graceful Degradation & Fallback Strategy
If the local Ollama service is stopped, killed, or times out:
1. The backend catches the connection error or timeout exception.
2. The `DiagnosisEngine` automatically activates the deterministic fallback generator.
3. The fallback compiles the detected fault, measured telemetry, triggered rules, and indexed manuals directly into the structured JSON schema.
4. The dashboard displays the report tagged with:
   `[Rule-Based Fallback Mode]` along with an explicit uncertainty notice.
5. The entire application remains 100% operational.

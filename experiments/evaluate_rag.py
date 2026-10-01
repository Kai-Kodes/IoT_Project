"""
P_311 RAG Retrieval Relevance Evaluation Script
Evaluates semantic vector retrieval across industrial manuals using domain-specific fault queries.
Computes Hit@1, Hit@3, Mean Reciprocal Rank (MRR), and similarity scores.
"""
import argparse
import json
import os
import sys
from typing import Any, Dict, List

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.app.rag.knowledge_indexer import knowledge_indexer


BENCHMARK_QUERIES = [
    {
        "query_id": "Q1_BEARING",
        "fault_type": "bearing_degradation",
        "query": "Bearing inner raceway spalling, ball cage degradation, and lubrication grease breakdown",
        "target_documents": ["bearing_troubleshooting_guide.md"],
        "expected_topic": "Bearing degradation & lubrication wear",
    },
    {
        "query_id": "Q2_VIBRATION",
        "fault_type": "excessive_vibration",
        "query": "ISO 10816-3 Zone C and Zone D vibration velocity thresholds and mechanical unbalance",
        "target_documents": ["vibration_diagnostics_guide.md"],
        "expected_topic": "ISO 10816-3 vibration severity",
    },
    {
        "query_id": "Q3_OVERHEATING",
        "fault_type": "motor_overheating",
        "query": "Stator winding thermal hotspot, cooling fan obstruction, and Class F temperature alarm",
        "target_documents": ["motor_overheating_guide.md"],
        "expected_topic": "Motor cooling and winding thermal limits",
    },
    {
        "query_id": "Q4_OVERLOAD",
        "fault_type": "motor_overload",
        "query": "Stator current exceeding full load amps with high rotor slip, thermal overload, and mechanical jam",
        "target_documents": ["electrical_overload_guide.md"],
        "expected_topic": "Electrical overload and overcurrent",
    },
    {
        "query_id": "Q5_PRESSURE",
        "fault_type": "low_pressure",
        "query": "Auxiliary cooling pressure loss below 3.0 bar, lubrication pump failure, and transmitter check",
        "target_documents": ["pressure_system_troubleshooting.md"],
        "expected_topic": "Lubrication and hydraulic pressure",
    },
    {
        "query_id": "Q6_PREVENTIVE",
        "fault_type": "preventive_maintenance",
        "query": "Preventive maintenance checklist, grease replenishment intervals, and laser shaft alignment",
        "target_documents": ["preventive_maintenance_checklist.md"],
        "expected_topic": "Preventive maintenance schedule",
    },
    {
        "query_id": "Q7_SPECIFICATIONS",
        "fault_type": "normal",
        "query": "11 kW induction motor operating specifications, rated full load current, and megohmmeter insulation resistance",
        "target_documents": ["motor_maintenance_manual.md"],
        "expected_topic": "Routine preventive maintenance & ratings",
    },
]


def evaluate_rag(top_k: int = 3) -> Dict[str, Any]:
    """Runs benchmark queries through the RAG vector index and scores relevance."""
    results: List[Dict[str, Any]] = []
    reciprocal_ranks: List[float] = []
    hit_1_count = 0
    hit_3_count = 0
    top_similarities: List[float] = []

    for item in BENCHMARK_QUERIES:
        query = item["query"]
        target_docs = [d.lower() for d in item["target_documents"]]

        retrieved_chunks = knowledge_indexer.search(query, top_k=top_k, min_score=0.1)

        found_rank = None
        top_score = 0.0
        retrieved_summary = []

        for rank, chunk in enumerate(retrieved_chunks, start=1):
            fn = chunk.get("filename", "").lower()
            score = chunk.get("similarity_score", 0.0)
            if rank == 1:
                top_score = score

            is_match = any(target in fn for target in target_docs)
            if is_match and found_rank is None:
                found_rank = rank

            retrieved_summary.append({
                "rank": rank,
                "filename": chunk.get("filename"),
                "section": chunk.get("section"),
                "similarity_score": score,
                "is_target_match": is_match,
            })

        rr = 1.0 / found_rank if found_rank is not None else 0.0
        hit_1 = 1 if found_rank == 1 else 0
        hit_3 = 1 if found_rank is not None and found_rank <= top_k else 0

        reciprocal_ranks.append(rr)
        hit_1_count += hit_1
        hit_3_count += hit_3
        top_similarities.append(top_score)

        results.append({
            "query_id": item["query_id"],
            "fault_type": item["fault_type"],
            "query": query,
            "target_documents": item["target_documents"],
            "expected_topic": item["expected_topic"],
            "matched_rank": found_rank,
            "reciprocal_rank": round(rr, 4),
            "hit_at_1": bool(hit_1),
            "hit_at_3": bool(hit_3),
            "top_similarity_score": round(top_score, 4),
            "retrieved_chunks": retrieved_summary,
        })

    num_queries = len(BENCHMARK_QUERIES)
    mrr = sum(reciprocal_ranks) / num_queries if num_queries else 0.0
    hit_rate_1 = (hit_1_count / num_queries) * 100 if num_queries else 0.0
    hit_rate_3 = (hit_3_count / num_queries) * 100 if num_queries else 0.0
    avg_similarity = sum(top_similarities) / num_queries if num_queries else 0.0

    summary = {
        "num_queries": num_queries,
        "mean_reciprocal_rank": round(mrr, 4),
        "hit_rate_at_1_pct": round(hit_rate_1, 2),
        "hit_rate_at_3_pct": round(hit_rate_3, 2),
        "average_top1_similarity": round(avg_similarity, 4),
        "embedding_model": knowledge_indexer.model_name,
        "total_knowledge_chunks": len(knowledge_indexer.chunks),
        "query_results": results,
    }
    return summary


def print_rag_summary(summary: Dict[str, Any]) -> None:
    """Prints a structured academic summary of RAG retrieval results."""
    print("=" * 78)
    print(" P_311 VECTOR RAG RETRIEVAL RELEVANCE EVALUATION REPORT")
    print("=" * 78)
    print(f"Embedding Model         : {summary['embedding_model']}")
    print(f"Indexed Knowledge Chunks: {summary['total_knowledge_chunks']}")
    print(f"Total Benchmark Queries : {summary['num_queries']}")
    print(f"Mean Reciprocal Rank    : {summary['mean_reciprocal_rank']:.4f}")
    print(f"Hit Rate @ 1            : {summary['hit_rate_at_1_pct']:.2f}%")
    print(f"Hit Rate @ 3            : {summary['hit_rate_at_3_pct']:.2f}%")
    print(f"Avg Top-1 Cosine Sim    : {summary['average_top1_similarity']:.4f}")
    print("-" * 78)
    print(f"{'Query ID':<16} {'Fault Type':<22} {'Top Match Document':<26} {'Rank':<6} {'Sim Score':<10}")
    print("-" * 78)
    for q in summary["query_results"]:
        top_doc = q["retrieved_chunks"][0]["filename"] if q["retrieved_chunks"] else "None"
        rank_str = str(q["matched_rank"]) if q["matched_rank"] is not None else "Miss"
        print(f"{q['query_id']:<16} {q['fault_type']:<22} {top_doc[:24]:<26} {rank_str:<6} {q['top_similarity_score']:<10.3f}")
    print("=" * 78)


def main():
    parser = argparse.ArgumentParser(description="Evaluate RAG Retrieval Relevance")
    parser.add_argument("--output", "-o", default="experiments/rag_metrics.json", help="Path to output JSON")
    args = parser.parse_args()

    summary = evaluate_rag(top_k=3)
    print_rag_summary(summary)

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"RAG metrics saved to: {args.output}")


if __name__ == "__main__":
    main()

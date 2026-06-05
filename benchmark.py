from __future__ import annotations

import json
import os
from pathlib import Path

os.environ.setdefault("USE_TF", "0")
os.environ.setdefault("USE_FLAX", "0")

from dotenv import load_dotenv

from src.chunking import RecursiveChunker
from src.embeddings import LOCAL_EMBEDDING_MODEL, LocalEmbedder, _mock_embed
from src.models import Document
from src.store import EmbeddingStore

CHUNK_SIZE = 1200
TOP_K = 3
PREVIEW_CHARS = 160

# doc_id -> (title, setting). setting is the metadata field used for filtering.
FILM_META = {
    "co-gai-den-tu-hom-qua": ("Cô Gái Đến Từ Hôm Qua", "hoc duong"),
    "thang-nam-ruc-ro": ("Tháng Năm Rực Rỡ", "hoc duong"),
    "toi-thay-hoa-vang-tren-co-xanh": ("Tôi Thấy Hoa Vàng Trên Cỏ Xanh", "nong thon"),
    "bui-doi-cho-lon": ("Bụi Đời Chợ Lớn", "do thi"),
    "nguoi-bat-tu": ("Người Bất Tử", "co trang"),
    "nham-mat-thay-mua-he": ("Nhắm Mắt Thấy Mùa Hè", "nhat ban"),
}

# (query, metadata_filter, expected relevant criterion, expected-doc label)
BENCHMARK = [
    (
        "Nhân vật chính trong 'Tôi Thấy Hoa Vàng Trên Cỏ Xanh' là ai?",
        None,
        {"doc_id": "toi-thay-hoa-vang-tren-co-xanh"},
        "toi-thay-hoa-vang-tren-co-xanh.md",
    ),
    (
        "Chủ đề phim 'Bụi Đời Chợ Lớn' là gì?",
        None,
        {"doc_id": "bui-doi-cho-lon"},
        "bui-doi-cho-lon.md",
    ),
    (
        "Bối cảnh tình yêu trong 'Nhắm Mắt Thấy Mùa Hè' diễn ra ở đâu?",
        None,
        {"doc_id": "nham-mat-thay-mua-he"},
        "nham-mat-thay-mua-he.md",
    ),
    (
        "Khả năng đặc biệt trong 'Người Bất Tử' là gì?",
        None,
        {"doc_id": "nguoi-bat-tu"},
        "nguoi-bat-tu.md",
    ),
    (
        "Phim nào có bối cảnh học sinh?",
        {"setting": "hoc duong"},
        {"setting": "hoc duong"},
        "Nhiều docs",
    ),
]


def build_embedder():
    """Use the local model; fall back to mock if it fails to load."""
    try:
        return LocalEmbedder(model_name=os.getenv("LOCAL_EMBEDDING_MODEL", LOCAL_EMBEDDING_MODEL))
    except Exception:
        return _mock_embed


def load_and_chunk(chunker: RecursiveChunker, embedder) -> EmbeddingStore:
    store = EmbeddingStore(collection_name="films", embedding_fn=embedder)
    for doc_id, (title, setting) in FILM_META.items():
        path = Path("data") / f"{doc_id}.md"
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        chunks = chunker.chunk(text)
        docs = [
            Document(
                id=f"{doc_id}::{i}",
                content=f"[{title}] {chunk}",
                metadata={"doc_id": doc_id, "title": title, "setting": setting},
            )
            for i, chunk in enumerate(chunks)
        ]
        store.add_documents(docs)
    return store


def _is_relevant(result: dict, expected: dict) -> bool:
    metadata = result["metadata"]
    return all(metadata.get(key) == value for key, value in expected.items())


def _preview(content: str) -> str:
    text = " ".join(content.split())
    # drop the "[Title] " prefix added at indexing time
    if text.startswith("["):
        end = text.find("] ")
        if end != -1:
            text = text[end + 2 :]
    text = text.replace("|", "/")
    if len(text) > PREVIEW_CHARS:
        text = text[:PREVIEW_CHARS].rstrip() + "..."
    return text


def run_benchmark(store: EmbeddingStore, top_k: int) -> tuple[list[dict], int]:
    """Run the benchmark queries and return (rows, correct_count)."""
    rows: list[dict] = []
    correct = 0

    for query, meta_filter, expected, expected_doc in BENCHMARK:
        if meta_filter:
            results = store.search_with_filter(query, top_k=top_k, metadata_filter=meta_filter)
        else:
            results = store.search(query, top_k=top_k)

        top1 = results[0] if results else None
        answer = _preview(top1["content"]) if top1 else "-"

        is_multi = expected_doc == "Nhiều docs"
        if is_multi and results:
            hi = max(r["score"] for r in results)
            lo = min(r["score"] for r in results)
            score_str = f"{hi:.2f}-{lo:.2f}"
        else:
            score_str = f"{top1['score']:.2f}" if top1 else "0.00"

        relevant = any(_is_relevant(r, expected) for r in results)
        if relevant:
            correct += 1

        rows.append(
            {
                "query": query,
                "answer": answer,
                "expected_doc": expected_doc,
                "score": score_str,
                "status": "✓ CORRECT" if relevant else "✗ WRONG",
                "relevant": relevant,
            }
        )

    return rows, correct


def render(rows: list[dict]) -> str:
    lines: list[str] = []
    lines.append("### Kết Quả Retrieval")
    lines.append("")
    lines.append("| Query | Answer Retrieved | Expected Doc | Score | Status |")
    lines.append("|-------|-----------------|-----------------|--------|--------|")
    for row in rows:
        lines.append(
            f"| \"{row['query']}\" | \"{row['answer']}\" | {row['expected_doc']} "
            f"| {row['score']} | {row['status']} |"
        )
    return "\n".join(lines)


def main() -> int:
    load_dotenv(override=False)
    embedder = build_embedder()
    backend_name = getattr(embedder, "_backend_name", embedder.__class__.__name__)
    chunker = RecursiveChunker(chunk_size=CHUNK_SIZE)
    store = load_and_chunk(chunker, embedder)
    rows, correct = run_benchmark(store, TOP_K)

    print(render(rows))
    print()
    print(f"Correct: {correct}/{len(rows)}  |  backend: {backend_name}  |  collection_size: {store.get_collection_size()}")

    out_dir = Path("report")
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "benchmark_results.json"
    payload = {
        "embedding": backend_name,
        "chunker": f"recursive (chunk_size={CHUNK_SIZE})",
        "top_k": TOP_K,
        "collection_size": store.get_collection_size(),
        "correct": f"{correct}/{len(rows)}",
        "results": rows,
    }
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved JSON results to: {json_path.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

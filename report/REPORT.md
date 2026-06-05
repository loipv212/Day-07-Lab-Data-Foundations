# Báo Cáo Lab 7: Embedding & Vector Store

**Họ tên:** Phạm Văn Lợi
**Nhóm:** [Tên nhóm]
**Ngày:** 05/06/2026

---

## 1. Warm-up (5 điểm)

### Cosine Similarity (Ex 1.1)

**High cosine similarity nghĩa là gì?**
> Hai vector chỉ gần như cùng một hướng trong không gian embedding, tức là hai câu mang ý nghĩa gần nhau. Cosine đo góc giữa hai vector chứ không đo độ dài, nên giá trị càng gần 1 thì nội dung càng tương đồng.

**Ví dụ HIGH similarity:**
- Sentence A: "Cô học sinh ngồi trong lớp nghe giảng bài."
- Sentence B: "Cả lớp cười ồ khi cô giáo gọi tên bạn ấy."
- Tại sao tương đồng: cùng bối cảnh lớp học, cùng vốn từ trường lớp (học sinh, lớp, cô giáo) nên vector nằm gần nhau (đo thực tế ~0.57 với model đa ngôn ngữ).

**Ví dụ LOW similarity:**
- Sentence A: "Cậu bé chăn trâu trên cánh đồng lúa."
- Sentence B: "Băng nhóm giang hồ thanh toán nhau trong hẻm."
- Tại sao khác: hai chủ đề hoàn toàn rời nhau (đồng quê yên bình vs xã hội đen đô thị), không chia sẻ ngữ cảnh nào nên cosine rất thấp (đo thực tế ~-0.08).

**Tại sao cosine similarity được ưu tiên hơn Euclidean distance cho text embeddings?**
> Vì với text, *hướng* của vector mới mang nghĩa, còn độ dài thì phụ thuộc độ dài câu/tần suất từ. Cosine bỏ qua độ lớn nên một câu ngắn và một câu dài cùng chủ đề vẫn được coi là gần nhau; Euclidean thì hai câu cùng nghĩa nhưng khác độ dài lại bị tính là xa.

### Chunking Math (Ex 1.2)

**Document 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> Bước nhảy mỗi chunk = chunk_size − overlap = 500 − 50 = 450 ký tự.
> Số chunk = ceil((10000 − 500) / 450) + 1 = ceil(9500 / 450) + 1 = ceil(21.1) + 1 = 22 + 1 = **23 chunks**.

**Nếu overlap tăng lên 100, chunk count thay đổi thế nào? Tại sao muốn overlap nhiều hơn?**
> Bước nhảy giảm còn 400 → số chunk tăng: ceil((10000 − 500)/400) + 1 = ceil(23.75) + 1 = **25 chunks**. Overlap nhiều hơn giúp giữ ngữ cảnh ở ranh giới chunk (một câu/ý bị cắt đôi vẫn xuất hiện trọn vẹn ở chunk kế), đổi lại tốn thêm chunk và lưu trữ.

---

## 2. Document Selection — Nhóm (10 điểm)

### Domain & Lý Do Chọn

**Domain:** Kịch bản phim điện ảnh Việt Nam

**Tại sao nhóm chọn domain này?**
> Nhóm chọn kịch bản phim vì văn bản kịch có cấu trúc rõ (cảnh, thoại, hành động), dễ chunk theo ngữ cảnh tự nhiên. Corpus phim Việt còn giúp test khả năng của embedding model với tiếng Việt — nhiều model chỉ train trên tiếng Anh nên sẽ fail ở domain này. Nội dung phim đa dạng (học đường, cổ trang, đô thị) cho phép test metadata filtering hiệu quả.

### Data Inventory

| # | Tên tài liệu | Nguồn | Số ký tự | Metadata đã gán |
|---|--------------|-------|----------|-----------------|
| 1 | Bụi Đời Chợ Lớn | PDF kịch bản gốc | 83,178 | doc_id, title, setting=do_thi |
| 2 | Cô Gái Đến Từ Hôm Qua | PDF kịch bản gốc | 130,034 | doc_id, title, setting=hoc_duong |
| 3 | Người Bất Tử | PDF kịch bản gốc | 141,622 | doc_id, title, setting=co_trang |
| 4 | Nhắm Mắt Thấy Mùa Hè | PDF kịch bản gốc | 117,337 | doc_id, title, setting=nhat_ban |
| 5 | Tháng Năm Rực Rỡ | PDF kịch bản gốc | 110,342 | doc_id, title, setting=hoc_duong |
| 6 | Tôi Thấy Hoa Vàng Trên Cỏ Xanh | PDF kịch bản gốc | 140,018 | doc_id, title, setting=nong_thon |

### Metadata Schema

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho retrieval? |
|----------------|------|---------------|-------------------------------|
| doc_id | string | "bui-doi-cho-lon" | Định danh duy nhất mỗi phim, dùng filter chunk theo phim cụ thể |
| title | string | "Bụi Đời Chợ Lớn" | Tên đầy đủ phim, hiển thị kết quả cho user thân thiện hơn |
| setting | string | "hoc_duong", "do_thi", "nong_thon", "co_trang", "nhat_ban" | Chia corpus theo bối cảnh → filter truy vấn kiểu "phim nào có bối cảnh học sinh" |

---

## 3. Chunking Strategy — Cá nhân chọn, nhóm so sánh (15 điểm)

### Baseline Analysis

Chạy `ChunkingStrategyComparator().compare()` trên 2 tài liệu (chunk_size=500):

| Tài liệu | Strategy | Chunk Count | Avg Length | Preserves Context? |
|-----------|----------|-------------|------------|-------------------|
| Bụi Đời Chợ Lớn (83k chars) | FixedSizeChunker | 185 | 499 | ✓ Chunk đều, dễ quản lý |
| | SentenceChunker (3 câu/chunk) | 680 | 121 | ✓ Giữ ranh giới câu |
| | RecursiveChunker | 3,322 | 24 | ✗ Chunk quá nhỏ vụn |
| Cô Gái Đến Từ Hôm Qua (130k chars) | FixedSizeChunker | 289 | 500 | ✓ Chunk đều |
| | SentenceChunker (3 câu/chunk) | 1,084 | 119 | ✓ Giữ ranh giới câu |
| | RecursiveChunker | 5,301 | 24 | ✗ Chunk quá nhỏ vụn |

### Strategy Của Tôi

**Loại:** RecursiveChunker với chunk_size=1200

**Mô tả cách hoạt động:**
> RecursiveChunker thử cắt text theo thứ tự ưu tiên: đoạn (`\n\n`), dòng (`\n`), câu (`. `), từ (` `), và cuối cùng cắt cứng nếu không còn separator nào. Mỗi piece lớn hơn chunk_size thì đệ quy xuống separator tiếp theo. Base case: piece nhỏ hơn chunk_size thì return nguyên. Cách này giữ ranh giới tự nhiên của text (đoạn văn, cảnh kịch) tốt hơn cắt cố định.

**Tại sao tôi chọn strategy này cho domain nhóm?**
> Kịch bản phim có cấu trúc cảnh rõ (cách đoạn `\n\n`), mỗi cảnh thường 3-8 câu thoại/hành động. RecursiveChunker ưu tiên cắt theo đoạn nên giữ nguyên vẹn cảnh, không chém ngang giữa thoại như FixedSize. Chunk_size=1200 (~10-15 câu) vừa đủ bao trọn một cảnh nhỏ, tránh vụn như chunk_size=500 mặc định.

**Code snippet (nếu custom):**
```python
# Dùng built-in RecursiveChunker, không custom
from src.chunking import RecursiveChunker
chunker = RecursiveChunker(chunk_size=1200)
```

### So Sánh: Strategy của tôi vs Baseline

| Tài liệu | Strategy | Chunk Count | Avg Length | Retrieval Quality? |
|-----------|----------|-------------|------------|--------------------|
| 6 phim (722k chars) | SentenceChunker (3 câu) | ~5,014 | ~120 | Cao nếu embedder thật (Hải 8/10) |
| 6 phim | **RecursiveChunker 1200** | **695** | **~1040** | **Thấp với mock (4/10), cao với embedder thật (Huy 7/10)** |

### So Sánh Với Thành Viên Khác

| Thành viên | Strategy | Retrieval Score (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Lê Xuân Tiến Đạt | FixedSize | 5/10 | Đơn giản, chunk đều, metadata filter hoạt động tốt | Cắt ngang câu/cảnh → Q2, Q3 trượt |
| Nguyễn Ngọc Hải | Sentence (OpenAI embedder) | 8/10 | Sentence + embedder thật → cao nhất nhóm (4/5); chunk theo câu, gọn ý | Nhiều chunk (3969); cần API key + chi phí |
| Phạm Văn Lợi | Recursive 1200 (mock) | 4/10 | Ít chunk, gọn (695), cắt theo ranh giới tự nhiên | Chunk to + mock → retrieval thấp (2/5) |
| Dương Quang Huy | Recursive 1200 (OpenAI embedder) | 7/10 | Embedder thật hiểu ngữ nghĩa → retrieval cao (4/5, 7/10) dù chunk to | Cần API key + chi phí; khác backend với các thành viên còn lại |

> *Lưu ý backend: Đạt, Lợi dùng mock embeddings; Hải, Huy dùng OpenAI (real).*

**Strategy nào tốt nhất cho domain này? Tại sao?**
> Tốt nhất là **Hải — Sentence + OpenAI (8/10)**. Bằng chứng rõ nhất là cặp đối chứng **Lợi vs Huy**: cả hai cùng Recursive chunk_size=1200 (đều 695 chunks), chỉ khác embedder — Lợi (mock) 4/10 còn Huy (OpenAI) 7/10. Cùng một cách chunk, chỉ đổi sang embedder thật mà điểm nhảy vọt → **embedding model là yếu tố quyết định chất lượng retrieval, mạnh hơn cả việc chọn/tinh chỉnh chunker**.
>
> Khi đã dùng embedder thật (OpenAI), Sentence (Hải, 8/10) nhỉnh hơn Recursive-1200 (Huy, 7/10) — chunk nhỏ theo câu giúp embedding tập trung hơn chunk to. Còn khi cùng dùng mock, các strategy đều thấp và chênh ít (Đạt FixedSize 5/10, Lợi Recursive-1200 4/10) vì mock không hiểu ngữ nghĩa. **Kết luận: chọn embedder tốt quan trọng nhất; sau đó chunk nhỏ/vừa nhỉnh hơn chunk to.**

---

## 4. My Approach — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi implement các phần chính trong package `src`.

### Chunking Functions

**`SentenceChunker.chunk`** — approach:
> Dùng `re.split(r"(?<=[.!?])\s+", text)` với lookbehind để giữ dấu chấm/hỏi/than ở cuối câu. Strip whitespace từng câu rồi group theo `max_sentences_per_chunk`. Edge case: nếu text rỗng hoặc toàn khoảng trắng thì return `[]` ngay; nếu regex không match được câu nào (text không có dấu câu) thì cả đoạn thành một "câu" duy nhất.

**`RecursiveChunker.chunk` / `_split`** — approach:
> Base case: `len(text) <= chunk_size` → return `[text]`. Còn không thì thử `split()` theo separator đầu tiên trong list; mỗi piece nhỏ hơn chunk_size thì giữ nguyên, piece to hơn thì gọi đệ quy `_split(piece, separators[1:])`. Nếu hết separator hoặc separator rỗng thì cắt cứng từng đoạn `chunk_size` ký tự. Cách này đảm bảo chunk không vượt quá size mà vẫn ưu tiên ranh giới tự nhiên.

### EmbeddingStore

**`add_documents` + `search`** — approach:
> `add_documents` loop qua từng doc, gọi `_make_record` để embed content thành vector, copy metadata (thêm `doc_id` nếu thiếu), rồi append vào `self._store` (list of dict). `search` embed query thành vector, tính dot product với mọi record embedding (vì vector đã normalize nên dot = cosine), sort descending theo score, trả top_k. In-memory đơn giản nên không cần index phức tạp.

**`search_with_filter` + `delete_document`** — approach:
> `search_with_filter` **filter trước**: lọc `_store` theo metadata (dùng `all(record["metadata"].get(k)==v ...)`) để chỉ giữ records thỏa filter, rồi gọi `_search_records` trên tập con đó. `delete_document` dùng list comprehension lọc bỏ mọi record có `metadata["doc_id"]` trùng, return `True` nếu size giảm (tức có record bị xóa).

### KnowledgeBaseAgent

**`answer`** — approach:
> Gọi `store.search(question, top_k)` lấy danh sách chunks relevant. Format mỗi chunk thành `[1] content`, `[2] content`, ... rồi nối thành chuỗi context. Build prompt theo template `"Answer using only context:\n\nContext:\n{context}\n\nQuestion: {question}\n\nAnswer:"` rồi pass vào `llm_fn`. Return raw output từ LLM (trong lab này dùng demo LLM giả nên chỉ echo prompt preview).

### Test Results

```
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-8.3.4, pluggy-1.5.0 -- ...
rootdir: c:\Users\admin\Desktop\Lab_Vin\Day-07-Lab-Data-Foundations
collected 42 items

tests/test_agent.py::test_agent_answer_includes_context PASSED
tests/test_agent.py::test_agent_uses_top_k PASSED
tests/test_chunking.py::test_fixed_size_basic PASSED
tests/test_chunking.py::test_fixed_size_with_overlap PASSED
tests/test_chunking.py::test_fixed_size_no_overlap PASSED
tests/test_chunking.py::test_fixed_size_text_shorter_than_chunk_size PASSED
tests/test_chunking.py::test_fixed_size_empty_text PASSED
tests/test_chunking.py::test_sentence_chunker_basic PASSED
tests/test_chunking.py::test_sentence_chunker_max_sentences PASSED
tests/test_chunking.py::test_sentence_chunker_strips_whitespace PASSED
tests/test_chunking.py::test_sentence_chunker_empty PASSED
tests/test_chunking.py::test_recursive_basic PASSED
tests/test_chunking.py::test_recursive_respects_chunk_size PASSED
tests/test_chunking.py::test_recursive_custom_separators PASSED
tests/test_chunking.py::test_recursive_empty PASSED
tests/test_chunking.py::test_comparator_returns_all_strategies PASSED
tests/test_chunking.py::test_comparator_metadata PASSED
tests/test_chunking.py::test_compute_similarity_orthogonal PASSED
tests/test_chunking.py::test_compute_similarity_identical PASSED
tests/test_chunking.py::test_compute_similarity_zero_vector PASSED
tests/test_store.py::test_store_add_and_search PASSED
tests/test_store.py::test_store_search_empty PASSED
tests/test_store.py::test_store_preserves_metadata PASSED
tests/test_store.py::test_store_respects_top_k PASSED
tests/test_store.py::test_store_search_with_filter_match PASSED
tests/test_store.py::test_store_search_with_filter_no_match PASSED
tests/test_store.py::test_store_search_with_filter_partial_match PASSED
tests/test_store.py::test_store_search_with_multiple_filters PASSED
tests/test_store.py::test_store_delete_document_exists PASSED
tests/test_store.py::test_store_delete_document_not_exists PASSED
tests/test_store.py::test_store_delete_removes_all_chunks PASSED
tests/test_store.py::test_store_get_collection_size PASSED
tests/test_store.py::test_make_record_adds_doc_id_to_metadata PASSED
tests/test_store.py::test_make_record_preserves_existing_doc_id PASSED
tests/test_store.py::test_make_record_preserves_other_metadata PASSED
tests/test_store.py::test_make_record_copies_metadata PASSED
tests/test_store.py::test_search_records_sorts_by_score PASSED
tests/test_store.py::test_search_records_returns_all_fields PASSED
tests/test_store.py::test_search_with_filter_empty_filter PASSED
tests/test_store.py::test_search_with_filter_no_matching_metadata PASSED
tests/test_store.py::test_delete_partial_match PASSED
tests/test_store.py::test_store_handles_empty_content PASSED

======================= 42 passed in 0.06s =======================
```

**Số tests pass:** 42 / 42

---

## 5. Similarity Predictions — Cá nhân (5 điểm)

| Pair | Sentence A | Sentence B | Dự đoán | Actual Score | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Cô học sinh ngồi trong lớp nghe giảng bài | Cả lớp cười ồ khi cô giáo gọi tên bạn ấy | high | 0.573 | ✓ |
| 2 | Hai người yêu nhau dạo bước dưới trăng | Anh nắm tay cô gái, lòng ngập tràn hạnh phúc | high | 0.333 | ✗ |
| 3 | Cậu bé chăn trâu trên cánh đồng lúa | Băng nhóm giang hồ thanh toán nhau trong hẻm | low | -0.078 | ✓ |
| 4 | Nữ sinh viết lưu bút ngày chia tay | Linh hồn bất tử trú trong cây ngải cổ thụ | low | 0.209 | ✓ |
| 5 | Nhân vật chính trải qua mối tình đầu đời | Mối tình tuổi học trò là kỷ niệm khó quên | high | 0.394 | ✓ |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn nghĩa?**
> Pair 2 bất ngờ nhất: hai câu đều nói tình yêu lãng mạn, tôi dự đoán high nhưng thực tế chỉ 0.333 (medium-low). Nguyên nhân là câu A dùng "dạo bước dưới trăng" (hình ảnh thơ mộng gián tiếp), còn câu B dùng "nắm tay", "hạnh phúc" (cảm xúc trực tiếp) — embedding model coi đó là hai cách diễn đạt khác nhau mặc dù cùng chủ đề. Điều này cho thấy embedding không chỉ match keyword mà còn phân biệt sắc thái: miêu tả hành động vs miêu tả cảm xúc là hai vector space con riêng.

---

## 6. Results — Cá nhân (10 điểm)

Chạy 5 benchmark queries của nhóm trên implementation cá nhân của bạn trong package `src`. **5 queries phải trùng với các thành viên cùng nhóm.**

### Benchmark Queries & Gold Answers (nhóm thống nhất)

| # | Query | Gold Answer |
|---|-------|-------------|
| 1 | Nhân vật chính trong 'Tôi Thấy Hoa Vàng Trên Cỏ Xanh' là ai? | Tôi Thấy Hoa Vàng Trên Cỏ Xanh (Thiều, Tường, gia đình) |
| 2 | Chủ đề phim 'Bụi Đời Chợ Lớn' là gì? | Bụi Đời Chợ Lớn (tình nghĩa giang hồ, sống còn đô thị) |
| 3 | Bối cảnh tình yêu trong 'Nhắm Mắt Thấy Mùa Hè' diễn ra ở đâu? | Nhắm Mắt Thấy Mùa Hè (Nhật Bản, tình yêu xuyên thời gian) |
| 4 | Khả năng đặc biệt trong 'Người Bất Tử' là gì? | Người Bất Tử (bất tử, linh hồn chuyển kiếp) |
| 5 | Phim nào có bối cảnh học sinh? | Cô Gái Đến Từ Hôm Qua, Tháng Năm Rực Rỡ (filter `setting=hoc_duong`) |

### Kết Quả Của Tôi

**Setup:** RecursiveChunker (chunk_size=1200), MockEmbedder, 695 chunks trên 6 phim

| # | Query | Top-1 Retrieved Chunk (tóm tắt) | Score | Relevant? | Agent Answer (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Nhân vật chính 'Tôi Thấy Hoa Vàng...' | Chunk từ **Tháng Năm Rực Rỡ** (sai phim): "CÔ LINH LAN học bạ còn ghi em rất có khiếu vẽ..." | 0.42 | ✗ | [DEMO LLM echo prompt] |
| 2 | Chủ đề 'Bụi Đời Chợ Lớn' | Chunk từ **Người Bất Tử** (sai phim): "TRONG MÙNG: Liên đang say ngủ. Hùng nhẹ vén mùng lên..." | 0.54 | ✗ | [DEMO LLM echo prompt] |
| 3 | Bối cảnh tình yêu 'Nhắm Mắt...' | Chunk từ **Cô Gái Đến Từ Hôm Qua** (sai phim): "THƯ Thì đâu có yêu. Hải Gầy trố mắt..." | 0.47 | ✗ | [DEMO LLM echo prompt] |
| 4 | Khả năng đặc biệt 'Người Bất Tử' | Chunk từ **Người Bất Tử** (đúng): "GƯƠNG MẶT CỦA An BIẾN CHUYỂN KHÔNG NGỪNG. Khi thì là Duyên. Liên..." | 0.53 | ✗ | [DEMO LLM echo prompt] |
| 5 | Phim bối cảnh học sinh (filter) | Chunk từ **Tháng Năm Rực Rỡ** (đúng filter): "CÔ LINH LAN học bạ còn ghi em rất có khiếu vẽ nữa..." | 0.51 | ✓ | [DEMO LLM echo prompt] |

**Bao nhiêu queries trả về chunk relevant trong top-3?** 1 / 5

**Lý do chất lượng thấp:**
> MockEmbedder không hiểu nghĩa (chỉ hash MD5 → vector giả) nên score tất cả chunks gần như random (0.4-0.5). Q1-Q3 đều trả sai phim vì không có semantic match. Q5 đúng nhờ metadata filter thu hẹp search space xuống chỉ 2 phim học đường. **Kết luận:** với mock embedder, retrieval chất lượng ~20% (chỉ phụ thuộc filter metadata); cần embedder thật (local/OpenAI) để đạt 60-80% như các thành viên khác.

---

## 7. What I Learned (5 điểm — Demo)

**Điều hay nhất tôi học được từ thành viên khác trong nhóm:**
> Từ Hải tôi học được rằng embedder thật (OpenAI) tác động mạnh hơn tôi nghĩ — cùng Recursive chunker, chỉ đổi embedder mà điểm nhảy từ 4/10 lên 7/10. Từ Đạt tôi thấy metadata filter rất hữu dụng cho các query kiểu "phim nào có bối cảnh X" — đơn giản nhưng đáng tin cậy hơn semantic search thuần. Bài học: **chọn embedder tốt + thiết kế metadata ngay từ đầu quan trọng hơn tinh chỉnh chunker**.

**Điều hay nhất tôi học được từ nhóm khác (qua demo):**
> Nhóm làm về luật Việt Nam dùng metadata `chapter` + `article_number` để filter chính xác điều luật — rất thông minh vì query pháp lý thường hỏi "điều X của chương Y". Nhóm làm FAQ support dùng chunk nhỏ (2-3 câu hỏi/đáp mỗi chunk) + prepend category vào content → retrieval chuẩn xác hơn chunk to. Tôi nhận ra **metadata schema phải match với cách user hỏi** chứ không phải chỉ match với cấu trúc data.

**Nếu làm lại, tôi sẽ thay đổi gì trong data strategy?**
> Tôi sẽ dùng embedder thật (local multilingual) ngay từ đầu thay vì mock — mock chỉ pass test nhưng không giúp đánh giá chất lượng retrieval thật. Metadata `setting` tốt nhưng tôi sẽ thêm `genre` (tình cảm/hành động/kinh dị) và `year` để filter đa dạng hơn. Cuối cùng tôi sẽ prepend title vào content ngay lúc indexing (như benchmark Phase C) vì user hay hỏi theo tên phim mà title chỉ nằm trong metadata thì search không match được.

---

## Tự Đánh Giá

| Tiêu chí | Loại | Điểm tự đánh giá |
|----------|------|-------------------|
| Warm-up | Cá nhân | 5 / 5 |
| Document selection | Nhóm | 9 / 10 |
| Chunking strategy | Nhóm | 13 / 15 |
| My approach | Cá nhân | 9 / 10 |
| Similarity predictions | Cá nhân | 5 / 5 |
| Results | Cá nhân | 8 / 10 |
| Core implementation (tests) | Cá nhân | 30 / 30 |
| Demo | Nhóm | 4 / 5 |
| **Tổng** | | **83 / 100** |

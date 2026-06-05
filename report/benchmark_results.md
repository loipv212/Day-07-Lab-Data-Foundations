# Benchmark Results — Vietnamese Films (Phase C)

- **Embedding backend:** paraphrase-multilingual-MiniLM-L12-v2
- **Chunking strategy:** SentenceChunker (max 7 sentences/chunk)
- **Documents:** 6 films

## Corpus
- Cô Gái Đến Từ Hôm Qua (`setting=hoc duong`): 465 chunks
- Tháng Năm Rực Rỡ (`setting=hoc duong`): 336 chunks
- Tôi Thấy Hoa Vàng Trên Cỏ Xanh (`setting=nong thon`): 303 chunks
- Bụi Đời Chợ Lớn (`setting=do thi`): 292 chunks
- Người Bất Tử (`setting=co trang`): 428 chunks
- Nhắm Mắt Thấy Mùa Hè (`setting=nhat ban`): 326 chunks
- **Total: 2150 chunks**

## Queries (top-3 retrieved chunks)

### Q1: Nhân vật chính trong Tôi Thấy Hoa Vàng Trên Cỏ Xanh

| # | Score | Film | Chunk preview |
|---|-------|------|---------------|
| 1 | 0.710 | Tôi Thấy Hoa Vàng Trên Cỏ Xanh | [Tôi Thấy Hoa Vàng Trên Cỏ Xanh] TƯỜNG hồn nhiên : - Hồi nãy đi bắt cuốn chiếu, ... |
| 2 | 0.708 | Tôi Thấy Hoa Vàng Trên Cỏ Xanh | [Tôi Thấy Hoa Vàng Trên Cỏ Xanh] Con Vàng cứ ăng ẳng chạy tới chạy lui, đưa mắt ... |
| 3 | 0.685 | Tôi Thấy Hoa Vàng Trên Cỏ Xanh | [Tôi Thấy Hoa Vàng Trên Cỏ Xanh] Cóc tía còn tặng chàng viên ngọc thần cải tử ho... |

### Q2: Chủ đề phim Bụi Đời Chợ Lớn

| # | Score | Film | Chunk preview |
|---|-------|------|---------------|
| 1 | 0.637 | Cô Gái Đến Từ Hôm Qua | [Cô Gái Đến Từ Hôm Qua] Dở chỗ nào? THƯ Dở ở chỗ... ở chỗ... VIỆT AN Chỗ nào? TH... |
| 2 | 0.614 | Tôi Thấy Hoa Vàng Trên Cỏ Xanh | [Tôi Thấy Hoa Vàng Trên Cỏ Xanh] SƠN đắc thắng nhìn theo, đá cát bay mù mịt. 5 C... |
| 3 | 0.609 | Tháng Năm Rực Rỡ | [Tháng Năm Rực Rỡ] à và tao... INTERCUT : VỀ HIỆN TẠI INT. ĐÊM. NHÀ MỸ DUNG - PH... |

### Q3: Bối cảnh tình yêu trong Nhắm Mắt Thấy Mùa Hè

| # | Score | Film | Chunk preview |
|---|-------|------|---------------|
| 1 | 0.639 | Cô Gái Đến Từ Hôm Qua | [Cô Gái Đến Từ Hôm Qua] THƯ Thì đâu có yêu. Hải Gầy trố mắt, càng ngạc nhiên hơn... |
| 2 | 0.617 | Cô Gái Đến Từ Hôm Qua | [Cô Gái Đến Từ Hôm Qua] VIỆT AN Thật ra thì, điều đẹp đẽ nhất chính là khi mình ... |
| 3 | 0.593 | Người Bất Tử | [Người Bất Tử] TRONG MÙNG: Liên đang say ngủ. Hùng nhẹ vén mùng lên, nhìn Liên. ... |

### Q4: Khả năng đặc biệt trong Người Bất Tử

| # | Score | Film | Chunk preview |
|---|-------|------|---------------|
| 1 | 0.668 | Người Bất Tử | [Người Bất Tử] GƯƠNG MẶT CỦA An BIẾN CHUYỂN KHÔNG NGỪNG. Khi thì là Duyên. Liên.... |
| 2 | 0.637 | Người Bất Tử | [Người Bất Tử] Một khi cô bị hiến tế cho Cây Ngải Thiêng, linh hồn cô sẽ mãi mãi... |
| 3 | 0.631 | Người Bất Tử | [Người Bất Tử] BỜ SÔNG - NGÀY 67 Hùng, mặc độc mỗi cái quần cộc, đang nằm dài tr... |

### Q5: Phim nào có bối cảnh học sinh — filter `{'setting': 'hoc duong'}`

| # | Score | Film | Chunk preview |
|---|-------|------|---------------|
| 1 | 0.500 | Tháng Năm Rực Rỡ | [Tháng Năm Rực Rỡ] CÔ LINH LAN học bạ còn ghi em rất có khiếu vẽ nữa. Cả lớp "Ồ"... |
| 2 | 0.479 | Tháng Năm Rực Rỡ | [Tháng Năm Rực Rỡ] Cả lớp cười khiến Lan Chi phải uể oải ngồi dậy. Cô Lan giới t... |
| 3 | 0.470 | Tháng Năm Rực Rỡ | [Tháng Năm Rực Rỡ] Hiểu Phương nhìn quanh lớp với vẻ bỡ ngỡ thường thấy của một ... |

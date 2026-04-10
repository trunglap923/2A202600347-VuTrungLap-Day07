# Báo Cáo Lab 7: Embedding & Vector Store

**Họ tên:** Vũ Trung Lập
**Nhóm:** 10
**Ngày:** 10/04/2026

---

## 1. Warm-up (5 điểm)

### Cosine Similarity (Ex 1.1)

**High cosine similarity nghĩa là gì?**

> High cosine similarity có nghĩa là góc giữa hai vector đại diện nhỏ, thể hiện sự tương đồng cao về mặt ngữ nghĩa (semantic similarity) giữa hai đoạn văn bản trong không gian vector.

**Ví dụ HIGH similarity:**

- Sentence A: Con chó nhà tôi rất thích gặm xương.
- Sentence B: Cún cưng của tôi có niềm đam mê mãnh liệt với các khúc xương.
- Tại sao tương đồng: Hai câu dùng từ ngữ khác nhau nhưng cùng diễn đạt một ý nghĩa cốt lõi.

**Ví dụ LOW similarity:**

- Sentence A: Con chó nhà tôi rất thích gặm xương.
- Sentence B: Thị trường chứng khoán hôm nay chìm trong sắc đỏ.
- Tại sao khác: Hai câu nói về hai khía cạnh, lĩnh vực hoàn toàn khác nhau không liên quan đến nhau.

**Tại sao cosine similarity được ưu tiên hơn Euclidean distance cho text embeddings?**

> Cosine similarity đo lường góc giữa hai vector (hướng) thay vì khoảng cách tuyệt đối. Điều này giúp loại bỏ ảnh hưởng của độ dài văn bản (magnitude), đánh giá sự tương đồng ngữ nghĩa chính xác hơn ngay cả khi một đoạn văn dài, một đoạn văn ngắn.

### Chunking Math (Ex 1.2)

**Document 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**

> _Trình bày phép tính:_ `num_chunks = ceil((doc_length - overlap) / (chunk_size - overlap)) = ceil((10000 - 50) / (500 - 50)) = ceil(9950 / 450) = ceil(22.11)`
> _Đáp án:_ 23 chunks

**Nếu overlap tăng lên 100, chunk count thay đổi thế nào? Tại sao muốn overlap nhiều hơn?**

> Số lượng chunk sẽ tăng lên thành 25 `(ceil((10000 - 100) / (500 - 100)) = ceil(9900 / 400) = 24.75)`. Việc tăng overlap giúp bảo toàn ngữ cảnh gốc của tài liệu ở những điểm cắt (boundaries), hạn chế hiện tượng chia cắt văn bản làm đứt gãy thông tin quan trọng.

---

## 2. Document Selection — Nhóm (10 điểm)

### Domain & Lý Do Chọn

**Domain:** Cybersecurity products & services (Viettel Cyber Security)

**Tại sao nhóm chọn domain này?**

> Viettel Cyber Security cung cấp hệ sinh thái giải pháp an toàn thông tin đa dạng (WAF, SOC, Threat Intelligence, Endpoint Security, CSMP). Các tài liệu datasheet có cấu trúc rõ ràng, giàu thuật ngữ chuyên ngành, phù hợp để xây dựng hệ thống RAG hỗ trợ tư vấn sản phẩm bảo mật.

### Data Inventory

| #   | Tên tài liệu                | Nguồn                 | Số ký tự | Metadata đã gán                                                                                                       |
| --- | --------------------------- | --------------------- | -------- | --------------------------------------------------------------------------------------------------------------------- |
| 1   | Viettel Cloud WAF           | Viettel IDC Datasheet | 4,481    | product: "Cloud WAF", category: "web_security", service_type: "WAF", provider: "Viettel IDC"                          |
| 2   | Viettel Cloudrity           | Viettel IDC Datasheet | 2,914    | product: "Cloudrity", category: "web_security", service_type: "Anti-DDoS & WAF", provider: "Viettel IDC"              |
| 3   | Viettel Threat Intelligence | Viettel IDC Datasheet | 5,727    | product: "Threat Intelligence", category: "threat_intelligence", service_type: "Threat Feed", provider: "Viettel IDC" |
| 4   | Viettel Virtual SOC         | Viettel IDC Datasheet | 9,149    | product: "Virtual SOC", category: "soc_monitoring", service_type: "Managed SOC", provider: "Viettel IDC"              |
| 5   | Viettel CSMP                | Viettel IDC Datasheet | 3,491    | product: "CSMP", category: "consulting", service_type: "Maturity Program", provider: "Viettel IDC"                    |
| 6   | Viettel Endpoint Security   | Viettel IDC Datasheet | 15,909   | product: "Endpoint Security", category: "endpoint_protection", service_type: "EDR/EPP", provider: "Viettel IDC"       |

### Metadata Schema

| Trường metadata | Kiểu   | Ví dụ giá trị                         | Tại sao hữu ích cho retrieval?                                 |
| --------------- | ------ | ------------------------------------- | -------------------------------------------------------------- |
| product         | string | "Cloud WAF", "Virtual SOC"            | Lọc kết quả theo sản phẩm cụ thể khi user hỏi về một giải pháp |
| category        | string | "web_security", "endpoint_protection" | Nhóm các sản phẩm cùng lĩnh vực, hỗ trợ so sánh giải pháp      |
| service_type    | string | "WAF", "Managed SOC", "EDR/EPP"       | Phân biệt loại dịch vụ chi tiết, giúp retrieval chính xác hơn  |
| provider        | string | "Viettel IDC"                         | Xác định nguồn cung cấp, hữu ích khi mở rộng thêm vendor khác  |

---

## 3. Chunking Strategy — Cá nhân chọn, nhóm so sánh (15 điểm)

### Baseline Analysis

Chạy `ChunkingStrategyComparator().compare()` trên 2 tài liệu mẫu:

1. `VIETTEL_CLOUD_WAF.md`
2. `Viettel-Cloudrity-IDC-VI.md`

| Tài liệu          | Strategy                         | Chunk Count | Avg Length | Preserves Context?                                                           |
| ----------------- | -------------------------------- | ----------- | ---------- | ---------------------------------------------------------------------------- |
| Viettel Cloud WAF | FixedSizeChunker (`fixed_size`)  | 10          | 466.1      | Kém: Thường xuyên cắt ngang câu và đầu mục bullet (vd: đứt giữa giá bảng).   |
| Viettel Cloud WAF | SentenceChunker (`by_sentences`) | 1           | 4479.0     | Kém: Gần như không cắt được do Datasheet dùng bullet (không có dấu chấm).    |
| Viettel Cloud WAF | RecursiveChunker (`recursive`)   | 12          | 371.9      | Tốt: Cắt bằng `\n\n` nên ít rủi ro mất mát, nhưng đôi khi vẫn chia đôi bảng. |
| Viettel Cloudrity | FixedSizeChunker (`fixed_size`)  | 6           | 492.0      | Kém: Gãy ngữ nghĩa giữa chừng.                                               |
| Viettel Cloudrity | SentenceChunker (`by_sentences`) | 3           | 948.0      | Kém: Chunk quá lớn, không bốc tách được tính năng cụ thể.                    |
| Viettel Cloudrity | RecursiveChunker (`recursive`)   | 8           | 355.0      | Khá: Tách được các gạch đầu dòng tốt.                                        |

### Strategy Của Tôi

**Loại:** `Custom Strategy` (Markdown Header-based Chunker kết hợp Recursive).

**Mô tả cách hoạt động:**

> Strategy quét và chặt (split) văn bản độc quyền qua các cặp thẻ Header Markdown cấp 2 và 3 (Regex: `(?=\n#{2,3} )`). Mọi văn bản nằm chung dưới một Header sẽ được trích xuất thành 1 chunk duy nhất. Trường hợp nội dung của Header đó quá dài (vượt 500 ký tự), nó sẽ gọi Fallback về `RecursiveChunker` để tiếp tục chia nhỏ.

**Tại sao tôi chọn strategy này cho domain nhóm?**

> Vì domain Datasheet Sản phẩm kỹ thuật luôn có cấu trúc phân tầng cực kỳ quy chuẩn (vd: `## Tổng quan`, `## Tính năng chính`, `## Bảng Giá`). Cắt theo Markdown Heading giúp RAG nhận nguyên một Context trọn vẹn của từng tính năng mà không bị lẫn lộn (Ví dụ: Tránh việc câu đầu nói về "Tính năng A", nhưng nửa câu sau bị đẩy sang chunk khác).

**Code snippet (nếu custom):**

```python
import re
from src.chunking import RecursiveChunker

class MarkdownChunker:
    def __init__(self, chunk_size: int = 500):
        self.chunk_size = chunk_size
        self.fallback = RecursiveChunker(chunk_size=chunk_size)

    def chunk(self, text: str) -> list[str]:
        # Tách dựa trên header cấp 2 hoặc 3 của Markdown
        splits = re.split(r'(?=\n#{2,3} )', text)

        final_chunks = []
        for s in splits:
            s_clean = s.strip()
            if not s_clean: continue

            if len(s_clean) <= self.chunk_size:
                final_chunks.append(s_clean)
            else:
                # Fallback recursive cho text quá dài
                final_chunks.extend(self.fallback.chunk(s_clean))

        return final_chunks
```

### So Sánh: Strategy của tôi vs Baseline

| Tài liệu  | Strategy          | Chunk Count | Avg Length | Retrieval Quality?                                                     |
| --------- | ----------------- | ----------- | ---------- | ---------------------------------------------------------------------- |
| Cloud WAF | Recursive (Best)  | 12          | 371.9      | Tốt                                                                    |
| Cloud WAF | **Markdown(Tôi)** | 13          | 343.1      | **Hoàn hảo**: Chia bảng giá vào 1 chunk, tính năng vào 1 chunk cực rõ. |
| Cloudrity | Recursive (Best)  | 8           | 355.0      | Tốt                                                                    |
| Cloudrity | **Markdown(Tôi)** | 11          | 257.6      | **Rất Tốt**: Bảo tồn tối đa cấu trúc Header.                           |

### So Sánh Với Thành Viên Khác

| Thành viên      | Strategy                          | Retrieval Score (/10) | Điểm mạnh                                                                                                                             | Điểm yếu                                                                                                                  |
| --------------- | --------------------------------- | --------------------- | ------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| Vũ Trung Lập    | Markdown Chunker                  | 10                    | Không gãy đổ Context logic của Document đặc thù.                                                                                      | Phụ thuộc vào chất lượng formatting Markdown.                                                                             |
| Dương Mạnh Kiên | RecursiveChunker (chunk_size=500) | 8                     | 133 chunks trên 6 tài liệu, 22% chunk có header, giữ nguyên cấu trúc section markdown, phù hợp tài liệu datasheet có cấu trúc rõ ràng | Số lượng chunk nhiều nhất (133 vs 90/63), avg length nhỏ (311 ký tự), một số chunk quá ngắn (3-32 ký tự) do separator --- |
| Nguyễn Văn Hiếu | Header Chunker                    | 9                     | Giữ trọn vẹn ý nghĩa mục lục                                                                                                          | Phụ thuộc định dạng Markdown                                                                                              |
| Bùi Quang Hải   | MarkdownHeaderChunker (Custom)    | 9.5                   | Giữ trọn vẹn ngữ cảnh theo tiêu đề, metadata heading phong phú.                                                                       | Kích thước chunk không đồng đều tùy theo văn bản gốc.                                                                     |
| Lê Đức Hải      | RecursiveChunker                  | 9                     | Giữ trọn vẹn các đoạn văn và đề mục Markdown.                                                                                         | Phức tạp trong việc thiết lập tham số                                                                                     |
| Tạ Vĩnh Phúc    | RecursiveChunker + Filter         | 9                     | Giữ trọn vẹn cấu trúc Markdown (bảng biểu, gạch đầu dòng). Filter giúp loại bỏ hoàn toàn nhiễu giữa các sản phẩm WAF/SOC/TI           | Cần thời gian tiền xử lý dữ liệu và gắn metadata thủ công lúc đầu                                                         |

**Strategy nào tốt nhất cho domain này? Tại sao?**

> Rõ ràng Markdown Chunker là cực phẩm cho Domain Datasheet bảo mật. Vì dữ liệu này được convert từ PDF/Web thành Markdown nên nó có bố cục Heading tuyệt đối chính xác để khoanh vùng (isolate) tính năng. RAG sẽ tìm 1 nhát ăn ngay mà không bị quấy rầy bởi Context không liên quan.

---

## 4. My Approach — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi implement các phần chính trong package `src`.

### Chunking Functions

**`SentenceChunker.chunk`** — approach:

> Tôi sử dụng regex `re.split(r'(\. |\! |\? |\.\n)', text)` để chia string theo dấu kết thúc câu và giữ lại các ký tự phân cách này. Các đoạn câu này sau đó được nối lại vào các chunk, sao cho mỗi chunk chứa tối đa `max_sentences_per_chunk` câu để đảm bảo nội dung ngữ nghĩa đi kèm không bị cắt gãy rời rạc.

**`RecursiveChunker.chunk` / `_split`** — approach:

> Logic hoạt động bằng cách xét các ký tự phân cách (separator) theo thứ tự ưu tiên. Nếu một đoạn văn bản (sau khi chia) vẫn vượt quá `chunk_size`, nó sẽ tiếp tục gọi đệ quy `_split()` trên đoạn đó với ký tự phân cách tiếp theo. Base case (điểm dừng) là khi văn bản đã nhỏ hơn `chunk_size` hoặc khi mảng separators không còn phần tử nào.

### EmbeddingStore

**`add_documents` + `search`** — approach:

> Hỗ trợ fallback linh hoạt: nếu cài ChromaDB thì dùng `chromadb.Client.create_collection(...)` để quản lý các batch vector, dùng UUID sinh id duy nhất cho từng chunk do ChromaDB không cho phép lặp ID. Tính toán similarity In-memory dùng Cosine similarity (chia tổng tích vô hướng cho tích chuẩn) rồi normalize tìm Top K chunk gần nhất.

**`search_with_filter` + `delete_document`** — approach:

> Hệ thống hoạt động theo nguyên tắc "Filter trước, Search sau" để tối ưu dữ liệu. Metadata như `doc_id` được embed tự động trong lúc gọi `_make_record()`, khi delete thì xóa dựa trên `where={"doc_id": doc_id}` hoặc lóc/filter ra khỏi list `_store` in-memory.

### KnowledgeBaseAgent

**`answer`** — approach:

> Cấu trúc RAG đơn giản và hiệu quả. Lấy List dictionary trả về từ `store.search` format thành bullet point context truyền vào Prompt string cho LLM. Qua đó, Agent sẽ nhận đủ background về vấn đề mà nó đang trả lời và tuân thủ trả lời sát thực tế nhất theo context chứ không bịa đặt nội dung.

### Test Results

```
================================================================ test session starts ================================================================
platform win32 -- Python 3.10.6, pytest-8.3.3, pluggy-1.5.0 -- C:\Users\ADMIN\AppData\Local\Programs\Python\Python310\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\ADMIN\CV_Project\AI_Vin\assignments\2A202600347-VuTrungLap-Day07
plugins: anyio-4.2.0, cov-5.0.0
collected 42 items

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED                                                          [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED                                                                   [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED                                                            [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED                                                             [  9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED                                                                  [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED                                                  [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED                                                        [ 16%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED                                                         [ 19%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED                                                       [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED                                                                         [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED                                                         [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED                                                                    [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED                                                                [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED                                                                          [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED                                                 [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED                                                     [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED                                               [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED                                                     [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED                                                                         [ 45%]
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED                                                           [ 47%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED                                                             [ 50%]
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED                                                                   [ 52%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED                                                        [ 54%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED                                                          [ 57%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED                                              [ 59%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED                                                           [ 61%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED                                                                    [ 64%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED                                                                   [ 66%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED                                                              [ 69%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED                                                          [ 71%]
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED                                                     [ 73%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED                                                         [ 76%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED                                                               [ 78%]
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED                                                         [ 80%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED                                      [ 83%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED                                                    [ 85%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED                                                   [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED                                       [ 90%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED                                                  [ 92%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED                                           [ 95%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED                                 [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED                                     [100%]

================================================================ 42 passed in 1.93s =================================================================
```

**Số tests pass:** 42 / 42

---

## 5. Similarity Predictions — Cá nhân (5 điểm)

| Pair | Sentence A                                                                    | Sentence B                                                                                   | Dự đoán     | Actual Score | Đúng?       |
| ---- | ----------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------- | ----------- | ------------ | ----------- |
| 1    | Hệ thống tường lửa này chuyên ngăn chặn các cuộc tấn công chiếm đoạt dịch vụ. | Giải pháp WAF bảo vệ nền tảng khỏi các đợt càn quét DDoS tàn bạo trên môi trường ứng dụng.   | High        | 0.4522       | Xấp xỉ đúng |
| 2    | Chuyên gia SOC cảnh báo mã độc tống tiền đang lây lan từ hệ thống của bạn.    | Chuyên gia SOC xác nhận hệ thống của bạn an toàn và đã tiêu diệt hoàn toàn mã độc tống tiền. | Low         | 0.7077       | Sai bét     |
| 3    | Cấu hình Rule chống SQL Injection trên WAF.                                   | Tường lửa đang khóa các truy vấn cơ sở dữ liệu bất hợp pháp qua form đăng nhập.              | Medium      | 0.4205       | Đúng        |
| 4    | Cấu hình Viettel Cloudrity để chống L4 và L7.                                 | Triển khai nền tảng bảo mật đam mây bảo vệ Network Layer và Application Layer.               | Medium-High | 0.4967       | Đúng        |
| 5    | Virtual SOC hoạt động như một trung tâm dữ liệu giám sát 24/7.                | Thực đơn bữa trưa hôm nay của văn phòng có món bún chả và nem rán.                           | Low         | 0.2160       | Đúng        |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn nghĩa?**

> **Kết quả gây ngã ngửa nhất: Cặp số (2) với số điểm cao chạm trần 0.70!** Mặc dù con OpenAI xịn đi chăng nữa, nó vẫn bị sập bẫy bài toán đảo ngược ý nghĩa. Cặp 2 xài cùng 100% lượng từ khóa (_Chuyên gia SOC, mã độc tống tiền, hệ thống_), chỉ khác mỗi từ _Cảnh báo Lây lan_ vs _Xác nhận An toàn_.
>
> **Bài học rút ra:** Mô hình Vectors (Embeddings) thực tế hoạt động bằng cách đo lường tính "xuất hiện đồng thời của từ vựng trong chung một bối cảnh" (Bag of Words / Context overlap) chứ phần lớn vẫn mù lờ trước yếu tố ngữ pháp như Thể Phủ Định / Đối Lập. Do đó, điểm yếu chí mạng của Vector Search RAG là rất dễ trỏ nhầm các tài liệu cùng nói chung đề tài nhưng bản chất thông tin lại xung đột nhau kịch liệt.

---

## 6. Results — Cá nhân (10 điểm)

Chạy 5 benchmark queries của nhóm trên implementation cá nhân của bạn trong package `src`. **5 queries phải trùng với các thành viên cùng nhóm.**

### Benchmark Queries & Gold Answers (nhóm thống nhất)

| #   | Query                                                            | Gold Answer                                                                                                               |
| --- | ---------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| 1   | Viettel Cloud WAF có những gói dịch vụ nào?                      | 3 gói: Standard, Advanced, Complete — khác nhau về WAF, Bot Manager, DDoS, Data Retention                                 |
| 2   | Giải pháp nào của Viettel giúp chống tấn công DDoS?              | Viettel Cloudrity (Anti-DDoS L4/L7) và Viettel Cloud WAF (DDoS Protection lên đến 15 Tbps)                                |
| 3   | Viettel Threat Intelligence thu thập dữ liệu từ những nguồn nào? | ISP toàn cầu, đối tác FIRST/APWG, Pentest, Threat Hunting, Managed Security Service, nghiên cứu nội bộ APT/zero-day       |
| 4   | SOC của Viettel tổ chức vận hành như thế nào?                    | 6 nhóm: Tier 1 (giám sát 24/7), Tier 2 (xử lý sự cố), Tier 3 (chuyên sâu), Content Analysis, Threat Analysis, SOC Manager |
| 5   | Viettel Endpoint Security hỗ trợ những hệ điều hành nào?         | Windows, Linux, macOS, Android, iOS; tương thích VMware, Hyper-V, XenServer, KVM                                          |

### Kết Quả Của Tôi

| #   | Query                                                            | Top-1 Retrieved Chunk (tóm tắt)                                        | Score  | Relevant? | Agent Answer (tóm tắt)                                           |
| --- | ---------------------------------------------------------------- | ---------------------------------------------------------------------- | ------ | --------- | ---------------------------------------------------------------- |
| 1   | Viettel Cloud WAF có những gói dịch vụ nào?                      | `[# Datasheet: VIETTEL CLOUD...]` Tổng quan giải pháp và tính năng...  | 0.3701 | Partial   | Agent cung cấp phần Tổng quan và các tính năng thay vì Gói cước  |
| 2   | Giải pháp nào của Viettel giúp chống tấn công DDoS?              | `[## GIỚI THIỆU DỊCH VỤ]` Viettel Cloudrity là giải pháp chống DDoS... | 0.4394 | Yes       | Agent trích xuất giải pháp Cloudrity chống tấn công L4 và L7     |
| 3   | Viettel Threat Intelligence thu thập dữ liệu từ những nguồn nào? | `[##### Nguồn dữ liệu...]` Các nguồn dữ liệu đa dạng của hệ thống...   | 0.5784 | Yes       | Agent tổng hợp các nguồn từ IPS, đối tác FIRST/APWG, Pentest     |
| 4   | SOC của Viettel tổ chức vận hành như thế nào?                    | `[## Tổ chức vận hành...]` Mô hình nhân sự S.O.C chia thành 6 nhóm...  | 0.2696 | Yes       | Agent tóm tắt quy trình Tier 1 (Giám sát 24/7), Tier 2, Tier 3   |
| 5   | Viettel Endpoint Security hỗ trợ những hệ điều hành nào?         | `[## TỔNG QUAN]` Giải pháp bảo vệ thiết bị (Windows, Linux, Mac)...    | 0.4386 | Yes       | Agent trả lời tương thích với các nền tảng Windows, Linux, macOS |

**Bao nhiêu queries trả về chunk relevant trong top-3?** **5** / 5

---

## 7. What I Learned (5 điểm — Demo)

**Điều hay nhất tôi học được từ thành viên khác trong nhóm:**

> Thành viên trong nhóm có ý tưởng vô cùng ấn tượng về việc tự động hóa quá trình gán Metadata. Thay vì gán tay cồng kềnh, bạn ấy đã dùng Regex và Hash Map để bóc tách trực tiếp Tên Sản Phẩm và Cấu Hình Dịch Vụ ngay từ tên file Document, giúp cho Vector Store filter mượt mà và tiết kiệm cực nhiều tài nguyên tính toán.

**Điều hay nhất tôi học được từ nhóm khác (qua demo):**

> Việc thiết kế **Parent Document Retriever**. Các bạn ấy không chỉ băm văn bản thành các Chunk nhỏ để tìm cho nhạy, mà sau khi tìm thấy, hệ thống còn tự động truy xuất ngược ra cái "Chunk Cha" ôm trọn văn bản lớn hơn để nạp vào LLM. Nhờ đó mà Agent không bao giờ bị tình trạng "mất não" do thiếu hụt ngữ cảnh trước sau.

**Nếu làm lại, tôi sẽ thay đổi gì trong data strategy?**

> Tôi sẽ không dựa dẫm hoàn toàn vào Cosine Similarity nữa. Thay vào đó, tôi sẽ triển khai mô hình **Hybrid Search**: Kết hợp Vector Search (OpenAI Embeddings) để bắt ngữ nghĩa + Keyword Search (BM25) để bắt chính xác tuyệt đối các từ viết tắt chuyên ngành bảo mật như _DDoS L4/L7, OWASP Top 10, WAF_.

---

## Tự Đánh Giá

| Tiêu chí                    | Loại    | Điểm tự đánh giá |
| --------------------------- | ------- | ---------------- |
| Warm-up                     | Cá nhân | 5 / 5            |
| Document selection          | Nhóm    | 10 / 10          |
| Chunking strategy           | Nhóm    | 15 / 15          |
| My approach                 | Cá nhân | 10 / 10          |
| Similarity predictions      | Cá nhân | 5 / 5            |
| Results                     | Cá nhân | 10 / 10          |
| Core implementation (tests) | Cá nhân | 30 / 30          |
| Demo                        | Nhóm    | 0 / 5            |
| Điểm Bonus (Custom Tooling) | Cá nhân | 0                |
| **Tổng**                    |         | **100 / 100**    |

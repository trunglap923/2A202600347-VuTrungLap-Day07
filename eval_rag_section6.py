import os
import json
import uuid
from dotenv import load_dotenv

# Tận dụng các hàm từ thư mục src/
from src.embeddings import OpenAIEmbedder
from src.store import EmbeddingStore
from src.chunking import MarkdownChunker
from src.models import Document
from src.agent import KnowledgeBaseAgent

def mock_llm_fn(prompt: str) -> str:
    """Fake LLM giúp bóc nội dung nhanh chóng từ prompt ghép bởi Agent."""
    context_str = prompt.split("Context:\n")[1].split("\n\nQuestion:")[0]
    return f"Dựa trên dữ liệu tìm được, có vẻ như hệ thống đang nhắc đến: {context_str.replace(chr(10), ' ')}..."

def main():
    load_dotenv()
    
    print("1. Khởi tạo Embedder và EmbeddingStore từ src...")
    embedder = OpenAIEmbedder()
    store = EmbeddingStore(embedding_fn=embedder)
    
    print("2. Sử dụng MarkdownChunker từ src/chunking...")
    chunker = MarkdownChunker(chunk_size=800)

    print("3. Cắt Chunk, Cập Nhật Metadata và lưu vào Store...")
    # Bảng mapping metadata dựa trên tên file
    metadata_map = {
        "Cloud WAF": {"product": "Cloud WAF", "category": "web_security", "service_type": "WAF", "provider": "Viettel IDC"},
        "Cloudrity": {"product": "Cloudrity", "category": "web_security", "service_type": "Anti-DDoS & WAF", "provider": "Viettel IDC"},
        "Threat Intelligence": {"product": "Threat Intelligence", "category": "threat_intelligence", "service_type": "Threat Feed", "provider": "Viettel IDC"},
        "Virtual SOC": {"product": "Virtual SOC", "category": "soc_monitoring", "service_type": "Managed SOC", "provider": "Viettel IDC"},
        "CSMP": {"product": "CSMP", "category": "consulting", "service_type": "Maturity Program", "provider": "Viettel IDC"},
        "Endpoint Security": {"product": "Endpoint Security", "category": "endpoint_protection", "service_type": "EDR/EPP", "provider": "Viettel IDC"}
    }

    data_dir = "data"
    docs = []
    for fname in os.listdir(data_dir):
        if fname.endswith(".md"):
            filepath = os.path.join(data_dir, fname)
            with open(filepath, "r", encoding="utf-8") as f:
                text = f.read()
            
            # Khớp tìm metadata thích hợp
            doc_metadata = {"source": fname}
            for keyword, meta in metadata_map.items():
                if keyword in fname:
                    doc_metadata.update(meta)
                    break
            
            # Cắt chunk
            chunks = chunker.chunk(text)
            
            # Tạo các object Document theo chuẩn src.models
            for c in chunks:
                docs.append(Document(id=str(uuid.uuid4()), content=c, metadata=doc_metadata))
                
    store.add_documents(docs)
    print(f"Đã lưu thành công {len(docs)} chunks vào Vector Store!")

    print("4. Khởi tạo Agent và Xử lý 5 Benchmark Queries...")
    agent = KnowledgeBaseAgent(store=store, llm_fn=mock_llm_fn)
    
    queries = [
        "Viettel Cloud WAF có những gói dịch vụ nào?",
        "Giải pháp nào của Viettel giúp chống tấn công DDoS?",
        "Viettel Threat Intelligence thu thập dữ liệu từ những nguồn nào?",
        "SOC của Viettel tổ chức vận hành như thế nào?",
        "Viettel Endpoint Security hỗ trợ những hệ điều hành nào?"
    ]

    results_data = []
    
    for i, q in enumerate(queries, 1):
        # Retrieve trực tiếp để trích xuất số liệu Score cho Report
        search_res = store.search(q, top_k=3)
        if search_res:
            top1 = search_res[0]
            # Giả định câu trả lời agent
            agent_answer = agent.answer(q, top_k=3)
            
            chunk_summary = top1["content"].replace("\n", " ")
            
            results_data.append({
                "query": q,
                "top1_chunk": chunk_summary,
                "score": round(top1["score"], 4),
                "is_relevant": "TBD",
                "Agent_Answer": agent_answer
            })
            
    print("\n[KẾT QUẢ RAG PIPELINE]")
    print(json.dumps(results_data, indent=2, ensure_ascii=False))
    
    with open("step_6_results.json", "w", encoding="utf-8") as f:
        json.dump(results_data, f, indent=2, ensure_ascii=False)
        

if __name__ == "__main__":
    main()

# Cấu hình cho Agent RAG

# Mô hình ngôn ngữ lớn (LLM) cho phân loại và sinh câu trả lời
LLM_MODEL_NAME = "gemini-2.5-flash"

# Mô hình Embeddings cho RAG
EMBEDDINGS_MODEL_NAME = "bge-m3"

# Đường dẫn tới cơ sở dữ liệu vector ChromaDB (tương đối từ thư mục gốc của dự án)
VECTORSTORE_PATH = "storage/chroma_db"

# Đường dẫn tới file dữ liệu mẫu (tương đối từ thư mục gốc của dự án)
SAMPLE_DATA_PATH = "data/sample_data.txt"

# Đường dẫn tới file SQLite để lưu trạng thái hội thoại (tương đối từ thư mục gốc của dự án)
SQLITE_CHECKPOINT_PATH = "storage/memory.sqlite"
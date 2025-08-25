# Agentic RAG CLI

## Giới Thiệu
Dự án này là một agent AI tương tác qua dòng lệnh, được xây dựng bằng LangGraph. Nó được thiết kế để trả lời các câu hỏi của người dùng bằng cách phân loại câu hỏi, truy xuất thông tin từ cơ sở tri thức (RAG) khi cần, và duy trì ngữ cảnh hội thoại.

## Tính Năng
Liệt kê các tính năng chính của ứng dụng.

*   Phân loại câu hỏi (cần RAG hay không).
*   Truy xuất thông tin từ ChromaDB.
*   Sinh câu trả lời bằng mô hình Gemini 2.5 Flash.
*   Duy trì lịch sử hội thoại bằng SQLite.
*   Giao diện dòng lệnh tương tác.
*   **Xử lý ý định mua hàng và truy vấn sản phẩm từ Saleor API.**

## Bắt Đầu
Hướng dẫn cách thiết lập và chạy dự án.

### Yêu Cầu Tiên Quyết
Đảm bảo bạn đã cài đặt các phần mềm sau:

*   Python 3.9+
*   pip (Trình quản lý gói của Python)
*   Ollama (Để chạy mô hình embeddings `bge-m3`)
    *   Tải và cài đặt Ollama từ [ollama.com](https://ollama.com).
    *   Sau khi cài đặt, tải mô hình `bge-m3` bằng lệnh: `ollama pull bge-m3`
*   Google API Key (Để sử dụng mô hình Gemini 2.5 Flash)
    *   Tạo file `.env` ở thư mục gốc của dự án.
    *   Thêm dòng sau vào file `.env` (thay `YOUR_GOOGLE_API_KEY_HERE` bằng API key của bạn):
        ```
        GOOGLE_API_KEY="YOUR_GOOGLE_API_KEY_HERE"
        ```
*   **Saleor Instance (Để truy vấn sản phẩm)**
    *   Đảm bảo bạn có một Saleor instance đang chạy (ví dụ: `http://localhost:8000`).
    *   Thêm các biến sau vào file `.env`:
        ```
        SALEOR_API_URL="http://localhost:8000/graphql/"
        SALEOR_API_EMAIL="your_saleor_email@example.com"
        SALEOR_API_PASSWORD="your_saleor_password"
        ```

### Cài Đặt
1.  Clone repository:
    ```bash
    git clone <URL_CỦA_DỰ_ÁN>
    cd <TÊN_THƯ_MỤC_DỰ_ÁN_CỦA_BẠN>
    ```
2.  Tạo và kích hoạt môi trường ảo (khuyến nghị):
    ```bash
    python -m venv .venv
    # Trên Windows
    .venv\Scripts\activate
    # Trên macOS/Linux
    source .venv/bin/activate
    ```
3.  Cài đặt các thư viện cần thiết:
    ```bash
    pip install -r requirements.txt
    ```

### Chạy Ứng Dụng
Từ thư mục gốc của dự án, chạy lệnh sau:
```bash
python src/main.py
```
Ứng dụng sẽ khởi động và bạn có thể bắt đầu tương tác qua dòng lệnh.

## Cách Sử Dụng
Giải thích cách người dùng tương tác với ứng dụng.

*   Khi ứng dụng chạy, bạn sẽ thấy lời nhắc `User:`. Nhập câu hỏi của bạn và nhấn Enter.
*   Agent sẽ xử lý câu hỏi và in ra câu trả lời.
*   Để thoát khỏi cuộc trò chuyện, gõ `quit` hoặc `exit`.
*   Lịch sử trò chuyện được lưu trữ trong `storage/memory.sqlite` và sẽ được tải lại khi bạn khởi động lại ứng dụng (với cùng `thread_id` - xem `docs/todo.md` để biết cách cải thiện).
*   **Để hỏi về sản phẩm:** Bạn có thể nhập các câu hỏi như "tôi muốn mua áo thun màu xanh", "bạn có bán The Dash Cushion không?" hoặc "giá của Apple Juice là bao nhiêu?". Agent sẽ tìm kiếm và hiển thị thông tin sản phẩm.

## Cấu Trúc Thư Mục Chính
Dưới đây là cái nhìn tổng quan về cấu trúc thư mục chính của dự án:

```
agentic-rag-3/
├── .env                  # Biến môi trường (API keys, cấu hình Saleor)
├── requirements.txt      # Danh sách các thư viện Python cần thiết
├── docs/                 # Chứa tất cả các tài liệu dự án
├── src/                  # Mã nguồn chính của ứng dụng
│   ├── main.py           # Điểm khởi chạy chính của ứng dụng
│   ├── config.py         # Các hằng số cấu hình toàn dự án
│   ├── core/             # Logic cốt lõi của agent (AgentState)
│   ├── setup/            # Cấu hình LLM, Embeddings, Vector Store
│   ├── graph/            # Các node và định nghĩa LangGraph
│   └── services/         # Các dịch vụ bên ngoài (ví dụ: Saleor API)
├── data/                 # Dữ liệu thô cho RAG (ví dụ: sample_data.txt)
└── storage/              # Dữ liệu bền vững (ChromaDB, SQLite)
```

## Tài liệu chi tiết về cấu trúc dự án
Để biết chi tiết về cấu trúc thư mục và quy ước phát triển, vui lòng tham khảo [docs/GEMINI.md](docs/GEMINI.md).

## Tổng Quan Tài Liệu
Phần này cung cấp tổng quan về các tài liệu chính trong thư mục `/docs`.

*   **`design_document.md`**: Giải thích kiến trúc cấp cao của RAG agent, trình bày chi tiết các thành phần như LangGraph, ChromaDB, và các mô hình Gemini. Tài liệu này phác thảo trạng thái của agent và luồng logic từ phân loại câu hỏi đến sinh câu trả lời.
*   **`GEMINI.md`**: Cung cấp ngữ cảnh cho Gemini CLI, mô tả dự án dưới dạng một agent dựa trên LangGraph, hướng dẫn build/run, các quy ước phát triển, cấu trúc dự án, và các mô hình ngôn ngữ được sử dụng.
*   **`lessons_learned.md`**: Nhìn lại quá trình phát triển của dự án, bao gồm các thách thức và giải pháp liên quan đến đa luồng với SQLite, lợi ích của LangGraph, và tầm quan trọng của một cấu trúc dự án rõ ràng.
*   **`plan_v1.md`**: Kế hoạch phát triển ban đầu, phác thảo các mục tiêu của dự án, các thành phần chính cần xây dựng, và cấu trúc dự án ban đầu.
*   **`todo.md`**: Danh sách các công việc và cải tiến trong tương lai, bao gồm việc tăng cường khả năng duy trì lịch sử trò chuyện và đánh giá lại giải pháp đa luồng cho SQLite.

## Công Nghệ Sử Dụng
*   **Framework:** LangGraph
*   **Ngôn ngữ:** Python
*   **LLM:** Gemini 2.5 Flash
*   **Embeddings:** bge-m3 (qua Ollama)
*   **Vector Database:** ChromaDB
*   **Persistence:** SQLite (qua LangGraph's SqliteSaver)
*   **Quản lý môi trường:** `venv`
*   **Quản lý biến môi trường:** `python-dotenv`

## Đóng Góp
Nếu bạn muốn đóng góp cho dự án, vui lòng làm theo các bước sau:

1.  Fork repository.
2.  Tạo một branch mới (`git checkout -b feature/your-feature-name`).
3.  Thực hiện các thay đổi của bạn.
4.  Viết các bài kiểm thử (nếu có thể).
5.  Commit các thay đổi (`git commit -m 'feat: Add new feature'`).
6.  Push lên branch của bạn (`git push origin feature/your-feature-name`).
7.  Mở một Pull Request.

## Giấy Phép
Dự án này được cấp phép theo Giấy phép MIT. Xem file `LICENSE` để biết thêm chi tiết. (Nếu bạn có file LICENSE)

## Liên Hệ
Nếu có bất kỳ câu hỏi hoặc vấn đề nào, vui lòng liên hệ **Kiên Tạ** qua email **kientathuc@gmail.com**.

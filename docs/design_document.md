# Thiết kế Luồng Agent LangGraph (Cập nhật)

Tài liệu này mô tả thiết kế luồng (flow) cho một agent sử dụng LangGraph, đã được cập nhật để phản ánh chính xác code hiện tại.

## 1. Luồng Công việc Tổng thể

Luồng công việc của agent được thiết kế để xử lý câu hỏi của người dùng bằng cách phân loại chúng vào một trong ba luồng xử lý chính: **Purchase** (ý định mua hàng), **Retrieve** (truy xuất thông tin từ RAG), và **Generate** (trả lời bằng kiến thức chung).

```
0. START
   |
   V
1. Nhận câu hỏi của user (`receive_question`)
   |
   V
2. Phân loại câu hỏi (`classify_question`)
   |
   +------------------+------------------+
   | (purchase)       | (retrieve)       | (generate)
   V                  V                  V
3. Trích xuất        4. Lấy context     5. Sinh câu trả lời (`generate_answer`)
   thực thể sản phẩm    từ VectorDB         |
   (`extract_entities`) (`retrieve_context`)  |
   |                  |                  |
   V                  V                  |
6. Truy vấn Saleor   5. Sinh câu trả lời -> |
   API (`query_saleor`) (`generate_answer`)   |
   |                  |                  |
   |                  |                  |
   +------------------+------------------+
   |
   V
7. Hỏi user có muốn hỏi tiếp (`ask_to_continue`)
   |
   +------------------+
   |                  |
   V                  V
(Vòng lặp mới)       8. END
```

## 2. Mô tả các Node

Mỗi node đại diện cho một bước xử lý cụ thể trong luồng:

*   **`receive_question`**: Tiếp nhận câu hỏi mới từ người dùng và cập nhật `question` trong `AgentState`.
*   **`classify_question`**: Phân tích câu hỏi để quyết định luồng xử lý tiếp theo.
    *   **Hành động:** Sử dụng LLM để phân loại câu hỏi thành một trong ba loại: `purchase`, `retrieve`, hoặc `generate`.
    *   **Kết quả:** Cập nhật `classification_decision` trong `AgentState` và điều hướng luồng.
*   **`extract_entities` (Luồng Purchase)**: Trích xuất các thông tin chi tiết về sản phẩm (tên, màu, size,...) từ câu hỏi của người dùng.
    *   **Hành động:** Sử dụng LLM để phân tích `question` và trích xuất các thực thể.
    *   **Kết quả:** Cập nhật `extracted_entities` vào `AgentState`.
*   **`query_saleor` (Luồng Purchase)**: Sử dụng các thực thể đã trích xuất để truy vấn sản phẩm thông qua Saleor API.
    *   **Hành động:** Gửi request đến Saleor GraphQL API.
    *   **Kết quả:** Cập nhật `saleor_products` (hoặc `saleor_error`) vào `AgentState`.
*   **`retrieve_context` (Luồng Retrieve)**: Truy vấn cơ sở dữ liệu vector (ChromaDB) để lấy context liên quan đến câu hỏi.
    *   **Hành động:** Sử dụng `question` để thực hiện tìm kiếm tương đồng.
    *   **Kết quả:** Cập nhật `context` vào `AgentState`.
*   **`generate_answer` (Luồng Retrieve & Generate)**: Tạo ra câu trả lời cuối cùng cho người dùng.
    *   **Hành động:** Sử dụng LLM để tổng hợp câu trả lời dựa trên `question`, `context` (nếu có từ luồng retrieve) và `chat_history`.
    *   **Kết quả:** Cập nhật `answer` vào `AgentState`.
*   **`ask_to_continue`**: Điểm kết thúc của một lượt xử lý, chờ đợi input tiếp theo từ người dùng. Trong code hiện tại, node này chỉ mang tính hình thức và vòng lặp được quản lý bên ngoài graph.

## 3. Mô tả các Edges

Các edges định nghĩa luồng chuyển đổi giữa các node:

*   **`receive_question` -> `classify_question`**: Luôn luôn chuyển tiếp để phân loại câu hỏi.
*   **`classify_question` (Conditional Edge)**:
    *   Nếu `classification_decision` là `purchase`: Chuyển đến `extract_entities`.
    *   Nếu `classification_decision` là `retrieve`: Chuyển đến `retrieve_context`.
    *   Nếu `classification_decision` là `generate`: Chuyển đến `generate_answer`.
*   **`extract_entities` -> `query_saleor`**: Sau khi trích xuất thực thể, luôn truy vấn Saleor.
*   **`retrieve_context` -> `generate_answer`**: Sau khi lấy context, luôn sinh câu trả lời.
*   **`generate_answer` -> `ask_to_continue`**: Sau khi sinh câu trả lời, kết thúc lượt.
*   **`query_saleor` -> `ask_to_continue`**: Sau khi truy vấn Saleor, kết thúc lượt.
*   **`ask_to_continue` -> `END`**: Kết thúc một chu trình thực thi của graph.

## 4. Cấu trúc Trạng thái (AgentState)

Trạng thái của agent đã được mở rộng để hỗ trợ các luồng mới.

```python
from typing import List, TypedDict, Optional, Dict, Any

class Message(TypedDict):
    role: str  # 'user' or 'assistant'
    content: str

class AgentState(TypedDict):
    """
    Đại diện cho trạng thái của agent trong suốt cuộc hội thoại.
    """
    question: str
    context: Optional[str]
    answer: Optional[str]
    chat_history: List[Message]
    classification_decision: Optional[str] # Quyết định: 'purchase', 'retrieve', 'generate'
    
    # Các trường được thêm vào trong quá trình chạy
    extracted_entities: Optional[Dict[str, Any]] # Kết quả từ node extract_entities
    saleor_products: Optional[List[Dict[str, Any]]] # Kết quả sản phẩm từ Saleor
    saleor_error: Optional[str] # Lỗi nếu có từ Saleor
```

## 5. Lưu trữ Trạng thái (Persistence)

*   **Cơ sở dữ liệu:** SQLite vẫn được sử dụng để lưu trữ trạng thái của agent.
*   **Cơ chế:** LangGraph `SqliteSaver` được sử dụng để tự động lưu và khôi phục trạng thái cho mỗi phiên hội thoại (`thread_id`).

Việc cập nhật này đảm bảo tài liệu thiết kế phản ánh đúng kiến trúc và luồng hoạt động của ứng dụng hiện tại.

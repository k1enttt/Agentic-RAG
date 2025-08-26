# Thiết kế Luồng Agent LangGraph (Cập nhật cho Phiên bản 2)

Tài liệu này mô tả thiết kế luồng (flow) cho một agent sử dụng LangGraph, đã được cập nhật để phản ánh chính xác code hiện tại và tích hợp persona của một người tư vấn thời trang, tập trung vào các luồng chính cho Phiên bản 2.

## 1. Luồng Công việc Tổng thể

Luồng công việc của agent được thiết kế để xử lý câu hỏi của người dùng bằng cách phân loại chúng vào một trong ba luồng xử lý chính cho Phiên bản 2: **Purchase** (ý định mua hàng), **General Fashion Inquiry** (hỏi đáp thời trang chung), và **Off-topic** (câu hỏi không liên quan đến thời trang/mua sắm).

```
0. START
   |
   V
1. Nhận câu hỏi của user (`receive_question`)
   |
   V
2. Phân loại câu hỏi (`classify_question`)
   |
   +------------------+--------------------------+------------------+
   | (purchase)       | (general_fashion_inquiry)| (off_topic)
   V                  V                          V
3. Trích xuất        4. Xử lý hỏi đáp           5. Xử lý lạc đề
   thực thể sản phẩm    thời trang chung           (`handle_off_topic`)
   (`extract_entities`) (`handle_general_inquiry`)  |
   |
   V                  V                          |
6. Truy vấn Saleor   5. Sinh câu trả lời        |
   API (`query_saleor`) (`generate_answer`)         |
   |
   |                  |                          |
   +------------------+--------------------------+------------------+
   | (Vòng lặp mới)
   V
7. Hỏi user có muốn hỏi tiếp (`ask_to_continue`)
   |
   +------------------+
   |                  |
   V                  V
8. END
```

## 2. Mô tả các Node

Mỗi node đại diện cho một bước xử lý cụ thể trong luồng:

*   **`receive_question`**: Tiếp nhận câu hỏi mới từ người dùng và cập nhật `question` trong `AgentState`.
*   **`classify_question`**: Phân tích câu hỏi để quyết định luồng xử lý tiếp theo.
    *   **Hành động:** Sử dụng LLM để phân loại câu hỏi thành một trong ba loại: `purchase`, `general_fashion_inquiry`, hoặc `off_topic`.
    *   **Kết quả:** Cập nhật `classification_decision` trong `AgentState` và điều hướng luồng.
*   **`extract_entities` (Luồng Purchase)**: Trích xuất các thông tin chi tiết về sản phẩm (tên, màu, size,...) từ câu hỏi của người dùng.
    *   **Hành động:** Sử dụng LLM để phân tích `question` và trích xuất các thực thể.
    *   **Kết quả:** Cập nhật `extracted_entities` vào `AgentState`.
*   **`query_saleor` (Luồng Purchase)**: Sử dụng các thực thể đã trích xuất để truy vấn sản phẩm thông qua Saleor API.
    *   **Hành động:** Gửi request đến Saleor GraphQL API.
    *   **Kết quả:** Cập nhật `saleor_products` (hoặc `saleor_error`) vào `AgentState`.
*   **`handle_general_inquiry` (Luồng General Fashion Inquiry)**: Xử lý các câu hỏi liên quan đến thời trang nhưng không phải mua bán trực tiếp.
    *   **Hành động:** Quyết định xem có cần truy vấn VectorDB để lấy ngữ cảnh (ví dụ: chính sách, thông tin sản phẩm chung) hay chỉ cần LLM tự sinh câu trả lời dựa trên kiến thức chung. Sau đó, chuẩn bị ngữ cảnh hoặc câu hỏi cho `generate_answer`.
    *   **Kết quả:** Cập nhật `context` (nếu có) và/hoặc `answer` tạm thời vào `AgentState`.
*   **`generate_answer` (Luồng General Fashion Inquiry)**: Tạo ra câu trả lời cuối cùng cho người dùng.
    *   **Hành động:** Sử dụng LLM để tổng hợp câu trả lời dựa trên `question`, `context` (nếu có từ luồng `handle_general_inquiry`) và `chat_history`.
    *   **Kết quả:** Cập nhật `answer` vào `AgentState`.
*   **`handle_off_topic` (Luồng Off-topic)**: Xử lý các câu hỏi không liên quan đến thời trang hoặc mua sắm.
    *   **Hành động:** Tạo ra một câu trả lời nhẹ nhàng nhắc nhở người dùng về mục đích của cuộc trò chuyện và khuyến khích họ hỏi về quần áo hoặc mua sắm.
    *   **Kết quả:** Cập nhật `answer` vào `AgentState` với thông điệp động viên.
*   **`ask_to_continue`**: Điểm kết thúc của một lượt xử lý, chờ đợi input tiếp theo từ người dùng. Trong code hiện tại, node này chỉ mang tính hình thức và vòng lặp được quản lý bên ngoài graph.

## 3. Mô tả các Edges

Các edges định nghĩa luồng chuyển đổi giữa các node:

*   **`receive_question` -> `classify_question`**: Luôn luôn chuyển tiếp để phân loại câu hỏi.
*   **`classify_question` (Conditional Edge)**:
    *   Nếu `classification_decision` là `purchase`: Chuyển đến `extract_entities`.
    *   Nếu `classification_decision` là `general_fashion_inquiry`: Chuyển đến `handle_general_inquiry`.
    *   Nếu `classification_decision` là `off_topic`: Chuyển đến `handle_off_topic`.
*   **`extract_entities` -> `query_saleor`**: Sau khi trích xuất thực thể, luôn truy vấn Saleor.
*   **`query_saleor` -> `ask_to_continue`**: Sau khi truy vấn Saleor, kết thúc lượt.
*   **`handle_general_inquiry` -> `generate_answer`**: Sau khi xử lý hỏi đáp chung, luôn sinh câu trả lời.
*   **`generate_answer` -> `ask_to_continue`**: Sau khi sinh câu trả lời, kết thúc lượt.
*   **`handle_off_topic` -> `ask_to_continue`**: Sau khi xử lý lạc đề, kết thúc lượt.
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
    classification_decision: Optional[str] # Quyết định: 'purchase', 'general_fashion_inquiry', 'off_topic'
    
    # Các trường được thêm vào trong quá trình chạy
    extracted_entities: Optional[Dict[str, Any]] # Kết quả từ node extract_entities
    saleor_products: Optional[List[Dict[str, Any]]] # Kết quả sản phẩm từ Saleor
    saleor_error: Optional[str] # Lỗi nếu có từ Saleor
```

## 5. Lưu trữ Trạng thái (Persistence)

*   **Cơ sở dữ liệu:** SQLite vẫn được sử dụng để lưu trữ trạng thái của agent.
*   **Cơ chế:** LangGraph `SqliteSaver` được sử dụng để tự động lưu và khôi phục trạng thái cho mỗi phiên hội thoại (`thread_id`).

Việc cập nhật này đảm bảo tài liệu thiết kế phản ánh đúng kiến trúc và luồng hoạt động của ứng dụng hiện tại cho Phiên bản 2.

```

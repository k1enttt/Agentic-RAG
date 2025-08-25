# Thiết kế Luồng Agent LangGraph

Tài liệu này mô tả thiết kế luồng (flow) cho một agent sử dụng LangGraph, bao gồm các node, edges, cấu trúc trạng thái và kế hoạch triển khai.

## 1. Luồng Công việc Tổng thể

Luồng công việc của agent được thiết kế để xử lý câu hỏi của người dùng, truy xuất thông tin khi cần, trả lời và quản lý phiên hội thoại.

```
0. START
   |
   V
1. Nhận câu hỏi của user
   |
   V
2. Phân loại câu hỏi (purchase? retrieve? hay generate?)
   |
   +-----------------------------------------------------------------+
   |                                 |                               |
   V                                 V                               V
3. Trích xuất thực thể sản phẩm      4. Chạy retrieve để lấy context   5. Tiến hành trả lời (kiến thức chung)
   |                                 |                               ^
   +---------------------------------+                               |
   |                                                                 |
   V                                                                 |
6. Truy vấn Saleor API để tìm sản phẩm                               |
   |                                                                 |
   +-----------------------------------------------------------------+
   |
   V
7. Hỏi user có muốn hỏi tiếp hay không?
   |
   +---------------------------------+
   |                                 |
   V                                 V
1. Nhận câu hỏi của user             8. END
```

## 2. Mô tả các Node

Mỗi node đại diện cho một bước xử lý cụ thể trong luồng:

*   **Node 0: START**
    *   Điểm bắt đầu của mọi phiên làm việc.
*   **Node 1: Nhận câu hỏi của user**
    *   **Mục đích:** Tiếp nhận câu hỏi mới từ người dùng.
    *   **Hành động:** Cập nhật `question` trong `AgentState`.
*   **Node 2: Phân loại câu hỏi**
    *   **Mục đích:** Xác định xem câu hỏi có thể được trả lời ngay lập tức (dựa trên kiến thức nội tại hoặc lịch sử hội thoại) hay cần phải truy xuất dữ liệu bên ngoài.
    *   **Hành động:** Phân tích `question` và `chat_history`.
    *   **Kết quả:** Quyết định chuyển đến Node 3 (Retrieve) hoặc Node 4 (Trả lời trực tiếp).
    *   *(Chi tiết cơ chế phân loại sẽ được mô tả sau.)*
*   **Node 3: Chạy retrieve để lấy context**
    *   **Mục đích:** Thực hiện truy vấn đến cơ sở dữ liệu kiến thức (vector DB, v.v.) để lấy các đoạn văn bản (context) liên quan đến câu hỏi.
    *   **Hành động:** Sử dụng `question` để truy vấn. Cập nhật `context` vào `AgentState`.
    *   **Kết quả:**
        *   Thành công: Chuyển đến Node 4.
        *   Thất bại/Không tìm thấy context phù hợp: Chuyển đến Node 5 (để thông báo không thể trả lời và hỏi tiếp).
*   **Node 4: Tiến hành trả lời**
    *   **Mục đích:** Tạo ra câu trả lời cuối cùng cho người dùng.
    *   **Hành động:** Sử dụng LLM để tổng hợp câu trả lời dựa trên `question`, `context` (nếu có) và `chat_history`. Cập nhật `answer` vào `AgentState`.
*   **Node 5: Hỏi user có muốn hỏi tiếp hay không?**
    *   **Mục đích:** Tương tác với người dùng để xác định xem họ muốn tiếp tục cuộc hội thoại hay kết thúc. Node này cũng là điểm hội tụ cho trường hợp agent không thể trả lời câu hỏi.
    *   **Hành động:** Gửi câu hỏi cho người dùng (ví dụ: "Bạn có muốn hỏi gì thêm không?"). Sử dụng LLM để phân tích phản hồi của người dùng.
    *   **Kết quả:**
        *   Muốn hỏi tiếp: Chuyển về Node 1.
        *   Muốn chấm dứt: Chuyển đến Node 6.
*   **Node 6: END**
    *   Điểm kết thúc của phiên làm việc.

## 3. Mô tả các Edges

Các edges định nghĩa luồng chuyển đổi giữa các node:

*   **START -> Node 1:** Luôn luôn chuyển từ START đến Node 1 để nhận câu hỏi đầu tiên.
*   **Node 1 -> Node 2:** Luôn luôn chuyển từ Node 1 đến Node 2 để phân loại câu hỏi.
*   **Node 2 (Conditional Edge):**
    *   Nếu cần retrieve data: Chuyển đến Node 3.
    *   Nếu có thể trả lời luôn: Chuyển đến Node 4.
*   **Node 3 (Conditional Edge):**
    *   Nếu retrieve thành công và có context: Chuyển đến Node 4.
    *   Nếu retrieve thất bại hoặc không có context phù hợp: Chuyển đến Node 5.
*   **Node 4 -> Node 5:** Luôn luôn chuyển từ Node 4 đến Node 5 sau khi đã trả lời.
*   **Node 5 (Conditional Edge):**
    *   Nếu người dùng muốn hỏi tiếp: Chuyển về Node 1 (tạo một chu trình).
    *   Nếu người dùng muốn chấm dứt hội thoại: Chuyển đến Node 6.

## 4. Cấu trúc Trạng thái (AgentState)

Trạng thái của agent sẽ được lưu trữ trong một `TypedDict` và được truyền giữa các node. Trạng thái này cũng sẽ được lưu trữ vào cơ sở dữ liệu SQLite để duy trì phiên làm việc.

```python
from typing import List, TypedDict, Optional

class Message(TypedDict):
    role: str # 'user' hoặc 'assistant'
    content: str

class AgentState(TypedDict):
    """
    Đại diện cho trạng thái của agent trong suốt cuộc hội thoại.
    """
    question: str # Câu hỏi hiện tại của người dùng
    context: Optional[str] # Context đã retrieve được (nếu có)
    answer: Optional[str] # Câu trả lời của agent
    chat_history: List[Message] # Lịch sử toàn bộ cuộc hội thoại (câu hỏi và trả lời)
    # Các trường bổ sung có thể được thêm vào sau này nếu cần
```

## 5. Lưu trữ Trạng thái (Persistence)

*   **Cơ sở dữ liệu:** SQLite sẽ được sử dụng để lưu trữ trạng thái của agent.
*   **Cơ chế:** LangGraph cung cấp `SqliteSaver` để dễ dàng tích hợp. Mỗi phiên hội thoại sẽ có một ID riêng biệt, và trạng thái của nó sẽ được lưu trữ và khôi phục từ file SQLite.

## 6. Các bước Triển khai Tiếp theo

Để bắt đầu xây dựng agent này, các bước sau đây được đề xuất:

1.  **Cài đặt môi trường:**
    *   Tạo thư mục dự án.
    *   Cài đặt các thư viện Python cần thiết: `langchain`, `langgraph`, `python-dotenv`.
2.  **Định nghĩa `AgentState`:**
    *   Tạo file `state.py` và định nghĩa `AgentState` như trên.
3.  **Khởi tạo LangGraph và `SqliteSaver`:**
    *   Trong file `main.py` (hoặc tương tự), khởi tạo `StateGraph` và `SqliteSaver`.
4.  **Triển khai các Node (hàm Python):**
    *   Viết các hàm Python tương ứng với mỗi node (Node 1, Node 2 (placeholder), Node 3, Node 4, Node 5).
5.  **Định nghĩa các Edges:**
    *   Sử dụng `add_node`, `set_entry_point`, `add_edge`, `add_conditional_edges` của LangGraph để xây dựng luồng.
6.  **Kiểm thử:**
    *   Chạy thử nghiệm từng phần và toàn bộ luồng để đảm bảo hoạt động đúng như thiết kế.
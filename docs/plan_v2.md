# Kế hoạch Phát triển Agent RAG - Phiên bản 2

Tài liệu này phác thảo kế hoạch phát triển cho Phiên bản 2 của Agent RAG, tập trung vào việc tích hợp persona người tư vấn thời trang và xử lý các loại câu hỏi chính.

## 1. Mục tiêu Phiên bản 2

*   **Tích hợp Persona:** Agent sẽ đóng vai một người phụ nữ làm việc trong cửa hàng thời trang, có khả năng trò chuyện và tư vấn về quần áo với giọng điệu thân thiện, chuyên nghiệp.
*   **Xử lý Câu hỏi Mua bán (`purchase`):** Nâng cao khả năng trích xuất thực thể và truy vấn sản phẩm thông qua Saleor API.
*   **Xử lý Hỏi đáp Thời trang Chung (`general_fashion_inquiry`):** Cung cấp thông tin và lời khuyên chung về thời trang, sử dụng cả kiến thức của LLM và ngữ cảnh từ VectorDB (nếu có).
*   **Xử lý Câu hỏi Lạc đề (`off_topic`):** Nhẹ nhàng động viên người dùng quay lại chủ đề mua bán quần áo khi họ hỏi những câu không liên quan.

## 2. Các Tính năng Chính

### 2.1. Phân loại Câu hỏi Nâng cao

*   **Mô tả:** Node `classify_question` sẽ được tinh chỉnh để phân loại câu hỏi của người dùng thành 3 loại chính:
    *   `purchase`: Người dùng có ý định mua hàng hoặc hỏi về sản phẩm cụ thể.
    *   `general_fashion_inquiry`: Người dùng hỏi về thông tin thời trang chung, lời khuyên, hoặc các vấn đề liên quan đến cửa hàng (ví dụ: chính sách).
    *   `off_topic`: Người dùng hỏi những câu không liên quan đến thời trang hay mua bán.
*   **Công nghệ:** Sử dụng LLM (Gemini 2.5 Flash) với prompt engineering để đạt được độ chính xác cao trong phân loại.

### 2.2. Luồng Mua bán (`purchase`)

*   **Mô tả:** Khi câu hỏi được phân loại là `purchase`, agent sẽ trích xuất các thực thể như tên sản phẩm, màu sắc, kích thước, số lượng. Sau đó, sử dụng các thực thể này để truy vấn Saleor API và cung cấp thông tin sản phẩm hoặc hỗ trợ quá trình mua hàng.
*   **Công nghệ:**
    *   Node `extract_entities`: Sử dụng LLM để trích xuất thông tin từ câu hỏi.
    *   Node `query_saleor`: Tương tác với Saleor GraphQL API để lấy dữ liệu sản phẩm.

### 2.3. Luồng Hỏi đáp Thời trang Chung (`general_fashion_inquiry`)

*   **Mô tả:** Khi câu hỏi được phân loại là `general_fashion_inquiry`, agent sẽ cố gắng cung cấp câu trả lời hữu ích. Điều này có thể bao gồm việc sử dụng kiến thức chung của LLM để đưa ra lời khuyên thời trang hoặc truy vấn VectorDB (ChromaDB) để lấy ngữ cảnh từ các tài liệu nội bộ (ví dụ: bài viết blog, FAQ về thời trang, thông tin chung về sản phẩm).
*   **Công nghệ:**
    *   Node `handle_general_inquiry`: Quyết định chiến lược trả lời (LLM-only hoặc RAG).
    *   Node `retrieve_context`: Sử dụng OllamaEmbeddings (bge-m3) và ChromaDB để tìm kiếm ngữ cảnh.
    *   Node `generate_answer`: Tổng hợp câu trả lời cuối cùng.

### 2.4. Luồng Xử lý Lạc đề (`off_topic`)

*   **Mô tả:** Khi câu hỏi được phân loại là `off_topic`, agent sẽ không phớt lờ mà sẽ tạo ra một câu trả lời nhẹ nhàng, lịch sự để động viên người dùng quay lại chủ đề mua bán quần áo hoặc tư vấn thời trang.
*   **Công nghệ:**
    *   Node `handle_off_topic`: Sử dụng LLM để tạo ra thông điệp động viên.

## 3. Cách tiếp cận Kỹ thuật

*   **Cập nhật `src/graph/nodes.py`:**
    *   Điều chỉnh hàm `classify_question` để hỗ trợ 3 loại phân loại mới.
    *   Thêm node mới `handle_general_inquiry` để xử lý luồng hỏi đáp thời trang chung.
    *   Thêm node mới `handle_off_topic` để xử lý câu hỏi lạc đề.
*   **Cập nhật `src/core/state.py`:**
    *   Điều chỉnh `AgentState` để phản ánh các trường dữ liệu cần thiết cho các luồng mới (ví dụ: `classification_decision` sẽ có các giá trị mới).
*   **Cập nhật `src/main.py`:**
    *   Điều chỉnh định nghĩa LangGraph để kết nối các node và edges theo luồng công việc mới.
    *   Cập nhật prompt cho LLM để phù hợp với persona và các loại phân loại mới.

## 4. Các Cải tiến trong Tương lai (Phiên bản 3 trở đi)

*   **Tư vấn Thời trang Chuyên sâu (`fashion_advice`):** Tách riêng luồng này khỏi `general_fashion_inquiry` để cung cấp lời khuyên cá nhân hóa hơn, có thể dựa trên hồ sơ người dùng hoặc sở thích đã biết.
*   **Tư vấn Đổi trả (`return_exchange_inquiry`):** Tách riêng luồng này để xử lý các câu hỏi về chính sách và quy trình đổi trả một cách chuyên biệt, có thể tích hợp với hệ thống quản lý đơn hàng.
*   **Tích hợp Hình ảnh:** Cho phép người dùng tải lên hình ảnh quần áo để agent tư vấn hoặc tìm kiếm sản phẩm tương tự.
*   **Hỗ trợ Đa ngôn ngữ:** Mở rộng khả năng của agent để hỗ trợ nhiều ngôn ngữ khác nhau.

Kế hoạch này sẽ là kim chỉ nam cho quá trình phát triển Phiên bản 2, đảm bảo chúng ta tập trung vào các tính năng cốt lõi và có lộ trình rõ ràng cho các cải tiến trong tương lai.

# Kế hoạch triển khai - Phiên bản 1

1.  **Tạo file `state.py`:**
    *   Định nghĩa `AgentState` `TypedDict` để lưu trữ trạng thái của agent (câu hỏi, context, lịch sử chat, v.v.).

2.  **Khởi tạo file `main.py`:**
    *   Import các thư viện cần thiết.
    *   Tạo cấu trúc cơ bản cho file.

3.  **Triển khai các Node trong `main.py`:**
    *   Viết hàm cho `node_receive_question` để nhận câu hỏi từ người dùng.
    *   Viết hàm cho `node_classify_question` để phân loại câu hỏi.
    *   Viết hàm cho `node_retrieve_context` để kết nối và truy vấn từ ChromaDB.
    *   Viết hàm cho `node_generate_answer` để gọi LLM và tạo câu trả lời.
    *   Viết hàm cho `node_ask_to_continue` để hỏi người dùng có muốn tiếp tục không.

4.  **Xây dựng Graph trong `main.py`:**
    *   Khởi tạo `StateGraph` với `AgentState`.
    *   Thêm các node đã tạo vào graph.
    *   Thiết lập điểm bắt đầu (entry point).
    *   Định nghĩa các cạnh (edges) và các cạnh điều kiện (conditional edges) để kết nối các node theo đúng luồng đã thiết kế.

5.  **Tích hợp Lưu trữ Trạng thái:**
    *   Cấu hình `SqliteSaver` để lưu và khôi phục lại các phiên hội thoại.

6.  **Tạo Vòng lặp Chính (Main Loop):**
    *   Viết vòng lặp chính trong `main.py` để nhận input từ dòng lệnh, thực thi graph, in ra câu trả lời và xử lý việc tiếp tục hay kết thúc phiên.

7.  **Chuẩn bị Dữ liệu và Kiểm thử:**
    *   Tạo một file văn bản đơn giản (`sample_data.txt`) để làm dữ liệu cho ChromaDB.
    *   Chạy và kiểm thử toàn bộ luồng để đảm bảo agent hoạt động đúng như mong đợi.

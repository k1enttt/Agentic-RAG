# Các công việc cần làm trong tương lai (TODO)

## 1. Cải thiện khả năng duy trì lịch sử trò chuyện
*   **Vấn đề:** Hiện tại, `thread_id` được tạo mới mỗi khi chương trình khởi động, dẫn đến việc không nhớ được lịch sử trò chuyện từ các phiên trước.
*   **Giải pháp:**
    *   Thay đổi logic trong `main.py` để sử dụng một `thread_id` cố định (ví dụ: "default_session") cho mục đích phát triển/kiểm thử.
    *   Hoặc, triển khai cơ chế cho phép người dùng nhập `thread_id` để tiếp tục một phiên trò chuyện cụ thể, hoặc chọn từ danh sách các phiên đã lưu.

## 2. Xem xét lại giải pháp đa luồng SQLite
*   **Vấn đề:** Đã sử dụng `check_same_thread=False` khi kết nối SQLite để giải quyết lỗi đa luồng. Mặc dù hoạt động, đây có thể không phải là giải pháp tối ưu nhất về mặt an toàn dữ liệu trong môi trường production.
*   **Giải pháp:** Khi chương trình ổn định, nghiên cứu các phương pháp quản lý kết nối SQLite an toàn hơn trong môi trường đa luồng (ví dụ: sử dụng `sqlite3.Connection` với `threading.local` hoặc các thư viện quản lý pool kết nối nếu cần).


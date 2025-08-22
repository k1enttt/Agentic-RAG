# Kinh nghiệm rút ra từ quá trình phát triển Agent RAG cơ bản

Trong quá trình phát triển agent RAG cơ bản, chúng ta đã gặp và khắc phục một số lỗi. Dưới đây là những bài học quan trọng được rút ra để tránh lặp lại trong các dự án tương lai:

1.  **Đọc kỹ tài liệu và chú ý phiên bản thư viện:**
    *   **Vấn đề:** Các lỗi liên quan đến cách khởi tạo `SqliteSaver` và `Chroma` cho thấy việc sử dụng API không đúng cách hoặc không cập nhật với phiên bản thư viện mới nhất.
    *   **Bài học:** Luôn tham khảo tài liệu chính thức của thư viện (LangChain, LangGraph, v.v.) cho phiên bản cụ thể đang sử dụng. Các thư viện này phát triển nhanh chóng, API có thể thay đổi.

2.  **Không bỏ qua cảnh báo (Deprecation Warnings):**
    *   **Vấn đề:** Cảnh báo `LangChainDeprecationWarning` cho `Chroma` là một ví dụ. Mặc dù không gây lỗi ngay lập tức, nhưng nó báo hiệu rằng cách sử dụng hiện tại sẽ bị loại bỏ trong tương lai.
    *   **Bài học:** Xử lý các cảnh báo ngay khi chúng xuất hiện. Chúng thường là dấu hiệu của các vấn đề tiềm ẩn sẽ trở thành lỗi trong các phiên bản sau.

3.  **Kiểm soát Encoding file rõ ràng:**
    *   **Vấn đề:** Lỗi `UnicodeDecodeError` khi đọc `sample_data.txt` xảy ra do không chỉ định rõ encoding là `UTF-8` khi đọc file, đặc biệt trên các hệ điều hành có encoding mặc định khác (như `cp1252` trên Windows).
    *   **Bài học:** Luôn chỉ định `encoding='utf-8'` một cách tường minh khi đọc hoặc ghi các file văn bản, đặc biệt là khi làm việc với các ngôn ngữ không phải tiếng Anh.

4.  **Cẩn thận với cú pháp f-string và dấu ngoặc:**
    *   **Vấn đề:** Lỗi `SyntaxError: f-string: unmatched '['` xuất hiện khi sử dụng dấu ngoặc kép `"` cả bên ngoài và bên trong f-string để truy cập key của dictionary.
    *   **Bài học:** Khi sử dụng f-string và cần nhúng các chuỗi có dấu ngoặc kép, hãy sử dụng dấu ngoặc đơn `'` cho các chuỗi bên trong (hoặc ngược lại) để tránh xung đột cú pháp.

5.  **Kiểm tra kiểu dữ liệu và tham số hàm:**
    *   **Vấn đề:** Các lỗi như `AttributeError: 'str' object has no attribute 'executescript'` và `TypeError: SqliteSaver.__init__() got an unexpected keyword argument 'conn_string'` cho thấy việc truyền sai kiểu dữ liệu (truyền chuỗi thay vì đối tượng kết nối) hoặc sai tên tham số cho hàm.
    *   **Bài học:** Đảm bảo rằng các đối số truyền vào hàm hoặc phương thức khớp chính xác với kiểu dữ liệu và tên tham số mà hàm/phương thức đó mong đợi. Nếu cần một đối tượng (ví dụ: `sqlite3.Connection`), hãy tạo đối tượng đó trước khi truyền vào.

6.  **Lưu ý về lỗi đa luồng SQLite (`sqlite3.ProgrammingError`):**
    *   **Vấn đề:** Lỗi `SQLite objects created in a thread can only be used in that same thread` xảy ra khi một kết nối SQLite được tạo trong một luồng nhưng lại được sử dụng bởi một luồng khác (điển hình trong môi trường đa luồng của LangGraph).
    *   **Giải pháp tạm thời:** Sử dụng `sqlite3.connect("memory.sqlite", check_same_thread=False)` để cho phép kết nối được sử dụng bởi nhiều luồng. 
    *   **Bài học quan trọng:** Mặc dù giải pháp này giúp chương trình chạy được, nhưng `check_same_thread=False` có thể tiềm ẩn rủi ro về an toàn dữ liệu trong các ứng dụng phức tạp hơn nếu không được quản lý cẩn thận. **Cần xem xét lại và tìm giải pháp quản lý kết nối SQLite an toàn hơn cho môi trường đa luồng khi chương trình đã chạy ổn định và chuẩn bị cho môi trường production.**

Những bài học này sẽ giúp quá trình phát triển diễn ra suôn sẻ hơn và giảm thiểu thời gian gỡ lỗi trong tương lai.
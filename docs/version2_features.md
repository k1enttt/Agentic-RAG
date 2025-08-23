# Tính năng cho Phiên bản 2 của Chương trình Agentic RAG

Phiên bản 2 của chương trình sẽ tập trung vào việc phát triển các tính năng cốt lõi để biến dự án thành một sản phẩm hoàn chỉnh, có khả năng mở rộng và thân thiện với người dùng.

## 1. Xử lý lỗi và Độ bền (Error Handling & Robustness) (Ưu tiên cao)

*   **Mục tiêu**: Đảm bảo chương trình hoạt động ổn định, đáng tin cậy và có khả năng phục hồi trong mọi tình huống, giảm thiểu gián đoạn cho người dùng.
*   **Các tính năng cụ thể**:
    *   **Cơ chế thử lại (Retry Mechanisms)**: Triển khai cơ chế tự động thử lại cho **tất cả các cuộc gọi API bên ngoài** (LLM, ChromaDB) sử dụng chiến lược **Exponential Backoff with Jitter** với tối đa **3 đến 5 lần thử lại**, tăng khả năng chịu lỗi của hệ thống.
    *   **Hệ thống ghi nhật ký (Logging) chi tiết**: Cải thiện hệ thống ghi nhật ký bằng cách sử dụng thư viện **Loguru** để triển khai **ghi nhật ký có cấu trúc (JSON format)** vào file, và sau đó tích hợp với một dịch vụ quản lý log tập trung (ví dụ: ELK Stack, Grafana Loki, Sentry) trong tương lai. Điều này giúp thu thập thông tin chi tiết về hoạt động của tác nhân, các lỗi xảy ra và các sự kiện quan trọng, giúp dễ dàng gỡ lỗi và giám sát hiệu suất.
    *   **Xử lý ngoại lệ duyên dáng**: Đảm bảo rằng ứng dụng có thể xử lý các ngoại lệ và lỗi một cách duyên dáng bằng cách kết hợp **`try-except` blocks một cách có chọn lọc**, **xử lý ngoại lệ toàn cục (Global Exception Handling)** ở cấp độ API backend, và **định nghĩa các ngoại lệ tùy chỉnh (Custom Exceptions)** cho các tình huống lỗi nghiệp vụ. Điều này giúp ngăn chặn sập chương trình, cung cấp thông báo lỗi rõ ràng cho người dùng hoặc ghi lại để phân tích.
    *   **Giám sát tài nguyên**: Triển khai các công cụ giám sát để theo dõi việc sử dụng tài nguyên (CPU, RAM, mạng) của ứng dụng, giúp phát hiện sớm các vấn đề về hiệu suất. Sử dụng **Prometheus và Grafana** để thu thập, trực quan hóa và cảnh báo về các số liệu từ ứng dụng FastAPI, PostgreSQL, Docker containers (thông qua cAdvisor) và máy chủ vật lý (thông qua node_exporter).

## 2. Hỗ trợ Đa người dùng và Kiến trúc Dịch vụ (Ưu tiên cao)

*   **Mục tiêu**: Chuyển đổi chương trình từ một công cụ CLI đơn người dùng thành một nền tảng có khả năng phục vụ nhiều người dùng đồng thời một cách ổn định và an toàn.
*   **Các tính năng cụ thể**:
    *   **Chuyển đổi sang Kiến trúc API Backend**: Phát triển một API backend mạnh mẽ (sử dụng **FastAPI**) để xử lý các yêu cầu từ nhiều người dùng đồng thời, tách biệt hoàn toàn logic RAG khỏi giao diện người dùng.
    *   **Nâng cấp Cơ sở dữ liệu**: Chuyển đổi hệ thống lưu trữ trạng thái từ SQLite sang một hệ quản trị cơ sở dữ liệu quan hệ (RDBMS) có khả năng mở rộng và xử lý đồng thời cao như **PostgreSQL**.
    *   **Quản lý Phiên độc lập**: Triển khai cơ chế tạo và quản lý ID phiên duy nhất cho mỗi người dùng (sử dụng **UUID**), đảm bảo rằng trạng thái và lịch sử trò chuyện của từng phiên được lưu trữ và truy xuất độc lập trong RDBMS mới.
    *   **Xác thực và Ủy quyền**: Tích hợp các cơ chế xác thực người dùng (sử dụng **Token JWT**) và ủy quyền để đảm bảo mỗi người dùng chỉ có thể truy cập vào dữ liệu và phiên của riêng mình, tăng cường bảo mật.
    *   **Triển khai có khả năng mở rộng**: Đóng gói ứng dụng backend bằng **Docker** và quản lý các container bằng **Docker Compose** trên máy chủ hiện có của bạn. Cân nhắc **Kubernetes** cho việc mở rộng trên nhiều máy chủ trong tương lai.

## 3. Cải thiện Truy xuất (Retrieval) và Xử lý ngữ cảnh nâng cao (Ưu tiên cao nhất)

*   **Mục tiêu**: Nâng cao đáng kể chất lượng và độ chính xác của câu trả lời bằng cách tối ưu hóa quá trình tìm kiếm và xử lý thông tin từ cơ sở tri thức.
*   **Các tính năng cụ thể**:
    *   **Tìm kiếm lai (Hybrid Search)**: Kết hợp tìm kiếm từ khóa **BM25** và tìm kiếm vector (dense retrieval) sử dụng **Reciprocal Rank Fusion (RRF)** để đạt được kết quả truy xuất toàn diện và chính xác hơn.
    *   **Re-ranking**: Triển khai mô hình re-ranker **bge-reranker-base** dựa trên Sentence-Transformers để sắp xếp lại các đoạn văn bản được truy xuất, đảm bảo rằng những thông tin liên quan nhất được ưu tiên đưa vào LLM.
    *   **Tóm tắt ngữ cảnh**: Tích hợp khả năng **tóm tắt trích xuất (Extractive Summarization) bằng LLM (Gemini 2.5 Flash)** các đoạn văn bản được truy xuất trước khi đưa vào LLM, giúp giảm token, tập trung vào thông tin cốt lõi và cải thiện tốc độ phản hồi.
    *   **Lọc ngữ cảnh**: Phát triển cơ chế **lọc dựa trên ngưỡng điểm liên quan (Relevance Score Thresholding)** và **lọc trùng lặp (Duplicate Filtering)** để loại bỏ các đoạn văn bản không liên quan, trùng lặp hoặc nhiễu, làm sạch ngữ cảnh đầu vào cho LLM.
    *   **Truy xuất đa bước (Multi-hop Retrieval)**: Triển khai chiến lược **Iterative Retrieval (Truy xuất lặp lại)**, cho phép tác nhân thực hiện nhiều bước truy xuất thông tin để trả lời các câu hỏi phức tạp, yêu cầu tổng hợp kiến thức từ nhiều nguồn, tận dụng khả năng quản lý luồng của LangGraph.

## 4. Trải nghiệm người dùng (User Experience) - Phát triển Giao diện người dùng (UI)

*   **Mục tiêu**: Cung cấp một giao diện trực quan, thân thiện và dễ sử dụng để người dùng có thể tương tác với tác nhân RAG một cách hiệu quả và thoải mái.
*   **Các tính năng cụ thể**:
    *   **Phát triển Giao diện Web (sử dụng Streamlit)**: Xây dựng một ứng dụng web tương tác hoàn toàn bằng Python với Streamlit để thay thế giao diện dòng lệnh hiện tại. Điều này giúp nhanh chóng có một UI hoạt động mà không cần kiến thức về frontend web truyền thống.
    *   **Thiết kế UI/UX thân thiện**: Tập trung vào thiết kế giao diện người dùng trực quan, sạch sẽ và dễ điều hướng, đảm bảo trải nghiệm người dùng mượt mà.
    *   **Hiển thị Lịch sử Trò chuyện**: Hiển thị rõ ràng toàn bộ lịch sử cuộc trò chuyện, cho phép người dùng dễ dàng theo dõi và tham khảo các tương tác trước đó.
    *   **Hiển thị Trạng thái Xử lý**: Cung cấp phản hồi trực quan cho người dùng về trạng thái hiện tại của hệ thống (ví dụ: "Đang tải...", "Đang tìm kiếm...", "Đang tạo câu trả lời...").
    *   **Cơ chế Phản hồi của người dùng**: Tích hợp các nút đánh giá (ví dụ: "Thích/Không thích", thang điểm) và hộp văn bản để người dùng có thể cung cấp phản hồi về chất lượng câu trả lời, giúp cải thiện hệ thống.
    *   **Ghi nhận Nguồn (Source Attribution)**: Hiển thị các đoạn văn bản gốc được sử dụng để tạo câu trả lời và cung cấp liên kết đến tài liệu nguồn (nếu có), tăng tính minh bạch và độ tin cậy.
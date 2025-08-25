# Tính năng: Xử lý Ý định Mua hàng

Khi người dùng nhập một câu nói có ý định mua hàng, thì hệ thống sẽ truy vấn dữ liệu hàng hóa và trả lời người dùng kèm thông tin các hàng hóa mà họ cần.

## Chi tiết triển khai

### 1. Xác định Ý định Mua hàng (Giai đoạn 1)
- Hệ thống sẽ sử dụng phương pháp kết hợp giữa từ khóa và xác nhận bởi LLM.
- **Từ khóa:** Một danh sách các từ khóa chính sẽ được định nghĩa (ví dụ: `mua`, `giá`, `bao nhiêu tiền`, `đặt hàng`...).
- **Xác nhận bởi LLM:** Nếu câu nói chứa từ khóa, một prompt sẽ được gửi đến LLM để xác nhận chắc chắn đó có phải là ý định mua hàng hay không.

### 2. Nguồn dữ liệu
- Dữ liệu hàng hóa sẽ được truy vấn trực tiếp từ hệ thống e-commerce Saleor.
- **API Endpoint:** `http://localhost:8000/graphql/`
- **Xác thực:** Yêu cầu token (có thể lấy bằng email và mật khẩu).

### 3. Hiển thị thông tin
- Khi trả về kết quả, mỗi sản phẩm sẽ được hiển thị với các thông tin sau:
  - Hình ảnh (thumbnail)
  - Tên sản phẩm
  - Giá
  - Mô tả ngắn (1-2 dòng)
  - Tình trạng tồn kho (Còn hàng / Hết hàng)

from typing import List, TypedDict, Optional

class Message(TypedDict):
    role: str  # 'user' or 'assistant'
    content: str

class AgentState(TypedDict):
    """
    Đại diện cho trạng thái của agent trong suốt cuộc hội thoại.
    """
    question: str  # Câu hỏi hiện tại của người dùng
    context: Optional[str]  # Context đã retrieve được (nếu có)
    answer: Optional[str]  # Câu trả lời của agent
    chat_history: List[Message]  # Lịch sử toàn bộ cuộc hội thoại
    classification_decision: Optional[str] # Quyết định phân loại: 'purchase', 'general_fashion_inquiry', 'off_topic'
    extracted_entities: Optional[dict] # Các thực thể sản phẩm được trích xuất từ câu hỏi của người dùng
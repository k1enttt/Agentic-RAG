from typing import List, TypedDict, Optional
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from src.core.state import AgentState, Message
from src.setup.llm_embeddings import llm
from src.setup.vectorstore import retriever
from src.services.saleor_service import get_saleor_auth_token, search_products

def node_receive_question(state: AgentState) -> AgentState:
    """Nhận câu hỏi từ người dùng."""
    print("---RECEIVING QUESTION---")
    return state

def node_classify_question(state: AgentState) -> AgentState:
    """Phân loại câu hỏi để quyết định luồng xử lý tiếp theo."""
    print("---CLASSIFYING QUESTION---")
    
    prompt = PromptTemplate(
        template="""Bạn là một chuyên gia phân loại câu hỏi. 
        Nhiệm vụ của bạn là phân tích câu hỏi của người dùng và quyết định xem nó thuộc loại nào trong ba loại sau:

        1.  **purchase**: Nếu câu hỏi thể hiện ý định mua hàng, hỏi về giá, hoặc các truy vấn liên quan đến sản phẩm trong một cửa hàng e-commerce.
            *   Ví dụ: "tôi muốn mua áo thun", "giá của đôi giày kia là bao nhiêu?", "bạn có bán quần jean không?".
        2.  **retrieve**: Nếu câu hỏi cần tra cứu thông tin từ một nguồn kiến thức bên ngoài (RAG) để trả lời. Đây là các câu hỏi về các chủ đề cụ thể, không phải kiến thức chung.
            *   Ví dụ: "dự án agentic-rag-3 này hoạt động như thế nào?".
        3.  **generate**: Nếu câu hỏi có thể được trả lời bằng kiến thức chung, hoặc là một lời chào hỏi, một câu trò chuyện thông thường.
            *   Ví dụ: "thủ đô của Pháp là gì?", "bạn có khỏe không?".

        Hãy trả lời bằng một file JSON với một key duy nhất là 'decision' và giá trị là một trong ba lựa chọn: 'purchase', 'retrieve', hoặc 'generate'.

        Câu hỏi của người dùng: {question}
        """,
        input_variables=["question"],
    )
    
    classifier_chain = prompt | llm | JsonOutputParser()
    
    decision = classifier_chain.invoke({"question": state["question"]})
    
    state["classification_decision"] = decision["decision"]
    print(f"Decision: {state['classification_decision']}")
    return state

def node_retrieve_context(state: AgentState) -> AgentState:
    """Truy xuất context từ ChromaDB."""
    print("---RETRIEVING CONTEXT---")
    documents = retriever.invoke(state["question"])
    context = "\n\n".join([doc.page_content for doc in documents])
    state["context"] = context
    print(f"Retrieved context: {context}")
    return state

def node_generate_answer(state: AgentState) -> AgentState:
    """Sinh câu trả lời."""
    print("---GENERATING ANSWER---")
    
    prompt = PromptTemplate(
        template="""Bạn là một bạn nữ dịu dàng và luôn khích lệ người khác. Bạn luôn lắng nghe và đồng cảm với mọi người. Khi trả lời, bạn hãy truyền tải sự ấm áp, tinh thần tích cực và khích lệ người dùng.
        Bạn cần dựa vào context và lịch sử trò chuyện để trả lời. Hãy đọc kỹ context và lịch sử trò chuyện để hiểu rõ câu hỏi của người dùng. Nếu có thể, hãy lồng ghép các chi tiết từ context vào câu trả lời của bạn để thể hiện sự quan tâm.
        Khi context rỗng, bạn có thể sử dụng kiến thức chung để trả lời. Tuy nhiên, hãy đảm bảo rằng câu trả lời của bạn vẫn giữ được sự dịu dàng, khích lệ và luôn hướng đến việc giúp đỡ người dùng một cách tốt nhất.
        
        Lịch sử trò chuyện:
        {chat_history}
        
        Context:
        {context}
        
        Câu hỏi: 
        {question}
        
        Câu trả lời:
        """,
        input_variables=["chat_history", "context", "question"],
    )

    rag_chain = prompt | llm | StrOutputParser()

    # Chuyển đổi chat_history sang chuỗi
    history_str = "".join([f"{msg['role']}: {msg['content']}\n" for msg in state.get("chat_history", [])])

    answer = rag_chain.invoke({
        "chat_history": history_str,
        "context": state.get("context", ""),
        "question": state["question"]
    })

    state["answer"] = answer
    print(f"Answer: {answer}")

    # Cập nhật lịch sử chat
    if "chat_history" not in state or state["chat_history"] is None:
        state["chat_history"] = []
    state["chat_history"] = state["chat_history"] + [
        Message(role="user", content=state["question"]),
        Message(role="assistant", content=answer)
    ]

    return state

def node_ask_to_continue(state: AgentState) -> AgentState:
    """Hỏi người dùng có muốn tiếp tục không.
    Trong phiên bản đơn giản này, node chỉ in ra thông báo.
    Logic thực tế sẽ nằm trong vòng lặp chính.
    """
    print("---ASKING TO CONTINUE---")
    return state

def node_extract_entities(state: AgentState) -> AgentState:
    """
    Trích xuất các thuộc tính sản phẩm từ câu hỏi của người dùng bằng LLM.
    """
    print("---EXTRACTING PRODUCT ENTITIES---")
    
    prompt = PromptTemplate(
        template="""Bạn là một chuyên gia phân tích truy vấn của khách hàng cho một trang web e-commerce.
        Nhiệm vụ của bạn là đọc câu hỏi của người dùng và trích xuất các thông tin chi tiết về sản phẩm mà họ đang tìm kiếm.

        Hãy xác định các thuộc tính sau nếu có:
        - `category`: Loại sản phẩm (ví dụ: "áo thun", "quần jean", "giày thể thao")
        - `name`: Tên cụ thể của sản phẩm nếu có.
        - `color`: Màu sắc (ví dụ: "xanh", "đỏ", "trắng")
        - `size`: Kích cỡ (ví dụ: "S", "M", "L", "XL", "39", "40")
        - `brand`: Thương hiệu (ví dụ: "Nike", "Adidas")
        - `gender`: Giới tính (ví dụ: "nam", "nữ", "trẻ em")
        - `attributes`: Các thuộc tính khác không thuộc các loại trên.

        Hãy trả lời bằng một file JSON với các key tương ứng. Nếu không tìm thấy thông tin cho một thuộc tính, hãy bỏ qua key đó.

        Câu hỏi của người dùng: {question}
        """,
        input_variables=["question"],
    )
    
    entity_extraction_chain = prompt | llm | JsonOutputParser()
    
    extracted_entities = entity_extraction_chain.invoke({"question": state["question"]})
    
    state["extracted_entities"] = extracted_entities
    print(f"Extracted Entities: {state['extracted_entities']}")
    return state

def node_query_saleor(state: AgentState) -> AgentState:
    """
    Truy vấn sản phẩm từ Saleor API dựa trên các thực thể đã trích xuất.
    """
    print("---QUERYING SALEOR---")
    
    extracted_entities = state.get("extracted_entities", {})

    try:
        auth_token = get_saleor_auth_token()
        products = search_products(auth_token, extracted_entities)
        state["saleor_products"] = products
        print(f"Found {len(products)} products from Saleor.")
    except Exception as e:
        print(f"Error querying Saleor: {e}")
        state["saleor_products"] = [] # Ensure it's an empty list on error
        state["saleor_error"] = str(e) # Store error message for potential handling
    
    return state

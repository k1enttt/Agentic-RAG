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
        template="""Bạn là một người tư vấn thời trang thân thiện và chuyên nghiệp tại cửa hàng. 
        Nhiệm vụ của bạn là phân tích câu hỏi của người dùng và quyết định xem nó thuộc loại nào trong ba loại sau:

        1.  **purchase**: Nếu câu hỏi thể hiện ý định mua hàng, hỏi về giá, size, màu sắc, hoặc các truy vấn liên quan trực tiếp đến việc mua sản phẩm trong cửa hàng.
            *   Ví dụ: "tôi muốn mua áo thun màu xanh size M", "giá của chiếc váy này là bao nhiêu?", "cửa hàng có quần jean không?".
        2.  **general_fashion_inquiry**: Nếu câu hỏi liên quan đến thời trang nói chung, lời khuyên phối đồ, xu hướng, hoặc các thông tin chung về cửa hàng (ví dụ: chính sách đổi trả, giờ mở cửa).
            *   Ví dụ: "mùa hè này nên mặc gì?", "chân váy midi phối với áo gì đẹp?", "chính sách đổi trả của cửa hàng là gì?".
        3.  **off_topic**: Nếu câu hỏi không liên quan đến thời trang, mua bán, hoặc các vấn đề của cửa hàng.
            *   Ví dụ: "hôm nay bạn có vui không?", "thời tiết hôm nay thế nào?", "bạn tên gì?".

        Hãy trả lời bằng một file JSON với một key duy nhất là 'decision' và giá trị là một trong ba lựa chọn: 'purchase', 'general_fashion_inquiry', hoặc 'off_topic'.

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
    
    new_state = state.copy()
    new_state["extracted_entities"] = extracted_entities
    print(f"Áo từ câu hỏi của user: {new_state}")
    return new_state

def node_query_saleor(state: AgentState) -> AgentState:
    """
    Truy vấn sản phẩm từ Saleor API dựa trên các thực thể đã trích xuất.
    """
    print("---QUERYING SALEOR---")
    
    # Ensure extracted_entities is retrieved correctly from the state
    extracted_entities = state.get("extracted_entities", {})
    print(f"Áo từ state: {state}")
    

    try:
        auth_token = get_saleor_auth_token()
        products = search_products(auth_token, extracted_entities)
        state["saleor_products"] = products
        print(f"Found {len(products)} products from Saleor.")

        if not products:
            # Construct a persona-aligned message if no products are found
            category = extracted_entities.get("category", "sản phẩm")
            color = extracted_entities.get("color", "")
            size = extracted_entities.get("size", "")
            
            # Build a more specific description if possible
            item_name_parts = []
            if category:
                item_name_parts.append(category)
            if color:
                item_name_parts.append(color)
            if size:
                item_name_parts.append(f"size {size}")

            if item_name_parts:
                item_name = " ".join(item_name_parts).strip()
            else:
                item_name = "sản phẩm" # More direct fallback

            

            no_product_message = (
                f"Mình rất tiếc, hiện tại cửa hàng mình chưa có {item_name} nào. "
                "Bạn có muốn mình tìm kiếm với tiêu chí khác không, hay bạn muốn mình gợi ý một số mẫu khác đang có sẵn không ạ?"
            )
            
            state["answer"] = no_product_message
            print(f"Agent response (no products): {no_product_message}")

    except Exception as e:
        print(f"Error querying Saleor: {e}")
        state["saleor_products"] = [] # Ensure it's an empty list on error
        state["saleor_error"] = str(e) # Store error message for potential handling
        state["answer"] = f"Rất tiếc, có lỗi xảy ra khi tìm kiếm sản phẩm: {e}. Bạn có thể thử lại sau hoặc hỏi mình về một sản phẩm khác nhé!"
    
    return state

def node_handle_general_inquiry(state: AgentState) -> AgentState:
    """
    Xử lý các câu hỏi liên quan đến thời trang nói chung.
    Quyết định xem có cần RAG hay chỉ cần LLM tự sinh câu trả lời.
    """
    print("---HANDLING GENERAL FASHION INQUIRY---")
    question = state["question"].lower()
    
    # Simple keyword-based decision for RAG vs. LLM-only
    # In a more advanced version, this would be another LLM classification or tool calling
    if "chính sách" in question or "đổi trả" in question or "thông tin cửa hàng" in question:
        print("---Triggering RAG for specific inquiry---")
        # Call retrieve_context if needed, then generate_answer
        # For now, we'll just call retrieve_context and then generate_answer will use the context
        # If no context is found, generate_answer will use general knowledge
        return node_retrieve_context(state)
    else:
        print("---Generating answer with general LLM knowledge---")
        # No specific context retrieval needed, just generate answer
        # The generate_answer node already handles empty context
        return state # Pass state directly to generate_answer, which will be the next node in the graph

def node_handle_off_topic(state: AgentState) -> AgentState:
    """
    Xử lý các câu hỏi không liên quan đến thời trang hoặc mua sắm.
    Tạo ra một câu trả lời nhẹ nhàng nhắc nhở người dùng, có tính đến câu hỏi của họ.
    """
    print("---HANDLING OFF-TOPIC QUESTION---")

    prompt = PromptTemplate(
        template="""Bạn là một người tư vấn thời trang thân thiện, dịu dàng và luôn lắng nghe khách hàng.
        Khi khách hàng hỏi một câu không liên quan đến thời trang hay mua bán, bạn cần phản hồi một cách tinh tế.
        Phản hồi của bạn nên có hai phần:
        1.  Thừa nhận hoặc phản hồi ngắn gọn, đồng cảm với câu nói lạc đề của khách hàng.
        2.  Nhẹ nhàng chuyển hướng cuộc trò chuyện về chủ đề thời trang, mua bán quần áo hoặc tư vấn phối đồ.
        Hãy đảm bảo giọng điệu luôn ấm áp, tích cực và khích lệ người dùng.

        Ví dụ:
        - Khách hàng: "Hôm nay bạn có vui không?"
        - Bạn: "Cảm ơn bạn đã hỏi thăm, mình luôn sẵn lòng để hỗ trợ bạn! Hiện tại mình đang ở đây để tư vấn về thời trang và các sản phẩm của cửa hàng. Bạn có đang tìm kiếm trang phục nào hay cần lời khuyên phối đồ không ạ?"

        - Khách hàng: "Thời tiết hôm nay thế nào?"
        - Bạn: "Mình rất tiếc, mình không thể cung cấp thông tin về thời tiết được ạ. Nhưng nếu bạn đang băn khoăn không biết mặc gì cho thời tiết hôm nay, mình rất sẵn lòng tư vấn những bộ trang phục phù hợp nhất. Bạn có muốn mình gợi ý không?"

        Câu hỏi lạc đề của khách hàng: {question}
        Phản hồi của bạn:
        """,
        input_variables=["question"],
    )

    off_topic_chain = prompt | llm | StrOutputParser()
    off_topic_response = off_topic_chain.invoke({"question": state["question"]})
    
    state["answer"] = off_topic_response
    print(f"Off-topic response: {off_topic_response}")

    # Cập nhật lịch sử chat
    if "chat_history" not in state or state["chat_history"] is None:
        state["chat_history"] = []
    state["chat_history"] = state["chat_history"] + [
        Message(role="user", content=state["question"]),
        Message(role="assistant", content=off_topic_response)
    ]
    
    return state

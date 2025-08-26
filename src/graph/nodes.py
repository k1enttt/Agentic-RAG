from typing import List, TypedDict, Optional
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from src.core.state import AgentState, Message
from src.setup.llm_embeddings import llm
from src.setup.vectorstore import retriever
from src.services.saleor_service import get_saleor_auth_token, search_products
from src.graph.prompts import (
    CLASSIFY_QUESTION_PROMPT,
    GENERATE_ANSWER_PROMPT,
    EXTRACT_ENTITIES_PROMPT,
    HANDLE_OFF_TOPIC_PROMPT,
)

def node_receive_question(state: AgentState) -> AgentState:
    """Nhận câu hỏi từ người dùng."""
    print("---RECEIVING QUESTION---")
    return state

def node_classify_question(state: AgentState) -> AgentState:
    """Phân loại câu hỏi để quyết định luồng xử lý tiếp theo."""
    print("---CLASSIFYING QUESTION---")
    
    classifier_chain = CLASSIFY_QUESTION_PROMPT | llm | JsonOutputParser()
    
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
    
    rag_chain = GENERATE_ANSWER_PROMPT | llm | StrOutputParser()

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
    
    entity_extraction_chain = EXTRACT_ENTITIES_PROMPT | llm | JsonOutputParser()
    
    extracted_entities = entity_extraction_chain.invoke({"question": state["question"]})
    
    state["extracted_entities"] = extracted_entities
    return state

def node_query_saleor(state: AgentState) -> AgentState:
    """
    Truy vấn sản phẩm từ Saleor API dựa trên các thực thể đã trích xuất.
    """
    print("---QUERYING SALEOR---")
    
    # Ensure extracted_entities is retrieved correctly from the state
    extracted_entities = state.get("extracted_entities", {})
   
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

    off_topic_chain = HANDLE_OFF_TOPIC_PROMPT | llm | StrOutputParser()
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
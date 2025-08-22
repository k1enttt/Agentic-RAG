from typing import List, TypedDict, Optional
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from src.core.state import AgentState, Message
from src.setup.llm_embeddings import llm
from src.setup.vectorstore import retriever

def node_receive_question(state: AgentState) -> AgentState:
    """Nhận câu hỏi từ người dùng."""
    print("---RECEIVING QUESTION---")
    return state

def node_classify_question(state: AgentState) -> AgentState:
    """Phân loại câu hỏi để quyết định có cần RAG hay không."""
    print("---CLASSIFYING QUESTION---")
    
    prompt = PromptTemplate(
        template="""Bạn là một chuyên gia phân loại câu hỏi. 
        Nhiệm vụ của bạn là phân tích câu hỏi của người dùng và quyết định xem nó có thể được trả lời trực tiếp bằng kiến thức chung của một LLM hay cần phải tra cứu thông tin từ một nguồn kiến thức bên ngoài (RAG).
        
        Hãy trả lời bằng một file JSON với một key duy nhất là 'decision' và giá trị là một trong hai lựa chọn sau:
        - 'retrieve': nếu câu hỏi cần tra cứu thông tin (ví dụ: hỏi về các chủ đề rất cụ thể, mới, hoặc cần dữ liệu chính xác).
        - 'generate': nếu câu hỏi có thể được trả lời bằng kiến thức chung.

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

import sys
import os

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import json
import uuid
import sqlite3
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver
from src.core.state import AgentState, Message
from src.config import SQLITE_CHECKPOINT_PATH
from src.graph.nodes import (
    node_receive_question,
    node_classify_question,
    node_retrieve_context,
    node_generate_answer,
    node_ask_to_continue,
    node_extract_entities,
    node_query_saleor,
    node_handle_general_inquiry, # New node
    node_handle_off_topic,      # New node
)

# Xây dựng Graph
workflow = StateGraph(AgentState)

# Thêm các node
workflow.add_node("receive_question", node_receive_question)
workflow.add_node("classify_question", node_classify_question)
workflow.add_node("retrieve_context", node_retrieve_context) # Keep for now, might be used by handle_general_inquiry
workflow.add_node("generate_answer", node_generate_answer)
workflow.add_node("ask_to_continue", node_ask_to_continue)
workflow.add_node("extract_entities", node_extract_entities)
workflow.add_node("query_saleor", node_query_saleor)
workflow.add_node("handle_general_inquiry", node_handle_general_inquiry) # New node
workflow.add_node("handle_off_topic", node_handle_off_topic)      # New node

# Đặt entry point
workflow.set_entry_point("receive_question")

# Thêm các cạnh
workflow.add_edge("receive_question", "classify_question")
workflow.add_edge("retrieve_context", "generate_answer")
workflow.add_edge("generate_answer", "ask_to_continue")

# New edges for purchase flow
workflow.add_edge("extract_entities", "query_saleor")
workflow.add_edge("query_saleor", "ask_to_continue")

# New edges for general inquiry and off-topic flows
workflow.add_edge("handle_general_inquiry", "generate_answer")
workflow.add_edge("handle_off_topic", "ask_to_continue")

# Thêm cạnh điều kiện sau khi phân loại
def route_after_classification(state: AgentState):
    """Routing function to decide the next step based on classification."""
    decision = state.get("classification_decision")
    if decision == "purchase":
        return "extract_entities"
    elif decision == "general_fashion_inquiry":
        return "handle_general_inquiry"
    elif decision == "off_topic":
        return "handle_off_topic"
    else: # Fallback, though classify_question should always return one of the above
        return "generate_answer" # Or a dedicated error handling node

workflow.add_conditional_edges(
    "classify_question",
    route_after_classification,
    {
        "extract_entities": "extract_entities",
        "handle_general_inquiry": "handle_general_inquiry",
        "handle_off_topic": "handle_off_topic",
        "generate_answer": "generate_answer", # Fallback, if route_after_classification returns this
    }
)

# Cạnh cuối cùng sẽ được xử lý trong vòng lặp chính
workflow.add_edge("ask_to_continue", END)

# Tích hợp lưu trữ trạng thái
memory = SqliteSaver(conn=sqlite3.connect(os.path.join(project_root, SQLITE_CHECKPOINT_PATH), check_same_thread=False))

# Biên dịch graph
app = workflow.compile(checkpointer=memory)

if __name__ == "__main__":
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    print("Agent: Chào bạn! Mình là trợ lý tư vấn thời trang của cửa hàng. Rất vui được hỗ trợ bạn. Bạn đang tìm kiếm trang phục nào hay cần lời khuyên phối đồ không ạ?")
    print("Gõ \'quit\' hoặc \'exit\' để thoát.")

    while True:
        user_input = input("User: ")
        if user_input.lower() in ["quit", "exit"]:
            break

        events = app.stream(
            {"question": user_input},
            config=config
        )
        for event in events:
            if "__end__" in event:
                final_state = event["__end__"]
                # Print Saleor products if found, otherwise print the answer
                if final_state.get("saleor_products"):
                    print("Agent: Đây là những sản phẩm tôi tìm được:")
                    for product in final_state["saleor_products"]:
                        print(f"  - Tên: {product.get('name')}, Giá: {product.get('price')}, Tồn kho: {product.get('stock')}")
                        if product.get("thumbnail_url"):
                            print(f"    Ảnh: {product.get('thumbnail_url')}")
                        if product.get("description"):
                            # Simple parsing for now, assuming it's a JSON string with 'blocks' and 'text'
                            try:
                                desc_json = json.loads(product.get("description"))
                                desc_text = " ".join([block["data"]["text"] for block in desc_json.get("blocks", []) if "text" in block["data"]])
                                print(f"    Mô tả: {desc_text}")
                            except:
                                print(f"    Mô tả: {product.get('description')}")
                elif final_state.get("saleor_error"):
                    print(f"Agent: Rất tiếc, có lỗi xảy ra khi tìm kiếm sản phẩm: {final_state['saleor_error']}")
                else:
                    print(f"Agent: {final_state.get('answer', 'Không tìm thấy câu trả lời.')}")

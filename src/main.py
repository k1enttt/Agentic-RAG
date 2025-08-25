import sys
import os

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

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
)

# Xây dựng Graph
workflow = StateGraph(AgentState)

# Thêm các node
workflow.add_node("receive_question", node_receive_question)
workflow.add_node("classify_question", node_classify_question)
workflow.add_node("retrieve_context", node_retrieve_context)
workflow.add_node("generate_answer", node_generate_answer)
workflow.add_node("ask_to_continue", node_ask_to_continue)

# Đặt entry point
workflow.set_entry_point("receive_question")

# Thêm các cạnh
workflow.add_edge("receive_question", "classify_question")
workflow.add_edge("retrieve_context", "generate_answer")
workflow.add_edge("generate_answer", "ask_to_continue")

# Thêm cạnh điều kiện sau khi phân loại
def decide_to_retrieve(state: AgentState):
    if state.get("classification_decision") == "retrieve":
        return "retrieve_context"
    else:
        return "generate_answer"

workflow.add_conditional_edges(
    "classify_question",
    decide_to_retrieve,
    {
        "retrieve_context": "retrieve_context",
        "generate_answer": "generate_answer",
    }
)

# Cạnh cuối cùng sẽ được xử lý trong vòng lặp chính
workflow.add_edge("ask_to_continue", END)

# Tích hợp lưu trữ trạng thái
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
memory = SqliteSaver(conn=sqlite3.connect(os.path.join(project_root, SQLITE_CHECKPOINT_PATH), check_same_thread=False))

# Biên dịch graph
app = workflow.compile(checkpointer=memory)

if __name__ == "__main__":
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    print("Bắt đầu cuộc trò chuyện mới. Gõ \'quit\' hoặc \'exit\' để thoát.")

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
                print(f"Agent: {final_state['answer']}")

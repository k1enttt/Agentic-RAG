# Gemini Workspace Context

## Project Overview
This project is a LangGraph-based agent designed to handle user queries through a command-line interface. It classifies questions to determine if they can be answered directly by an LLM or if they require additional context from a knowledge base. The agent retrieves context from a ChromaDB vector store and manages the conversational session. The entire workflow is defined and managed by LangGraph, with the state persisted in a SQLite database.

The agent's workflow is as follows:
1.  Receive user question from the command line.
2.  Classify the question into two types: one that the LLM can answer directly, and one that requires additional context.
3.  If necessary, retrieve context from a ChromaDB vector store.
4.  Generate an answer based on the question and retrieved context.
5.  Ask the user via the command line if they want to continue the conversation.

## Building and Running
**Dependencies:**
The project's dependencies are listed in `requirements.txt`. To install them, run:
```bash
pip install -r requirements.txt
```

**Running the agent:**
To run the agent, navigate to the project's root directory and execute:
```bash
python src/main.py
```

## Development Conventions
The project follows a modular and organized structure:

```
agentic-rag-3/
├── .git/
├── .venv/
├── .gitignore
├── .env
├── requirements.txt
├── docs/                   # Chứa tất cả các tài liệu Markdown
│   ├── design_document.md
│   ├── GEMINI.md
│   ├── plan_v1.md
│   ├── lessons_learned.md
│   └── todo.md
├── src/                    # Mã nguồn chính của ứng dụng
│   ├── __init__.py         # Đánh dấu 'src' là một Python package
│   ├── main.py             # Điểm khởi chạy chính của ứng dụng
│   ├── config.py           # Các hằng số cấu hình toàn dự án
│   ├── core/               # Logic cốt lõi của agent
│   │   ├── __init__.py
│   │   └── state.py        # Định nghĩa AgentState
│   ├── setup/              # Các file thiết lập LLM, Embeddings, Vector Store
│   │   ├── __init__.py
│   │   ├── llm_embeddings.py # Khởi tạo LLM và Embeddings
│   │   └── vectorstore.py    # Thiết lập ChromaDB và Retriever
│   └── graph/              # Các node và định nghĩa LangGraph
│       ├── __init__.py
│       └── nodes.py        # Các hàm node của LangGraph
├── data/                   # Dữ liệu thô cho RAG
│   └── sample_data.txt
├── storage/                # Dữ liệu bền vững được tạo ra bởi ứng dụng
│   ├── chroma_db/          # Thư mục lưu trữ ChromaDB
│   └── memory.sqlite       # File SQLite lưu trạng thái hội thoại
└── checkpoints/            # (Giữ lại, mặc dù hiện tại trống, có thể dùng sau)
```

*   **`src/core/state.py`**: Định nghĩa `AgentState` `TypedDict`. `TypedDict` này đại diện cho trạng thái của agent, bao gồm `question`, `context`, `answer`, và `chat_history`. Việc tách riêng file này giúp định nghĩa trạng thái rõ ràng và tái sử dụng được.
*   **`src/main.py`**: Đây là điểm khởi chạy chính của ứng dụng. Nó chứa logic cốt lõi để xây dựng LangGraph agent, bao gồm khởi tạo `StateGraph`, định nghĩa các cạnh, thiết lập `SqliteSaver` để duy trì trạng thái, và chạy vòng lặp chính để nhận input từ người dùng và thực thi graph.

## Language Models
*   **Generation and Classification:** The agent will use the `Gemini 2.5 Flash` model.
*   **Embeddings:** The agent will use the `bge-m3` model served via Ollama (`OllamaEmbeddings`) to generate vector embeddings for the RAG pipeline.

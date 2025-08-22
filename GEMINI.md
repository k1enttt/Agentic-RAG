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
*TODO: Add instructions on how to run the agent once the main script is available.*

## Development Conventions
The project follows a modular structure:

*   `state.py`: This file defines the `AgentState` `TypedDict`. This `TypedDict` represents the state of the agent, including the `question`, `context`, `answer`, and `chat_history`. This keeps the state definition separate and reusable.
*   `main.py`: This will be the main entry point of the application. It will contain the core logic for the LangGraph agent, including:
    *   Initializing the LangGraph `StateGraph`.
    *   Defining the nodes (as Python functions) for the graph.
    *   Defining the edges that connect the nodes.
    *   Setting up the `SqliteSaver` for persistence.
    *   Running the main application loop to get user input and execute the graph.

## Language Models
*   **Generation and Classification:** The agent will use the `GPT-2.5-flash` model.
*   **Embeddings:** The agent will use the `bge-m3` model served via Ollama (`OllamaEmbeddings`) to generate vector embeddings for the RAG pipeline.

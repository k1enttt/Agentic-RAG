import os
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader
from src.setup.llm_embeddings import embeddings
from src.config import VECTORSTORE_PATH, SAMPLE_DATA_PATH

# Khởi tạo retriever
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')) # Go up two levels from src/setup/ to project root
full_vectorstore_path = os.path.join(project_root, VECTORSTORE_PATH)
full_sample_data_path = os.path.join(project_root, SAMPLE_DATA_PATH)

# Khởi tạo retriever
if not os.path.exists(full_vectorstore_path):
    print("---CREATING NEW VECTORSTORE---")
    # Tải dữ liệu
    loader = TextLoader(full_sample_data_path, encoding="utf-8")
    documents = loader.load()

    # Chia nhỏ văn bản
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    splits = text_splitter.split_documents(documents)

    # Tạo và lưu vectorstore
    vectorstore = Chroma.from_documents(documents=splits, embedding=embeddings, persist_directory=full_vectorstore_path)
else:
    vectorstore = Chroma(persist_directory=full_vectorstore_path, embedding_function=embeddings)

retriever = vectorstore.as_retriever()

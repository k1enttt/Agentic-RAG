from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import OllamaEmbeddings
from src.config import LLM_MODEL_NAME, EMBEDDINGS_MODEL_NAME

# Tải các biến môi trường từ file .env
load_dotenv()

# Khởi tạo LLM
llm = ChatGoogleGenerativeAI(model=LLM_MODEL_NAME, temperature=0)

# Khởi tạo Embeddings
embeddings = OllamaEmbeddings(model=EMBEDDINGS_MODEL_NAME)

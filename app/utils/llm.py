from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from app.config.config import settings
import logging

logger = logging.getLogger("semanticsql")

# Initialize chat model
chat_model = ChatGoogleGenerativeAI(
    model=settings.GEMINI_MODEL,
    google_api_key=settings.GEMINI_API_KEY,
    temperature=settings.MODEL_TEMPERATURE
)

# Initialize embeddings model
embeddings_model = GoogleGenerativeAIEmbeddings(
    model="models/embedding-001",
    google_api_key=settings.GEMINI_API_KEY
) 
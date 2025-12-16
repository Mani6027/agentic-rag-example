from langchain_google_genai import GoogleGenerativeAIEmbeddings
from src.config.settings import settings
from src.utils.logger import logger


class EmbeddingManager:
    """Manager for creating and managing embeddings using Google Generative AI."""

    _instance = None

    def __new__(cls):
        """Singleton pattern to reuse embeddings instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize the embedding manager."""
        if self._initialized:
            return

        logger.info("Initializing Google Generative AI Embeddings")

        try:
            self.embeddings = GoogleGenerativeAIEmbeddings(
                model="models/embedding-001",
                google_api_key=settings.google_api_key
            )
            self._initialized = True
            logger.info("Embedding manager initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize embeddings: {str(e)}")
            raise

    def get_embeddings(self) -> GoogleGenerativeAIEmbeddings:
        """
        Get the embeddings instance.

        Returns:
            GoogleGenerativeAIEmbeddings instance
        """
        return self.embeddings


# Global embedding manager instance
embedding_manager = EmbeddingManager()

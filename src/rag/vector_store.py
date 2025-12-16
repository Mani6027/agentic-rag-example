from typing import List, Dict, Optional
import threading
from langchain.docstore.document import Document
from langchain_community.vectorstores import Chroma
from src.rag.embeddings import embedding_manager
from src.utils.logger import logger


class VectorStoreManager:
    """Manager for Chroma vector stores (one per dataset)."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """Singleton pattern to ensure only one instance exists."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize the vector store manager."""
        if self._initialized:
            return

        self._stores: Dict[str, Chroma] = {}
        self._store_lock = threading.Lock()
        self.embeddings = embedding_manager.get_embeddings()
        self._initialized = True
        logger.info("VectorStoreManager initialized")

    def create_store(
        self,
        dataset_id: str,
        documents: List[Document]
    ) -> None:
        """
        Create a vector store for a dataset.

        Args:
            dataset_id: Unique dataset identifier
            documents: List of Document objects to embed

        Raises:
            ValueError: If dataset already has a vector store
        """
        with self._store_lock:
            if dataset_id in self._stores:
                logger.warning(
                    f"Vector store for dataset {dataset_id} already exists. "
                    "Deleting old store and creating new one."
                )
                self.delete_store(dataset_id)

            try:
                logger.info(
                    f"Creating vector store for dataset {dataset_id} "
                    f"with {len(documents)} documents"
                )

                # Create in-memory Chroma vector store
                vector_store = Chroma.from_documents(
                    documents=documents,
                    embedding=self.embeddings,
                    collection_name=f"dataset_{dataset_id}"
                )

                self._stores[dataset_id] = vector_store
                logger.info(
                    f"Vector store created successfully for dataset {dataset_id}"
                )

            except Exception as e:
                logger.error(
                    f"Failed to create vector store for dataset {dataset_id}: {str(e)}"
                )
                raise ValueError(
                    f"Failed to create vector store: {str(e)}"
                )

    def query_metadata(
        self,
        dataset_id: str,
        query: str,
        k: int = 5,
        filter_metadata: Optional[Dict] = None
    ) -> List[Document]:
        """
        Query the vector store for relevant metadata.

        Args:
            dataset_id: Dataset identifier
            query: Query string
            k: Number of results to return
            filter_metadata: Optional metadata filter

        Returns:
            List of relevant Document objects

        Raises:
            ValueError: If vector store doesn't exist
        """
        with self._store_lock:
            if dataset_id not in self._stores:
                raise ValueError(
                    f"Vector store for dataset {dataset_id} not found. "
                    "Please upload the dataset first."
                )

            try:
                vector_store = self._stores[dataset_id]

                if filter_metadata:
                    results = vector_store.similarity_search(
                        query,
                        k=k,
                        filter=filter_metadata
                    )
                else:
                    results = vector_store.similarity_search(query, k=k)

                logger.info(
                    f"Retrieved {len(results)} documents for query: '{query}'"
                )
                return results

            except Exception as e:
                logger.error(f"Query failed: {str(e)}")
                raise ValueError(f"Failed to query vector store: {str(e)}")

    def get_column_info(
        self,
        dataset_id: str,
        column_name: Optional[str] = None,
        k: int = 3
    ) -> List[Document]:
        """
        Get information about specific columns.

        Args:
            dataset_id: Dataset identifier
            column_name: Optional specific column name
            k: Number of results to return

        Returns:
            List of Document objects with column information
        """
        if column_name:
            query = f"column {column_name}"
            filter_metadata = {
                "type": "column_info",
                "column_name": column_name
            }
        else:
            query = "all columns information"
            filter_metadata = {"type": "column_info"}

        return self.query_metadata(
            dataset_id,
            query,
            k=k,
            filter_metadata=filter_metadata
        )

    def get_sheet_summary(self, dataset_id: str, sheet_name: str) -> List[Document]:
        """
        Get summary information for a specific sheet.

        Args:
            dataset_id: Dataset identifier
            sheet_name: Sheet name

        Returns:
            List of Document objects with sheet summary
        """
        return self.query_metadata(
            dataset_id,
            f"summary of sheet {sheet_name}",
            k=1,
            filter_metadata={
                "type": "sheet_summary",
                "sheet_name": sheet_name
            }
        )

    def delete_store(self, dataset_id: str) -> None:
        """
        Delete a vector store.

        Args:
            dataset_id: Dataset identifier

        Raises:
            ValueError: If vector store doesn't exist
        """
        with self._store_lock:
            if dataset_id not in self._stores:
                raise ValueError(f"Vector store for dataset {dataset_id} not found")

            # Delete the Chroma collection
            try:
                vector_store = self._stores[dataset_id]
                vector_store.delete_collection()
            except Exception as e:
                logger.warning(f"Error deleting Chroma collection: {str(e)}")

            del self._stores[dataset_id]
            logger.info(f"Vector store deleted for dataset {dataset_id}")

    def store_exists(self, dataset_id: str) -> bool:
        """
        Check if a vector store exists for a dataset.

        Args:
            dataset_id: Dataset identifier

        Returns:
            True if store exists, False otherwise
        """
        with self._store_lock:
            return dataset_id in self._stores

    def list_stores(self) -> List[str]:
        """
        List all dataset IDs with vector stores.

        Returns:
            List of dataset IDs
        """
        with self._store_lock:
            return list(self._stores.keys())


# Global vector store manager instance
vector_store_manager = VectorStoreManager()

import threading
from typing import Dict, Optional, List
from datetime import datetime
import pandas as pd
from src.utils.logger import logger


class DataStore:
    """Thread-safe in-memory storage for uploaded Excel datasets."""

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
        """Initialize the data store."""
        if self._initialized:
            return

        self._datasets: Dict[str, Dict[str, pd.DataFrame]] = {}
        self._metadata: Dict[str, dict] = {}
        self._data_lock = threading.Lock()
        self._initialized = True
        logger.info("DataStore initialized")

    def add_dataset(
        self,
        dataset_id: str,
        sheets: Dict[str, pd.DataFrame],
        metadata: dict
    ) -> None:
        """
        Add a new dataset to the store.

        Args:
            dataset_id: Unique identifier for the dataset
            sheets: Dictionary of sheet_name -> DataFrame
            metadata: Dataset metadata (filename, upload time, etc.)
        """
        with self._data_lock:
            self._datasets[dataset_id] = sheets
            self._metadata[dataset_id] = {
                **metadata,
                "uploaded_at": datetime.utcnow().isoformat()
            }
            logger.info(f"Dataset {dataset_id} added to store with {len(sheets)} sheets")

    def get_dataframe(
        self,
        dataset_id: str,
        sheet_name: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Get a DataFrame from the store.

        Args:
            dataset_id: Dataset identifier
            sheet_name: Optional sheet name (returns first sheet if None)

        Returns:
            DataFrame for the specified dataset and sheet

        Raises:
            ValueError: If dataset or sheet not found
        """
        with self._data_lock:
            if dataset_id not in self._datasets:
                raise ValueError(f"Dataset {dataset_id} not found")

            sheets = self._datasets[dataset_id]

            if sheet_name:
                if sheet_name not in sheets:
                    available_sheets = list(sheets.keys())
                    raise ValueError(
                        f"Sheet '{sheet_name}' not found. "
                        f"Available sheets: {available_sheets}"
                    )
                return sheets[sheet_name].copy()
            else:
                # Return first sheet
                first_sheet = list(sheets.values())[0]
                return first_sheet.copy()

    def get_all_sheets(self, dataset_id: str) -> Dict[str, pd.DataFrame]:
        """
        Get all sheets for a dataset.

        Args:
            dataset_id: Dataset identifier

        Returns:
            Dictionary of sheet_name -> DataFrame

        Raises:
            ValueError: If dataset not found
        """
        with self._data_lock:
            if dataset_id not in self._datasets:
                raise ValueError(f"Dataset {dataset_id} not found")
            return {name: df.copy() for name, df in self._datasets[dataset_id].items()}

    def get_metadata(self, dataset_id: str) -> dict:
        """
        Get metadata for a dataset.

        Args:
            dataset_id: Dataset identifier

        Returns:
            Dataset metadata

        Raises:
            ValueError: If dataset not found
        """
        with self._data_lock:
            if dataset_id not in self._metadata:
                raise ValueError(f"Dataset {dataset_id} not found")
            return self._metadata[dataset_id].copy()

    def delete_dataset(self, dataset_id: str) -> None:
        """
        Delete a dataset from the store.

        Args:
            dataset_id: Dataset identifier

        Raises:
            ValueError: If dataset not found
        """
        with self._data_lock:
            if dataset_id not in self._datasets:
                raise ValueError(f"Dataset {dataset_id} not found")

            del self._datasets[dataset_id]
            del self._metadata[dataset_id]
            logger.info(f"Dataset {dataset_id} deleted from store")

    def list_datasets(self) -> List[dict]:
        """
        List all datasets in the store.

        Returns:
            List of dataset metadata dictionaries
        """
        with self._data_lock:
            return [
                {
                    "dataset_id": dataset_id,
                    **metadata
                }
                for dataset_id, metadata in self._metadata.items()
            ]

    def dataset_exists(self, dataset_id: str) -> bool:
        """
        Check if a dataset exists.

        Args:
            dataset_id: Dataset identifier

        Returns:
            True if dataset exists, False otherwise
        """
        with self._data_lock:
            return dataset_id in self._datasets

    def get_sheet_names(self, dataset_id: str) -> List[str]:
        """
        Get list of sheet names for a dataset.

        Args:
            dataset_id: Dataset identifier

        Returns:
            List of sheet names

        Raises:
            ValueError: If dataset not found
        """
        with self._data_lock:
            if dataset_id not in self._datasets:
                raise ValueError(f"Dataset {dataset_id} not found")
            return list(self._datasets[dataset_id].keys())


# Global data store instance
data_store = DataStore()

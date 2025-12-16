from typing import Dict, List
from pathlib import Path
import pandas as pd
from src.utils.logger import logger


class ExcelHandler:
    """Handler for processing Excel files."""

    @staticmethod
    def process_file(file_path: str) -> Dict[str, pd.DataFrame]:
        """
        Read Excel file and return dictionary of sheet_name -> DataFrame.

        Args:
            file_path: Path to Excel file

        Returns:
            Dictionary mapping sheet names to DataFrames

        Raises:
            ValueError: If file cannot be read or is invalid
        """
        try:
            file_path_obj = Path(file_path)

            if not file_path_obj.exists():
                raise ValueError(f"File not found: {file_path}")

            if file_path_obj.suffix.lower() not in ['.xlsx', '.xls']:
                raise ValueError(
                    f"Invalid file format: {file_path_obj.suffix}. "
                    "Supported formats: .xlsx, .xls"
                )

            logger.info(f"Processing Excel file: {file_path}")

            # Read Excel file
            excel_file = pd.ExcelFile(file_path)
            sheets = {}

            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(file_path, sheet_name=sheet_name)

                # Clean column names
                df.columns = (
                    df.columns
                    .str.strip()
                    .str.lower()
                    .str.replace(' ', '_')
                    .str.replace('[^a-z0-9_]', '', regex=True)
                )

                # Remove completely empty rows and columns
                df = df.dropna(how='all', axis=0)
                df = df.dropna(how='all', axis=1)

                sheets[sheet_name] = df
                logger.info(
                    f"Processed sheet '{sheet_name}': "
                    f"{len(df)} rows, {len(df.columns)} columns"
                )

            if not sheets:
                raise ValueError("No valid sheets found in Excel file")

            return sheets

        except Exception as e:
            logger.error(f"Error processing Excel file: {str(e)}")
            raise ValueError(f"Failed to process Excel file: {str(e)}")

    @staticmethod
    def get_metadata(sheets: Dict[str, pd.DataFrame], filename: str) -> dict:
        """
        Extract basic metadata from sheets.

        Args:
            sheets: Dictionary of sheet_name -> DataFrame
            filename: Original filename

        Returns:
            Dictionary containing metadata
        """
        metadata = {
            "filename": filename,
            "sheets": list(sheets.keys()),
            "columns": {},
            "rows_count": {},
            "dtypes": {}
        }

        for sheet_name, df in sheets.items():
            metadata["columns"][sheet_name] = list(df.columns)
            metadata["rows_count"][sheet_name] = len(df)
            metadata["dtypes"][sheet_name] = {
                col: str(dtype) for col, dtype in df.dtypes.items()
            }

        logger.info(f"Extracted metadata for {len(sheets)} sheets")
        return metadata

    @staticmethod
    def get_sample_data(
        sheets: Dict[str, pd.DataFrame],
        n: int = 5
    ) -> Dict[str, List[dict]]:
        """
        Get sample rows from each sheet.

        Args:
            sheets: Dictionary of sheet_name -> DataFrame
            n: Number of sample rows to retrieve

        Returns:
            Dictionary of sheet_name -> list of sample rows as dictionaries
        """
        sample_data = {}

        for sheet_name, df in sheets.items():
            # Get up to n rows
            sample_rows = df.head(n)
            sample_data[sheet_name] = sample_rows.to_dict(orient='records')

        return sample_data

    @staticmethod
    def validate_file_size(file_path: str, max_size_mb: int = 50) -> None:
        """
        Validate file size.

        Args:
            file_path: Path to file
            max_size_mb: Maximum allowed file size in MB

        Raises:
            ValueError: If file exceeds size limit
        """
        file_size_mb = Path(file_path).stat().st_size / (1024 * 1024)

        if file_size_mb > max_size_mb:
            raise ValueError(
                f"File size ({file_size_mb:.2f} MB) exceeds "
                f"maximum allowed size ({max_size_mb} MB)"
            )

        logger.info(f"File size: {file_size_mb:.2f} MB")

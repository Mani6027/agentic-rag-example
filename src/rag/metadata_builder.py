from typing import List, Dict, Any
import pandas as pd
import numpy as np
from langchain.docstore.document import Document
from src.utils.logger import logger


class MetadataBuilder:
    """Build metadata documents from Excel data for RAG embedding."""

    @staticmethod
    def _analyze_column(series: pd.Series, col_name: str) -> Dict[str, Any]:
        """
        Analyze a single column and extract metadata.

        Args:
            series: Pandas Series (column data)
            col_name: Column name

        Returns:
            Dictionary with column analysis
        """
        analysis = {
            "name": col_name,
            "dtype": str(series.dtype),
            "null_count": int(series.isnull().sum()),
            "null_percentage": float(series.isnull().sum() / len(series) * 100),
        }

        # Type-specific analysis
        if pd.api.types.is_numeric_dtype(series):
            analysis["type_category"] = "numeric"
            non_null = series.dropna()
            if len(non_null) > 0:
                analysis["statistics"] = {
                    "min": float(non_null.min()),
                    "max": float(non_null.max()),
                    "mean": float(non_null.mean()),
                    "median": float(non_null.median()),
                    "std": float(non_null.std()) if len(non_null) > 1 else 0.0
                }
            # Sample values
            analysis["sample_values"] = [
                float(x) for x in non_null.head(5).tolist()
            ]

        elif pd.api.types.is_datetime64_any_dtype(series):
            analysis["type_category"] = "datetime"
            non_null = series.dropna()
            if len(non_null) > 0:
                analysis["statistics"] = {
                    "min": str(non_null.min()),
                    "max": str(non_null.max())
                }
            analysis["sample_values"] = [
                str(x) for x in non_null.head(5).tolist()
            ]

        else:
            # Categorical/Text
            analysis["type_category"] = "categorical"
            non_null = series.dropna()
            unique_count = series.nunique()
            analysis["unique_count"] = int(unique_count)

            if unique_count <= 50:
                # If few unique values, list them all
                analysis["unique_values"] = [
                    str(x) for x in series.unique()[:20]
                ]
            else:
                # Too many unique values, just show samples
                analysis["sample_values"] = [
                    str(x) for x in non_null.head(10).tolist()
                ]

        # Infer semantic meaning
        analysis["inferred_description"] = MetadataBuilder._infer_column_meaning(
            col_name, series
        )

        return analysis

    @staticmethod
    def _infer_column_meaning(col_name: str, series: pd.Series) -> str:
        """
        Infer the semantic meaning of a column based on name and values.

        Args:
            col_name: Column name
            series: Column data

        Returns:
            Inferred description string
        """
        col_lower = col_name.lower()

        # Common patterns
        if 'id' in col_lower:
            return "Identifier or unique key"
        elif 'date' in col_lower or 'time' in col_lower:
            return "Temporal data (date/time)"
        elif 'name' in col_lower:
            return "Name or label"
        elif 'price' in col_lower or 'cost' in col_lower or 'amount' in col_lower:
            return "Monetary value"
        elif 'sales' in col_lower or 'revenue' in col_lower:
            return "Sales or revenue metric"
        elif 'count' in col_lower or 'quantity' in col_lower or 'qty' in col_lower:
            return "Count or quantity metric"
        elif 'percent' in col_lower or 'rate' in col_lower:
            return "Percentage or rate metric"
        elif 'region' in col_lower or 'location' in col_lower or 'city' in col_lower:
            return "Geographic or location data"
        elif 'category' in col_lower or 'type' in col_lower:
            return "Classification or category"
        elif 'status' in col_lower:
            return "Status indicator"
        elif pd.api.types.is_numeric_dtype(series):
            return "Numeric metric or measurement"
        elif pd.api.types.is_datetime64_any_dtype(series):
            return "Date or timestamp"
        else:
            return "Categorical or text data"

    @staticmethod
    def build_metadata(
        sheets: Dict[str, pd.DataFrame],
        dataset_id: str
    ) -> List[Document]:
        """
        Generate metadata documents for embedding from Excel sheets.

        Args:
            sheets: Dictionary of sheet_name -> DataFrame
            dataset_id: Unique dataset identifier

        Returns:
            List of LangChain Document objects for embedding
        """
        documents = []

        for sheet_name, df in sheets.items():
            # 1. Sheet summary document
            summary_content = f"""
Sheet Name: {sheet_name}
Dataset ID: {dataset_id}
Total Rows: {len(df)}
Total Columns: {len(df.columns)}
Column Names: {', '.join(df.columns.tolist())}

This sheet contains {len(df)} records with {len(df.columns)} attributes.
"""
            summary_doc = Document(
                page_content=summary_content.strip(),
                metadata={
                    "type": "sheet_summary",
                    "dataset_id": dataset_id,
                    "sheet_name": sheet_name
                }
            )
            documents.append(summary_doc)

            # 2. Per-column metadata documents
            for col in df.columns:
                col_analysis = MetadataBuilder._analyze_column(df[col], col)

                # Build detailed column description
                col_content = f"""
Column Name: {col}
Sheet: {sheet_name}
Data Type: {col_analysis['dtype']} ({col_analysis['type_category']})
Description: {col_analysis['inferred_description']}
Null Values: {col_analysis['null_count']} ({col_analysis['null_percentage']:.1f}%)
"""

                # Add type-specific details
                if col_analysis['type_category'] == 'numeric':
                    stats = col_analysis.get('statistics', {})
                    col_content += f"""
Statistics:
  - Min: {stats.get('min', 'N/A')}
  - Max: {stats.get('max', 'N/A')}
  - Mean: {stats.get('mean', 'N/A')}
  - Median: {stats.get('median', 'N/A')}
  - Std Dev: {stats.get('std', 'N/A')}
Sample Values: {col_analysis.get('sample_values', [])}
"""
                elif col_analysis['type_category'] == 'categorical':
                    unique_vals = col_analysis.get('unique_values', [])
                    sample_vals = col_analysis.get('sample_values', [])
                    col_content += f"""
Unique Count: {col_analysis.get('unique_count', 'N/A')}
"""
                    if unique_vals:
                        col_content += f"Unique Values: {', '.join(map(str, unique_vals[:10]))}\n"
                    elif sample_vals:
                        col_content += f"Sample Values: {', '.join(map(str, sample_vals[:10]))}\n"

                elif col_analysis['type_category'] == 'datetime':
                    stats = col_analysis.get('statistics', {})
                    col_content += f"""
Date Range:
  - From: {stats.get('min', 'N/A')}
  - To: {stats.get('max', 'N/A')}
"""

                col_doc = Document(
                    page_content=col_content.strip(),
                    metadata={
                        "type": "column_info",
                        "dataset_id": dataset_id,
                        "sheet_name": sheet_name,
                        "column_name": col,
                        "dtype": col_analysis['dtype'],
                        "type_category": col_analysis['type_category']
                    }
                )
                documents.append(col_doc)

            # 3. Relationship insights (for categorical + numeric combinations)
            relationship_insights = MetadataBuilder._detect_relationships(df, sheet_name)
            if relationship_insights:
                rel_doc = Document(
                    page_content=relationship_insights,
                    metadata={
                        "type": "relationships",
                        "dataset_id": dataset_id,
                        "sheet_name": sheet_name
                    }
                )
                documents.append(rel_doc)

        logger.info(
            f"Built {len(documents)} metadata documents for dataset {dataset_id}"
        )
        return documents

    @staticmethod
    def _detect_relationships(df: pd.DataFrame, sheet_name: str) -> str:
        """
        Detect potential relationships between columns.

        Args:
            df: DataFrame
            sheet_name: Sheet name

        Returns:
            String describing relationships
        """
        relationships = []

        # Find categorical columns
        categorical_cols = [
            col for col in df.columns
            if pd.api.types.is_object_dtype(df[col]) or
               pd.api.types.is_categorical_dtype(df[col])
        ]

        # Find numeric columns
        numeric_cols = [
            col for col in df.columns
            if pd.api.types.is_numeric_dtype(df[col])
        ]

        if categorical_cols and numeric_cols:
            relationships.append(
                f"Sheet '{sheet_name}' contains data that can be grouped by "
                f"{', '.join(categorical_cols[:3])} and aggregated on "
                f"{', '.join(numeric_cols[:3])}."
            )

        # Detect potential time series
        datetime_cols = [
            col for col in df.columns
            if pd.api.types.is_datetime64_any_dtype(df[col]) or
               'date' in col.lower() or 'time' in col.lower()
        ]

        if datetime_cols and numeric_cols:
            relationships.append(
                f"Time series analysis is possible using {datetime_cols[0]} "
                f"with metrics like {', '.join(numeric_cols[:3])}."
            )

        return "\n".join(relationships) if relationships else ""

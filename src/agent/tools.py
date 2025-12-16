"""Pandas-based tools for the data analysis agent."""

from typing import List, Optional
import pandas as pd
import json
from langchain.tools import tool
from src.data.storage import data_store
from src.rag.vector_store import vector_store_manager
from src.utils.logger import logger


def create_tools(dataset_id: str, sheet_name: str):
    """
    Create tools with access to a specific dataset.

    Args:
        dataset_id: Dataset identifier
        sheet_name: Sheet name

    Returns:
        List of LangChain tools
    """

    def get_df() -> pd.DataFrame:
        """Helper to get the DataFrame."""
        return data_store.get_dataframe(dataset_id, sheet_name)

    @tool
    def get_data_sample(n: int = 5, filter_condition: Optional[str] = None) -> str:
        """
        Get sample rows from the dataset. Useful for understanding data structure.

        Args:
            n: Number of rows to sample (default 5)
            filter_condition: Optional filter in format 'column==value' or 'column>value'

        Returns:
            JSON string with sample data

        Examples:
            get_data_sample(5) - Get first 5 rows
            get_data_sample(3, "region=='North'") - Get 3 rows where region is North
        """
        try:
            df = get_df()

            if filter_condition:
                df = df.query(filter_condition)

            sample = df.head(n)
            result = {
                "sample_count": len(sample),
                "total_rows": len(df),
                "columns": list(df.columns),
                "sample_data": sample.to_dict(orient='records')
            }

            logger.info(f"Retrieved {len(sample)} sample rows")
            return json.dumps(result, indent=2, default=str)

        except Exception as e:
            logger.error(f"Error in get_data_sample: {str(e)}")
            return json.dumps({"error": str(e)})

    @tool
    def query_data(filter_condition: str) -> str:
        """
        Filter and query data based on conditions.

        Args:
            filter_condition: Pandas query string (e.g., "sales > 1000", "region == 'North'")

        Returns:
            JSON string with filtered results summary

        Examples:
            query_data("sales > 1000")
            query_data("region == 'North' and product.str.contains('Widget')")
        """
        try:
            df = get_df()
            filtered_df = df.query(filter_condition)

            result = {
                "filter_condition": filter_condition,
                "matched_rows": len(filtered_df),
                "total_rows": len(df),
                "percentage": round(len(filtered_df) / len(df) * 100, 2) if len(df) > 0 else 0,
                "columns": list(filtered_df.columns),
                "sample_results": filtered_df.head(10).to_dict(orient='records')
            }

            logger.info(
                f"Query '{filter_condition}' matched {len(filtered_df)} rows"
            )
            return json.dumps(result, indent=2, default=str)

        except Exception as e:
            logger.error(f"Error in query_data: {str(e)}")
            return json.dumps({
                "error": str(e),
                "suggestion": "Check column names and syntax. Use exact column names."
            })

    @tool
    def aggregate_data(
        column: str,
        operation: str,
        filter_condition: Optional[str] = None
    ) -> str:
        """
        Perform aggregation operations on a column.

        Args:
            column: Column name to aggregate
            operation: One of 'sum', 'mean', 'median', 'count', 'min', 'max', 'std'
            filter_condition: Optional filter condition

        Returns:
            JSON string with aggregation result

        Examples:
            aggregate_data("sales", "sum")
            aggregate_data("price", "mean", "region == 'North'")
        """
        try:
            df = get_df()

            if filter_condition:
                df = df.query(filter_condition)

            if column not in df.columns:
                return json.dumps({
                    "error": f"Column '{column}' not found",
                    "available_columns": list(df.columns)
                })

            operations_map = {
                'sum': df[column].sum,
                'mean': df[column].mean,
                'median': df[column].median,
                'count': df[column].count,
                'min': df[column].min,
                'max': df[column].max,
                'std': df[column].std
            }

            if operation not in operations_map:
                return json.dumps({
                    "error": f"Invalid operation '{operation}'",
                    "valid_operations": list(operations_map.keys())
                })

            result_value = operations_map[operation]()

            result = {
                "column": column,
                "operation": operation,
                "result": float(result_value) if pd.notna(result_value) else None,
                "rows_analyzed": len(df),
                "filter_applied": filter_condition or "None"
            }

            logger.info(
                f"Aggregation {operation}({column}) = {result['result']}"
            )
            return json.dumps(result, indent=2, default=str)

        except Exception as e:
            logger.error(f"Error in aggregate_data: {str(e)}")
            return json.dumps({"error": str(e)})

    @tool
    def group_by_analysis(
        group_columns: str,
        agg_column: str,
        agg_operation: str
    ) -> str:
        """
        Group data by columns and perform aggregation.

        Args:
            group_columns: Comma-separated column names to group by
            agg_column: Column to aggregate
            agg_operation: One of 'sum', 'mean', 'median', 'count', 'min', 'max'

        Returns:
            JSON string with grouped results

        Examples:
            group_by_analysis("region", "sales", "sum")
            group_by_analysis("region,product", "sales", "mean")
        """
        try:
            df = get_df()

            # Parse group columns
            group_cols = [col.strip() for col in group_columns.split(',')]

            # Validate columns
            missing_cols = [col for col in group_cols if col not in df.columns]
            if missing_cols:
                return json.dumps({
                    "error": f"Columns not found: {missing_cols}",
                    "available_columns": list(df.columns)
                })

            if agg_column not in df.columns:
                return json.dumps({
                    "error": f"Aggregation column '{agg_column}' not found",
                    "available_columns": list(df.columns)
                })

            # Perform groupby
            operations_map = {
                'sum': 'sum',
                'mean': 'mean',
                'median': 'median',
                'count': 'count',
                'min': 'min',
                'max': 'max'
            }

            if agg_operation not in operations_map:
                return json.dumps({
                    "error": f"Invalid operation '{agg_operation}'",
                    "valid_operations": list(operations_map.keys())
                })

            grouped = df.groupby(group_cols)[agg_column].agg(
                operations_map[agg_operation]
            ).reset_index()

            # Sort by aggregated value descending
            grouped = grouped.sort_values(by=agg_column, ascending=False)

            result = {
                "group_by": group_cols,
                "aggregated_column": agg_column,
                "operation": agg_operation,
                "num_groups": len(grouped),
                "results": grouped.to_dict(orient='records')
            }

            logger.info(
                f"GroupBy {group_cols} with {agg_operation}({agg_column}) "
                f"produced {len(grouped)} groups"
            )
            return json.dumps(result, indent=2, default=str)

        except Exception as e:
            logger.error(f"Error in group_by_analysis: {str(e)}")
            return json.dumps({"error": str(e)})

    @tool
    def get_column_info(column_name: Optional[str] = None) -> str:
        """
        Get metadata information about columns from RAG.

        Args:
            column_name: Optional specific column name (if None, returns info about all columns)

        Returns:
            String with column metadata and descriptions

        Examples:
            get_column_info() - Get info about all columns
            get_column_info("sales") - Get info about sales column
        """
        try:
            docs = vector_store_manager.get_column_info(
                dataset_id,
                column_name,
                k=5 if column_name else 10
            )

            if not docs:
                return "No column information found in metadata."

            info_parts = []
            for doc in docs:
                info_parts.append(doc.page_content)

            result = "\n\n---\n\n".join(info_parts)
            logger.info(f"Retrieved column info for: {column_name or 'all columns'}")
            return result

        except Exception as e:
            logger.error(f"Error in get_column_info: {str(e)}")
            return f"Error retrieving column info: {str(e)}"

    @tool
    def query_schema(question: str) -> str:
        """
        Ask questions about the dataset structure and meaning using RAG.

        Args:
            question: Natural language question about the schema

        Returns:
            String with relevant metadata from RAG

        Examples:
            query_schema("What columns contain sales data?")
            query_schema("What does the region column represent?")
        """
        try:
            docs = vector_store_manager.query_metadata(
                dataset_id,
                question,
                k=5
            )

            if not docs:
                return "No relevant schema information found."

            info_parts = []
            for doc in docs:
                info_parts.append(doc.page_content)

            result = "\n\n---\n\n".join(info_parts)
            logger.info(f"Schema query: '{question}'")
            return result

        except Exception as e:
            logger.error(f"Error in query_schema: {str(e)}")
            return f"Error querying schema: {str(e)}"

    @tool
    def calculate_correlation(column1: str, column2: str) -> str:
        """
        Calculate correlation between two numeric columns.

        Args:
            column1: First column name
            column2: Second column name

        Returns:
            JSON string with correlation coefficient and interpretation

        Examples:
            calculate_correlation("price", "sales")
        """
        try:
            df = get_df()

            if column1 not in df.columns:
                return json.dumps({
                    "error": f"Column '{column1}' not found",
                    "available_columns": list(df.columns)
                })

            if column2 not in df.columns:
                return json.dumps({
                    "error": f"Column '{column2}' not found",
                    "available_columns": list(df.columns)
                })

            # Check if columns are numeric
            if not pd.api.types.is_numeric_dtype(df[column1]):
                return json.dumps({
                    "error": f"Column '{column1}' is not numeric",
                    "dtype": str(df[column1].dtype)
                })

            if not pd.api.types.is_numeric_dtype(df[column2]):
                return json.dumps({
                    "error": f"Column '{column2}' is not numeric",
                    "dtype": str(df[column2].dtype)
                })

            # Calculate correlation
            corr = df[[column1, column2]].corr().iloc[0, 1]

            # Interpret correlation
            if abs(corr) < 0.3:
                interpretation = "weak"
            elif abs(corr) < 0.7:
                interpretation = "moderate"
            else:
                interpretation = "strong"

            direction = "positive" if corr > 0 else "negative"

            result = {
                "column1": column1,
                "column2": column2,
                "correlation_coefficient": round(float(corr), 4),
                "interpretation": f"{interpretation} {direction} correlation",
                "rows_analyzed": len(df.dropna(subset=[column1, column2]))
            }

            logger.info(
                f"Correlation between {column1} and {column2}: {corr:.4f}"
            )
            return json.dumps(result, indent=2)

        except Exception as e:
            logger.error(f"Error in calculate_correlation: {str(e)}")
            return json.dumps({"error": str(e)})

    @tool
    def analyze_trend(
        date_column: str,
        value_column: str,
        groupby_column: Optional[str] = None
    ) -> str:
        """
        Analyze trends over time.

        Args:
            date_column: Column containing dates/times
            value_column: Column with values to analyze
            groupby_column: Optional column to group by (e.g., region, product)

        Returns:
            JSON string with trend analysis

        Examples:
            analyze_trend("date", "sales")
            analyze_trend("date", "sales", "region")
        """
        try:
            df = get_df()

            # Validate columns
            if date_column not in df.columns:
                return json.dumps({
                    "error": f"Date column '{date_column}' not found",
                    "available_columns": list(df.columns)
                })

            if value_column not in df.columns:
                return json.dumps({
                    "error": f"Value column '{value_column}' not found",
                    "available_columns": list(df.columns)
                })

            # Convert date column to datetime if not already
            df_copy = df.copy()
            if not pd.api.types.is_datetime64_any_dtype(df_copy[date_column]):
                df_copy[date_column] = pd.to_datetime(df_copy[date_column])

            # Sort by date
            df_copy = df_copy.sort_values(by=date_column)

            if groupby_column:
                # Trend by group
                trends = {}
                for group_name, group_df in df_copy.groupby(groupby_column):
                    group_df = group_df.sort_values(by=date_column)
                    first_val = group_df[value_column].iloc[0]
                    last_val = group_df[value_column].iloc[-1]
                    change = last_val - first_val
                    pct_change = (change / first_val * 100) if first_val != 0 else 0

                    trends[str(group_name)] = {
                        "first_value": float(first_val),
                        "last_value": float(last_val),
                        "change": float(change),
                        "percent_change": round(float(pct_change), 2)
                    }

                result = {
                    "date_column": date_column,
                    "value_column": value_column,
                    "grouped_by": groupby_column,
                    "trends": trends
                }
            else:
                # Overall trend
                first_val = df_copy[value_column].iloc[0]
                last_val = df_copy[value_column].iloc[-1]
                change = last_val - first_val
                pct_change = (change / first_val * 100) if first_val != 0 else 0

                result = {
                    "date_column": date_column,
                    "value_column": value_column,
                    "first_value": float(first_val),
                    "last_value": float(last_val),
                    "change": float(change),
                    "percent_change": round(float(pct_change), 2),
                    "trend_direction": "increasing" if change > 0 else "decreasing"
                }

            logger.info(f"Trend analysis for {value_column} over {date_column}")
            return json.dumps(result, indent=2, default=str)

        except Exception as e:
            logger.error(f"Error in analyze_trend: {str(e)}")
            return json.dumps({"error": str(e)})

    return [
        get_data_sample,
        query_data,
        aggregate_data,
        group_by_analysis,
        get_column_info,
        query_schema,
        calculate_correlation,
        analyze_trend
    ]

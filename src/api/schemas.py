"""Pydantic models for API request/response validation."""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field, validator


class UploadResponse(BaseModel):
    """Response model for file upload."""
    dataset_id: str = Field(..., description="Unique dataset identifier")
    filename: str = Field(..., description="Original filename")
    sheets: List[str] = Field(..., description="List of sheet names")
    columns: Dict[str, List[str]] = Field(..., description="Columns per sheet")
    rows_count: Dict[str, int] = Field(..., description="Row count per sheet")
    message: str = Field(..., description="Success message")


class QueryRequest(BaseModel):
    """Request model for querying a dataset."""
    dataset_id: str = Field(..., min_length=1, description="Dataset identifier")
    query: str = Field(
        ...,
        min_length=3,
        max_length=1000,
        description="Natural language query about the data"
    )
    sheet_name: Optional[str] = Field(
        None,
        description="Optional sheet name (uses first sheet if not specified)"
    )

    @validator('query')
    def validate_query(cls, v):
        """Validate query is not empty or just whitespace."""
        if not v.strip():
            raise ValueError("Query cannot be empty")
        return v.strip()


class ExecutionStep(BaseModel):
    """Model for a single execution step."""
    step: int = Field(..., description="Step number")
    action: str = Field(..., description="Tool/action used")
    action_input: Any = Field(..., description="Input to the action")
    observation: str = Field(..., description="Result of the action")


class QueryResponse(BaseModel):
    """Response model for query execution."""
    query: str = Field(..., description="Original query")
    answer: str = Field(..., description="Answer to the query")
    execution_steps: List[ExecutionStep] = Field(
        default=[],
        description="Steps taken to answer the query"
    )
    rag_context_used: Optional[str] = Field(
        None,
        description="RAG context snippet used for understanding"
    )
    success: bool = Field(..., description="Whether query was successful")
    error: Optional[str] = Field(None, description="Error message if failed")


class DatasetInfo(BaseModel):
    """Model for dataset information."""
    dataset_id: str = Field(..., description="Dataset identifier")
    filename: str = Field(..., description="Original filename")
    uploaded_at: str = Field(..., description="Upload timestamp (ISO format)")
    sheets: List[str] = Field(..., description="List of sheet names")
    columns: Dict[str, List[str]] = Field(..., description="Columns per sheet")
    rows_count: Dict[str, int] = Field(..., description="Row count per sheet")
    sample_data: Optional[Dict[str, List[Dict]]] = Field(
        None,
        description="Sample rows from each sheet"
    )


class DatasetListItem(BaseModel):
    """Model for dataset list item."""
    dataset_id: str = Field(..., description="Dataset identifier")
    filename: str = Field(..., description="Original filename")
    uploaded_at: str = Field(..., description="Upload timestamp (ISO format)")
    sheets: List[str] = Field(..., description="List of sheet names")


class DatasetListResponse(BaseModel):
    """Response model for listing datasets."""
    datasets: List[DatasetListItem] = Field(..., description="List of datasets")
    total: int = Field(..., description="Total number of datasets")


class DeleteResponse(BaseModel):
    """Response model for dataset deletion."""
    message: str = Field(..., description="Success message")
    dataset_id: str = Field(..., description="Deleted dataset identifier")


class ErrorResponse(BaseModel):
    """Response model for errors."""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str = Field(..., description="Health status")
    version: str = Field(..., description="API version")
    model: str = Field(..., description="LLM model being used")

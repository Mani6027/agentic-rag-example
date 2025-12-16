"""API routes for the Agentic RAG Excel Analyzer."""

import uuid
import os
from pathlib import Path
from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from fastapi.responses import JSONResponse

from src.api.schemas import (
    UploadResponse,
    QueryRequest,
    QueryResponse,
    DatasetInfo,
    DatasetListResponse,
    DatasetListItem,
    DeleteResponse,
    ErrorResponse,
    HealthResponse,
    ExecutionStep
)
from src.data.storage import data_store
from src.data.excel_handler import ExcelHandler
from src.rag.metadata_builder import MetadataBuilder
from src.rag.vector_store import vector_store_manager
from src.agent.executor import data_analysis_agent
from src.config.settings import settings
from src.utils.logger import logger


router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version=settings.api_version,
        model=settings.model_name
    )


@router.post("/upload", response_model=UploadResponse)
async def upload_excel(file: UploadFile = File(...)):
    """
    Upload an Excel file and process it.

    Args:
        file: Excel file (.xlsx or .xls)

    Returns:
        UploadResponse with dataset information
    """
    try:
        # Validate file extension
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file format. Only .xlsx and .xls files are supported."
            )

        logger.info(f"Uploading file: {file.filename}")

        # Generate unique dataset ID
        dataset_id = str(uuid.uuid4())

        # Create upload directory if it doesn't exist
        upload_dir = Path(settings.upload_dir)
        upload_dir.mkdir(parents=True, exist_ok=True)

        # Save file
        file_path = upload_dir / f"{dataset_id}_{file.filename}"
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        logger.info(f"File saved to: {file_path}")

        # Validate file size (50 MB limit)
        ExcelHandler.validate_file_size(str(file_path), max_size_mb=50)

        # Process Excel file
        sheets = ExcelHandler.process_file(str(file_path))

        # Extract metadata
        metadata = ExcelHandler.get_metadata(sheets, file.filename)

        # Store in data store
        data_store.add_dataset(dataset_id, sheets, metadata)

        # Build metadata for RAG
        rag_documents = MetadataBuilder.build_metadata(sheets, dataset_id)

        # Create vector store
        vector_store_manager.create_store(dataset_id, rag_documents)

        logger.info(
            f"Dataset {dataset_id} processed successfully with "
            f"{len(rag_documents)} metadata documents"
        )

        # Clean up uploaded file (optional - keep for debugging)
        # os.remove(file_path)

        return UploadResponse(
            dataset_id=dataset_id,
            filename=file.filename,
            sheets=metadata["sheets"],
            columns=metadata["columns"],
            rows_count=metadata["rows_count"],
            message="File uploaded and processed successfully"
        )

    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process file: {str(e)}"
        )


@router.post("/query", response_model=QueryResponse)
async def query_dataset(request: QueryRequest):
    """
    Query a dataset with natural language.

    Args:
        request: QueryRequest with dataset_id, query, and optional sheet_name

    Returns:
        QueryResponse with answer and execution details
    """
    try:
        logger.info(
            f"Query request for dataset {request.dataset_id}: '{request.query}'"
        )

        # Check if dataset exists
        if not data_store.dataset_exists(request.dataset_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Dataset {request.dataset_id} not found"
            )

        # Get sheet name
        if request.sheet_name:
            sheet_names = data_store.get_sheet_names(request.dataset_id)
            if request.sheet_name not in sheet_names:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Sheet '{request.sheet_name}' not found. "
                           f"Available sheets: {sheet_names}"
                )
            sheet_name = request.sheet_name
        else:
            # Use first sheet
            sheet_names = data_store.get_sheet_names(request.dataset_id)
            sheet_name = sheet_names[0]
            logger.info(f"Using default sheet: {sheet_name}")

        # Execute query using agent
        result = data_analysis_agent.query(
            dataset_id=request.dataset_id,
            sheet_name=sheet_name,
            user_query=request.query
        )

        # Convert execution steps to schema
        execution_steps = [
            ExecutionStep(**step) for step in result.get("execution_steps", [])
        ]

        return QueryResponse(
            query=result["query"],
            answer=result["answer"],
            execution_steps=execution_steps,
            rag_context_used=result.get("rag_context_used"),
            success=result["success"],
            error=result.get("error")
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process query: {str(e)}"
        )


@router.get("/dataset/{dataset_id}", response_model=DatasetInfo)
async def get_dataset_info(dataset_id: str, include_sample: bool = True):
    """
    Get information about a specific dataset.

    Args:
        dataset_id: Dataset identifier
        include_sample: Whether to include sample data

    Returns:
        DatasetInfo with dataset details
    """
    try:
        if not data_store.dataset_exists(dataset_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Dataset {dataset_id} not found"
            )

        metadata = data_store.get_metadata(dataset_id)

        response_data = {
            "dataset_id": dataset_id,
            **metadata
        }

        # Add sample data if requested
        if include_sample:
            sheets = data_store.get_all_sheets(dataset_id)
            sample_data = ExcelHandler.get_sample_data(sheets, n=5)
            response_data["sample_data"] = sample_data

        return DatasetInfo(**response_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting dataset info: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get dataset info: {str(e)}"
        )


@router.get("/datasets", response_model=DatasetListResponse)
async def list_datasets():
    """
    List all uploaded datasets.

    Returns:
        DatasetListResponse with list of datasets
    """
    try:
        datasets = data_store.list_datasets()

        dataset_items = [
            DatasetListItem(
                dataset_id=ds["dataset_id"],
                filename=ds["filename"],
                uploaded_at=ds["uploaded_at"],
                sheets=ds["sheets"]
            )
            for ds in datasets
        ]

        return DatasetListResponse(
            datasets=dataset_items,
            total=len(dataset_items)
        )

    except Exception as e:
        logger.error(f"Error listing datasets: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list datasets: {str(e)}"
        )


@router.delete("/dataset/{dataset_id}", response_model=DeleteResponse)
async def delete_dataset(dataset_id: str):
    """
    Delete a dataset.

    Args:
        dataset_id: Dataset identifier

    Returns:
        DeleteResponse with success message
    """
    try:
        if not data_store.dataset_exists(dataset_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Dataset {dataset_id} not found"
            )

        # Delete from data store
        data_store.delete_dataset(dataset_id)

        # Delete vector store
        if vector_store_manager.store_exists(dataset_id):
            vector_store_manager.delete_store(dataset_id)

        # Delete uploaded file (optional)
        upload_dir = Path(settings.upload_dir)
        for file_path in upload_dir.glob(f"{dataset_id}_*"):
            try:
                os.remove(file_path)
                logger.info(f"Deleted file: {file_path}")
            except Exception as e:
                logger.warning(f"Failed to delete file {file_path}: {str(e)}")

        logger.info(f"Dataset {dataset_id} deleted successfully")

        return DeleteResponse(
            message="Dataset deleted successfully",
            dataset_id=dataset_id
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting dataset: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete dataset: {str(e)}"
        )

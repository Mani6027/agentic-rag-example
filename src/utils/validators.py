"""Input validation utilities."""

import re
from typing import Optional


def is_valid_dataset_id(dataset_id: str) -> bool:
    """
    Validate dataset ID format (UUID).

    Args:
        dataset_id: Dataset identifier

    Returns:
        True if valid UUID format, False otherwise
    """
    uuid_pattern = re.compile(
        r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
        re.IGNORECASE
    )
    return bool(uuid_pattern.match(dataset_id))


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent directory traversal attacks.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename
    """
    # Remove any directory path components
    filename = filename.split('/')[-1].split('\\')[-1]

    # Remove any potentially dangerous characters
    filename = re.sub(r'[^\w\s.-]', '', filename)

    return filename


def is_valid_column_name(column_name: str) -> bool:
    """
    Validate column name (alphanumeric, underscore only).

    Args:
        column_name: Column name to validate

    Returns:
        True if valid, False otherwise
    """
    pattern = re.compile(r'^[a-z0-9_]+$', re.IGNORECASE)
    return bool(pattern.match(column_name))


def validate_query_length(query: str, max_length: int = 1000) -> Optional[str]:
    """
    Validate query length.

    Args:
        query: Query string
        max_length: Maximum allowed length

    Returns:
        Error message if invalid, None if valid
    """
    if not query or not query.strip():
        return "Query cannot be empty"

    if len(query) > max_length:
        return f"Query too long (max {max_length} characters)"

    return None

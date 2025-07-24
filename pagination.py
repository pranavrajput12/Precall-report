"""
Pagination utilities for API endpoints

This module provides standardized pagination functionality for API endpoints
that return large datasets. It includes a Paginator class that handles
pagination logic and a PaginatedResponse class for consistent response formatting.
"""

from typing import List, Dict, Any, TypeVar, Generic, Optional, Callable
from math import ceil
from fastapi import Query, HTTPException, status

T = TypeVar('T')

class PaginatedResponse(Generic[T]):
    """
    Standardized paginated response format
    
    Attributes:
        items: The paginated items
        total: Total number of items
        page: Current page number
        page_size: Number of items per page
        total_pages: Total number of pages
        has_next: Whether there is a next page
        has_prev: Whether there is a previous page
    """
    
    def __init__(
        self,
        items: List[T],
        total: int,
        page: int,
        page_size: int
    ):
        """
        Initialize a paginated response
        
        Args:
            items: The paginated items
            total: Total number of items
            page: Current page number
            page_size: Number of items per page
        """
        self.items = items
        self.total = total
        self.page = page
        self.page_size = page_size
        self.total_pages = ceil(total / page_size) if page_size > 0 else 0
        self.has_next = page < self.total_pages
        self.has_prev = page > 1
    
    def dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON response"""
        return {
            "items": self.items,
            "pagination": {
                "total": self.total,
                "page": self.page,
                "page_size": self.page_size,
                "total_pages": self.total_pages,
                "has_next": self.has_next,
                "has_prev": self.has_prev
            }
        }


class Paginator:
    """
    Paginator utility for handling pagination logic
    
    This class provides methods for paginating lists of items and
    creating standardized paginated responses.
    """
    
    @staticmethod
    def paginate_list(
        items: List[T],
        page: int = 1,
        page_size: int = 10
    ) -> PaginatedResponse[T]:
        """
        Paginate a list of items
        
        Args:
            items: The list of items to paginate
            page: The page number (1-based)
            page_size: The number of items per page
            
        Returns:
            PaginatedResponse: A paginated response object
            
        Raises:
            HTTPException: If page or page_size is invalid
        """
        # Validate pagination parameters
        if page < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Page number must be greater than 0"
            )
        
        if page_size < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Page size must be greater than 0"
            )
        
        # Calculate pagination
        total = len(items)
        start_idx = (page - 1) * page_size
        end_idx = min(start_idx + page_size, total)
        
        # Handle out-of-range page
        if start_idx >= total and total > 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Page {page} out of range, total pages: {ceil(total / page_size)}"
            )
        
        # Get paginated items
        paginated_items = items[start_idx:end_idx]
        
        return PaginatedResponse(
            items=paginated_items,
            total=total,
            page=page,
            page_size=page_size
        )
    
    @staticmethod
    def paginate_query(
        query_func: Callable[..., List[T]],
        page: int = 1,
        page_size: int = 10,
        **query_params
    ) -> PaginatedResponse[T]:
        """
        Paginate a query function that returns a list of items
        
        Args:
            query_func: A function that returns a list of items
            page: The page number (1-based)
            page_size: The number of items per page
            **query_params: Additional parameters to pass to the query function
            
        Returns:
            PaginatedResponse: A paginated response object
        """
        # Get all items from the query function
        all_items = query_func(**query_params)
        
        # Use paginate_list to handle pagination
        return Paginator.paginate_list(all_items, page, page_size)


# Common pagination parameters for FastAPI endpoints
def pagination_params(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page")
) -> Dict[str, int]:
    """
    Common pagination parameters for FastAPI endpoints
    
    Args:
        page: The page number (1-based)
        page_size: The number of items per page
        
    Returns:
        Dict[str, int]: A dictionary with pagination parameters
    """
    return {"page": page, "page_size": page_size}
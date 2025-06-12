
# backend/lib/utils.py
from datetime import datetime, timedelta, timezone
from flask import url_for # Used to generate URLs for pagination links

def _format_datetime(dt_str):
    """
    Formats a datetime string to ISO 8601 with 'Z' for UTC.
    Handles both with and without microseconds.
    """
    if not dt_str:
        return None
    try:
        # Try parsing with microseconds first
        dt_obj = datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S.%f')
    except ValueError:
        # Fallback to parsing without microseconds
        dt_obj = datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')
    
    # Ensure the datetime object is timezone-aware (UTC) before formatting
    return dt_obj.replace(tzinfo=timezone.utc).isoformat().replace('+00:00', 'Z')


def _get_pagination_metadata(endpoint_name, total_items, current_page, per_page, **kwargs):
    """
    Helper to generate pagination metadata, including next/prev page URLs.
    Args:
        endpoint_name (str): The name of the Flask endpoint for URL generation.
        total_items (int): Total number of items available.
        current_page (int): The current page number (1-indexed).
        per_page (int): Number of items per page.
        **kwargs: Additional keyword arguments to pass to url_for (e.g., group_id).
    Returns:
        dict: A dictionary containing pagination details.
    """
    total_pages = (total_items + per_page - 1) // per_page # Calculate total pages, rounding up
    next_page = None
    prev_page = None

    # Generate URL for the next page if it exists
    if current_page < total_pages:
        next_page = url_for(endpoint_name, page=current_page + 1, limit=per_page, _external=True, **kwargs)
    
    # Generate URL for the previous page if it exists
    if current_page > 1:
        prev_page = url_for(endpoint_name, page=current_page - 1, limit=per_page, _external=True, **kwargs)

    return {
        "total_items": total_items,
        "total_pages": total_pages,
        "current_page": current_page,
        "items_per_page": per_page,
        "next_page": next_page,
        "prev_page": prev_page
    }

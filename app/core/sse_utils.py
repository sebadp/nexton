"""
Server-Sent Events (SSE) utilities.

Provides helpers for formatting and streaming SSE events.
"""

import json
from typing import Any


def format_sse_event(event: str, data: dict[str, Any]) -> str:
    """
    Format data as an SSE event.

    Args:
        event: Event type name
        data: Dictionary to serialize as JSON

    Returns:
        Formatted SSE event string
    """
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def format_sse_data(data: dict[str, Any]) -> str:
    """
    Format data as SSE message (without event type).

    Args:
        data: Dictionary to serialize as JSON

    Returns:
        Formatted SSE data string
    """
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

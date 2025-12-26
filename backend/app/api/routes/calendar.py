"""
Calendar API endpoints
Implements identical functionality to Next.js calendar endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Dict, Any, List, Optional
from datetime import datetime, date

from app.api.dependencies import get_current_user
from app.core.database import query
from app.models.schemas import CalendarEventCreate, CalendarEventResponse

router = APIRouter()

@router.get("/calendar")
async def get_calendar_events(
    start: Optional[str] = Query(None, description="Start date filter (YYYY-MM-DD)"),
    end: Optional[str] = Query(None, description="End date filter (YYYY-MM-DD)"),
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Get calendar events with same date range filtering as Next.js
    Equivalent to: SELECT * FROM calendar_events WHERE user_id = $1 AND DATE(start_time) >= $2 [AND DATE(start_time) <= $3] ORDER BY start_time ASC
    """
    try:
        # Use current date as default start if not provided (same as Next.js)
        start_date = start or datetime.now().date().isoformat()
        
        # Build query with same logic as Next.js
        calendar_query = 'SELECT * FROM calendar_events WHERE user_id = $1 AND DATE(start_time) >= $2'
        calendar_params = [user['id'], start_date]
        
        if end:
            calendar_query += ' AND DATE(start_time) <= $3'
            calendar_params.append(end)
        
        calendar_query += ' ORDER BY start_time ASC'
        
        calendar_result = await query(calendar_query, calendar_params)
        return {"events": calendar_result}
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(error)
        )

@router.post("/calendar")
async def create_calendar_event(
    event_data: CalendarEventCreate,
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Dict[str, Any]]:
    """
    Create calendar event with identical creation logic as Next.js
    Equivalent to: INSERT INTO calendar_events (user_id, title, description, start_time, end_time, event_type, is_blocking) VALUES (...) RETURNING *
    """
    try:
        event_result = await query(
            """INSERT INTO calendar_events (user_id, title, description, start_time, end_time, event_type, is_blocking)
               VALUES ($1, $2, $3, $4, $5, $6, $7) RETURNING *""",
            [
                user['id'],
                event_data.title,
                event_data.description,
                event_data.start_time,
                event_data.end_time,
                event_data.event_type,  # defaults to 'internal' in Pydantic model
                event_data.is_blocking   # defaults to True in Pydantic model
            ]
        )
        return {"event": event_result[0]}
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(error)
        )

@router.delete("/calendar/{event_id}")
async def delete_calendar_event(
    event_id: str,
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, str]:
    """
    Delete calendar event with identical deletion logic as Next.js
    Equivalent to: DELETE FROM calendar_events WHERE id = $1 AND user_id = $2
    """
    try:
        await query(
            'DELETE FROM calendar_events WHERE id = $1 AND user_id = $2',
            [event_id, user['id']]
        )
        return {"message": "Deleted successfully"}
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(error)
        )
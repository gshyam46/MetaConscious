"""
Relationships API endpoints
Implements identical functionality to Next.js relationships endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, List

from app.api.dependencies import get_current_user
from app.core.database import query
from app.models.schemas import RelationshipCreate, RelationshipUpdate, RelationshipResponse

router = APIRouter()

@router.get("/relationships")
async def get_relationships(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, List[Dict[str, Any]]]:
    """
    Get user relationships with same SQL query and response format as Next.js
    Equivalent to: SELECT * FROM relationships WHERE user_id = $1 ORDER BY priority DESC
    """
    try:
        relationships_result = await query(
            'SELECT * FROM relationships WHERE user_id = $1 ORDER BY priority DESC',
            [user['id']]
        )
        return {"relationships": relationships_result}
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(error)
        )

@router.post("/relationships")
async def create_relationship(
    relationship_data: RelationshipCreate, 
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Dict[str, Any]]:
    """
    Create new relationship with identical validation and creation logic as Next.js
    Equivalent to: INSERT INTO relationships (user_id, name, relationship_type, priority, time_budget_hours, notes) VALUES (...) RETURNING *
    """
    try:
        relationship_result = await query(
            """INSERT INTO relationships (user_id, name, relationship_type, priority, time_budget_hours, notes)
               VALUES ($1, $2, $3, $4, $5, $6) RETURNING *""",
            [
                user['id'], 
                relationship_data.name, 
                relationship_data.relationship_type, 
                relationship_data.priority, 
                relationship_data.time_budget_hours, 
                relationship_data.notes
            ]
        )
        return {"relationship": relationship_result[0]}
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(error)
        )

@router.delete("/relationships/{relationship_id}")
async def delete_relationship(
    relationship_id: str, 
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, str]:
    """
    Delete relationship with identical deletion logic as Next.js
    Equivalent to: DELETE FROM relationships WHERE id = $1 AND user_id = $2
    """
    try:
        await query(
            'DELETE FROM relationships WHERE id = $1 AND user_id = $2',
            [relationship_id, user['id']]
        )
        return {"message": "Deleted successfully"}
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(error)
        )
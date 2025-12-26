"""
Goals API endpoints
Implements identical functionality to Next.js goals endpoints
"""
from fastapi import APIRouter, Depends
from typing import Dict, Any, List

from app.api.dependencies import get_current_user
from app.core.database import query
from app.core.exceptions import NotFoundError
from app.models.schemas import GoalCreate, GoalUpdate, GoalResponse

router = APIRouter()

@router.get("/goals")
async def get_goals(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, List[Dict[str, Any]]]:
    """
    Get user goals with same SQL query and response format as Next.js
    Equivalent to: SELECT * FROM goals WHERE user_id = $1 ORDER BY priority DESC, created_at DESC
    """
    # Database errors handled by exception handlers
    goals_result = await query(
        'SELECT * FROM goals WHERE user_id = $1 ORDER BY priority DESC, created_at DESC',
        [user['id']]
    )
    return {"goals": goals_result}

@router.post("/goals")
async def create_goal(
    goal_data: GoalCreate, 
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Dict[str, Any]]:
    """
    Create new goal with identical validation and creation logic as Next.js
    Equivalent to: INSERT INTO goals (user_id, title, description, priority, priority_reasoning, target_date) VALUES (...) RETURNING *
    """
    from datetime import datetime
    
    # Convert string date to date object if provided
    target_date = None
    if goal_data.target_date:
        try:
            target_date = datetime.strptime(goal_data.target_date, '%Y-%m-%d').date()
        except ValueError:
            target_date = None
    
    # Database errors handled by exception handlers
    goal_result = await query(
        """INSERT INTO goals (user_id, title, description, priority, priority_reasoning, target_date)
           VALUES ($1, $2, $3, $4, $5, $6) RETURNING *""",
        [
            user['id'], 
            goal_data.title, 
            goal_data.description, 
            goal_data.priority, 
            goal_data.priority_reasoning, 
            target_date
        ]
    )
    return {"goal": goal_result[0]}

@router.put("/goals/{goal_id}")
async def update_goal(
    goal_id: str, 
    goal_data: GoalUpdate, 
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Dict[str, Any]]:
    """
    Update goal with same update logic as Next.js
    Equivalent to: UPDATE goals SET ... WHERE id = $7 AND user_id = $8 RETURNING *
    """
    from datetime import datetime
    
    # Convert string date to date object if provided
    target_date = goal_data.target_date
    if target_date:
        try:
            target_date = datetime.strptime(goal_data.target_date, '%Y-%m-%d').date()
        except ValueError:
            target_date = None
    
    try:
        goal_result = await query(
            """UPDATE goals SET 
               title = COALESCE($1, title),
               description = COALESCE($2, description),
               priority = COALESCE($3, priority),
               priority_reasoning = COALESCE($4, priority_reasoning),
               status = COALESCE($5, status),
               target_date = COALESCE($6, target_date),
               updated_at = CURRENT_TIMESTAMP
               WHERE id = $7 AND user_id = $8
               RETURNING *""",
            [
                goal_data.title, 
                goal_data.description, 
                goal_data.priority, 
                goal_data.priority_reasoning, 
                goal_data.status, 
                target_date, 
                goal_id, 
                user['id']
            ]
        )
        
        if not goal_result:
            raise NotFoundError("Goal not found")
        
        return {"goal": goal_result[0]}
    except NotFoundError:
        raise

@router.delete("/goals/{goal_id}")
async def delete_goal(
    goal_id: str, 
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, str]:
    """
    Delete goal with identical deletion logic as Next.js
    Equivalent to: DELETE FROM goals WHERE id = $1 AND user_id = $2
    """
    # Database errors handled by exception handlers
    await query(
        'DELETE FROM goals WHERE id = $1 AND user_id = $2',
        [goal_id, user['id']]
    )
    return {"message": "Deleted successfully"}
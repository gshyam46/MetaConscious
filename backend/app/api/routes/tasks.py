"""
Tasks API endpoints
Implements identical functionality to Next.js tasks endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Dict, Any, List, Optional

from app.api.dependencies import get_current_user
from app.core.database import query
from app.models.schemas import TaskCreate, TaskUpdate, TaskResponse

router = APIRouter()

@router.get("/tasks")
async def get_tasks(
    status_filter: Optional[str] = Query(default="pending", alias="status"),
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Get user tasks with same filtering and SQL queries as Next.js
    Equivalent to: SELECT t.*, array_agg(gt.goal_id) as goal_ids FROM tasks t LEFT JOIN goal_tasks gt ON t.id = gt.task_id WHERE t.user_id = $1 AND t.status = $2 GROUP BY t.id ORDER BY t.priority DESC, t.due_date ASC
    """
    try:
        tasks_result = await query(
            """SELECT t.*, array_agg(gt.goal_id) as goal_ids
               FROM tasks t
               LEFT JOIN goal_tasks gt ON t.id = gt.task_id
               WHERE t.user_id = $1 AND t.status = $2
               GROUP BY t.id
               ORDER BY t.priority DESC, t.due_date ASC""",
            [user['id'], status_filter]
        )
        return {"tasks": tasks_result}
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(error)
        )

@router.post("/tasks")
async def create_task(
    task_data: TaskCreate, 
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Dict[str, Any]]:
    """
    Create new task with goal linking logic identical to Next.js
    Equivalent to: INSERT INTO tasks (...) VALUES (...) RETURNING * + goal linking
    """
    from datetime import datetime
    
    # Convert string date to date object if provided
    due_date = None
    if task_data.due_date:
        try:
            due_date = datetime.strptime(task_data.due_date, '%Y-%m-%d').date()
        except ValueError:
            due_date = None
    
    try:
        # Create the task
        task_result = await query(
            """INSERT INTO tasks (user_id, title, description, priority, priority_reasoning, estimated_duration, due_date)
               VALUES ($1, $2, $3, $4, $5, $6, $7) RETURNING *""",
            [
                user['id'], 
                task_data.title, 
                task_data.description, 
                task_data.priority, 
                task_data.priority_reasoning, 
                task_data.estimated_duration, 
                due_date
            ]
        )
        
        created_task = task_result[0]
        
        # Link to goals if provided (identical logic to Next.js)
        if task_data.goal_ids and len(task_data.goal_ids) > 0:
            for goal_id in task_data.goal_ids:
                await query(
                    'INSERT INTO goal_tasks (goal_id, task_id) VALUES ($1, $2)',
                    [goal_id, created_task['id']]
                )
        
        return {"task": created_task}
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(error)
        )

@router.put("/tasks/{task_id}")
async def update_task(
    task_id: str, 
    task_data: TaskUpdate, 
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Dict[str, Any]]:
    """
    Update task with completed_at auto-setting identical to Next.js
    Equivalent to: UPDATE tasks SET ... completed_at = CASE WHEN $5 = 'completed' THEN CURRENT_TIMESTAMP ELSE completed_at END ... WHERE id = $9 AND user_id = $10 RETURNING *
    """
    from datetime import datetime
    
    # Convert string date to date object if provided
    due_date = task_data.due_date
    if due_date:
        try:
            due_date = datetime.strptime(task_data.due_date, '%Y-%m-%d').date()
        except ValueError:
            due_date = None
    
    try:
        task_result = await query(
            """UPDATE tasks SET 
               title = COALESCE($1, title),
               description = COALESCE($2, description),
               priority = COALESCE($3, priority),
               priority_reasoning = COALESCE($4, priority_reasoning),
               status = COALESCE($5, status),
               estimated_duration = COALESCE($6, estimated_duration),
               actual_duration = COALESCE($7, actual_duration),
               due_date = COALESCE($8, due_date),
               completed_at = CASE WHEN $5 = 'completed' THEN CURRENT_TIMESTAMP ELSE completed_at END,
               updated_at = CURRENT_TIMESTAMP
               WHERE id = $9 AND user_id = $10
               RETURNING *""",
            [
                task_data.title, 
                task_data.description, 
                task_data.priority, 
                task_data.priority_reasoning, 
                task_data.status, 
                task_data.estimated_duration, 
                task_data.actual_duration, 
                due_date, 
                task_id, 
                user['id']
            ]
        )
        
        if not task_result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        return {"task": task_result[0]}
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(error)
        )

@router.delete("/tasks/{task_id}")
async def delete_task(
    task_id: str, 
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, str]:
    """
    Delete task with same deletion logic as Next.js
    Equivalent to: DELETE FROM tasks WHERE id = $1 AND user_id = $2
    """
    try:
        await query(
            'DELETE FROM tasks WHERE id = $1 AND user_id = $2',
            [task_id, user['id']]
        )
        return {"message": "Deleted successfully"}
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(error)
        )
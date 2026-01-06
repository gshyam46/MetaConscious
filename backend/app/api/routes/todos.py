"""
Todo API routes for interactive todo management
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
import logging
from uuid import uuid4
from datetime import datetime

from ...api.dependencies import get_current_user
from ...core.database import query
from ...models.schemas import TodoItem, TodoCreate, TodoUpdate
from ...core.exceptions import DatabaseError

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/todos", response_model=List[TodoItem])
async def get_todos(
    status: str = "pending",
    user: dict = Depends(get_current_user)
) -> List[TodoItem]:
    """
    Get todos for the current user
    
    Args:
        status: Filter by status (pending, in_progress, completed, cancelled)
        user: Current authenticated user
        
    Returns:
        List of todo items
    """
    try:
        result = await query(
            """SELECT id, title, description, priority, difficulty, 
                      estimated_duration, due_date, reasoning, subtasks, 
                      status, created_at, updated_at
               FROM todos 
               WHERE user_id = $1 AND status = $2
               ORDER BY priority DESC, due_date ASC NULLS LAST, created_at DESC""",
            [user['id'], status]
        )
        
        todos = []
        for row in result:
            todo_dict = dict(row)
            # Handle subtasks JSON array
            if todo_dict['subtasks'] is None:
                todo_dict['subtasks'] = []
            todos.append(TodoItem(**todo_dict))
        
        return todos
        
    except DatabaseError as e:
        logger.error(f"Database error getting todos: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve todos")
    except Exception as e:
        logger.error(f"Unexpected error getting todos: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/todos", response_model=TodoItem)
async def create_todo(
    todo_data: TodoCreate,
    user: dict = Depends(get_current_user)
) -> TodoItem:
    """
    Create a new todo item
    
    Args:
        todo_data: Todo creation data
        user: Current authenticated user
        
    Returns:
        Created todo item
    """
    try:
        todo_id = str(uuid4())
        now = datetime.utcnow()
        
        result = await query(
            """INSERT INTO todos (id, user_id, title, description, priority, difficulty,
                                estimated_duration, due_date, reasoning, subtasks, status, created_at, updated_at)
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, 'pending', $11, $12)
               RETURNING *""",
            [
                todo_id, user['id'], todo_data.title, todo_data.description,
                todo_data.priority, todo_data.difficulty, todo_data.estimated_duration,
                todo_data.due_date, todo_data.reasoning, todo_data.subtasks,
                now, now
            ]
        )
        
        if not result:
            raise HTTPException(status_code=500, detail="Failed to create todo")
        
        todo_dict = dict(result[0])
        if todo_dict['subtasks'] is None:
            todo_dict['subtasks'] = []
            
        return TodoItem(**todo_dict)
        
    except DatabaseError as e:
        logger.error(f"Database error creating todo: {e}")
        raise HTTPException(status_code=500, detail="Failed to create todo")
    except Exception as e:
        logger.error(f"Unexpected error creating todo: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/todos/{todo_id}", response_model=TodoItem)
async def update_todo(
    todo_id: str,
    todo_data: TodoUpdate,
    user: dict = Depends(get_current_user)
) -> TodoItem:
    """
    Update a todo item
    
    Args:
        todo_id: Todo ID to update
        todo_data: Todo update data
        user: Current authenticated user
        
    Returns:
        Updated todo item
    """
    try:
        # Build dynamic update query
        update_fields = []
        params = []
        param_count = 1
        
        for field, value in todo_data.dict(exclude_unset=True).items():
            if value is not None:
                update_fields.append(f"{field} = ${param_count}")
                params.append(value)
                param_count += 1
        
        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        # Add updated_at
        update_fields.append(f"updated_at = ${param_count}")
        params.append(datetime.utcnow())
        param_count += 1
        
        # Add WHERE conditions
        params.extend([todo_id, user['id']])
        
        query_text = f"""
            UPDATE todos 
            SET {', '.join(update_fields)}
            WHERE id = ${param_count - 1} AND user_id = ${param_count}
            RETURNING *
        """
        
        result = await query(query_text, params)
        
        if not result:
            raise HTTPException(status_code=404, detail="Todo not found")
        
        todo_dict = dict(result[0])
        if todo_dict['subtasks'] is None:
            todo_dict['subtasks'] = []
            
        return TodoItem(**todo_dict)
        
    except DatabaseError as e:
        logger.error(f"Database error updating todo: {e}")
        raise HTTPException(status_code=500, detail="Failed to update todo")
    except Exception as e:
        logger.error(f"Unexpected error updating todo: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/todos/{todo_id}")
async def delete_todo(
    todo_id: str,
    user: dict = Depends(get_current_user)
) -> Dict[str, str]:
    """
    Delete a todo item
    
    Args:
        todo_id: Todo ID to delete
        user: Current authenticated user
        
    Returns:
        Success message
    """
    try:
        result = await query(
            "DELETE FROM todos WHERE id = $1 AND user_id = $2",
            [todo_id, user['id']]
        )
        
        return {"message": "Todo deleted successfully"}
        
    except DatabaseError as e:
        logger.error(f"Database error deleting todo: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete todo")
    except Exception as e:
        logger.error(f"Unexpected error deleting todo: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
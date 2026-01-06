"""
Chat API routes for interactive AI conversations
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List
import logging
from datetime import datetime, date

from ...api.dependencies import get_current_user
from ...services.chat_service import ChatService
from ...services.planning_engine import PlanningEngine
from ...models.schemas import ChatMessage, ChatResponse, ChatAction
from ...core.exceptions import LLMError
from ...core.database import query

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/chat/action")
async def execute_chat_action(
    action_data: Dict[str, Any],
    user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Execute actions suggested by the AI assistant
    
    Args:
        action_data: Action data from chat interface
        user: Current authenticated user
        
    Returns:
        Result of action execution
    """
    try:
        action_type = action_data.get("type")
        data = action_data.get("data", {})
        
        if action_type == "create_structured_plan":
            return await _create_structured_plan(user['id'], data)
        elif action_type == "create_and_plan":
            result = await _create_structured_plan(user['id'], data)
            if result.get("success") and data.get("regenerate_plan"):
                # Also regenerate today's plan
                planner = PlanningEngine()
                today = datetime.now().strftime('%Y-%m-%d')
                await planner.generate_daily_plan(user['id'], today)
                result["plan_regenerated"] = True
            return result
        else:
            return {"success": False, "error": "Unknown action type"}
            
    except Exception as e:
        logger.error(f"Error executing chat action: {e}")
        return {"success": False, "error": str(e)}

async def _create_structured_plan(user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Create goals and tasks from structured data"""
    try:
        def parse_date(date_str):
            """Parse date string to date object, return None if null or invalid"""
            if not date_str or date_str == "null":
                return None
            try:
                # Parse ISO format date string (YYYY-MM-DD)
                return datetime.strptime(date_str, "%Y-%m-%d").date()
            except (ValueError, TypeError):
                return None
        
        goals_created = 0
        tasks_created = 0
        
        # Create goals
        for goal_data in data.get("goals", []):
            target_date = parse_date(goal_data.get("target_date"))
            await query(
                """INSERT INTO goals (user_id, title, description, priority, priority_reasoning, target_date, status)
                   VALUES ($1, $2, $3, $4, $5, $6, 'active')""",
                [
                    user_id,
                    goal_data["title"],
                    goal_data.get("description", ""),
                    goal_data["priority"],
                    goal_data["priority_reasoning"],
                    target_date
                ]
            )
            goals_created += 1
        
        # Create tasks
        for task_data in data.get("tasks", []):
            due_date = parse_date(task_data.get("due_date"))
            await query(
                """INSERT INTO tasks (user_id, title, description, priority, priority_reasoning, 
                                   estimated_duration, due_date, status)
                   VALUES ($1, $2, $3, $4, $5, $6, $7, 'pending')""",
                [
                    user_id,
                    task_data["title"],
                    task_data.get("description", ""),
                    task_data["priority"],
                    task_data["priority_reasoning"],
                    task_data.get("estimated_duration"),
                    due_date
                ]
            )
            tasks_created += 1
        
        return {
            "success": True,
            "goals_created": goals_created,
            "tasks_created": tasks_created,
            "message": f"Created {goals_created} goals and {tasks_created} tasks successfully!"
        }
        
    except Exception as e:
        logger.error(f"Error creating structured plan: {e}")
        return {"success": False, "error": str(e)}


@router.post("/chat", response_model=ChatResponse)
async def chat_with_ai(
    message: ChatMessage,
    user: dict = Depends(get_current_user)
) -> ChatResponse:
    """
    Interactive chat with AI for planning assistance with full context awareness
    
    Args:
        message: User's chat message
        user: Current authenticated user
        
    Returns:
        AI response with context awareness and potential actions
    """
    try:
        chat_service = ChatService()
        
        # Process message with full context
        result = await chat_service.process_message(user['id'], message.content)
        
        # Convert actions to ChatAction objects
        actions = []
        for action in result.get("actions", []):
            actions.append(ChatAction(
                type=action["type"],
                label=action["label"], 
                data=action["data"]
            ))
        
        return ChatResponse(
            response=result["response"],
            timestamp=message.timestamp,
            suggestions=actions
        )
        
    except Exception as e:
        logger.error(f"Unexpected error in chat: {e}")
        raise HTTPException(status_code=500, detail="Chat service unavailable")
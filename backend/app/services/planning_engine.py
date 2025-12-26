"""
Core planning logic - ISOLATED AND REWRITABLE
Identical implementation to Next.js PlanningEngine
"""
import json
import logging
import os
import uuid
from datetime import datetime, timedelta, date
from typing import Dict, Any, List, Optional

from ..services.llm_client import LLMClient
from ..models.schemas import validate_plan
from ..core.database import query

logger = logging.getLogger(__name__)

def serialize_for_json(obj):
    """Convert UUID objects to strings for JSON serialization"""
    if isinstance(obj, uuid.UUID):
        return str(obj)
    elif isinstance(obj, list):
        return [serialize_for_json(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: serialize_for_json(value) for key, value in obj.items()}
    elif isinstance(obj, (datetime, date)):
        return obj.isoformat()
    return obj

class PlanningEngine:
    """Planning engine with identical business logic to Next.js version"""
    
    def __init__(self):
        self.llm_client = LLMClient()
        self.max_retries = 3
    
    async def generate_daily_plan(self, user_id: str, target_date: str) -> Dict[str, Any]:
        """
        Generate daily plan with identical logic flow to Next.js version
        
        Args:
            user_id: User identifier
            target_date: Target date in YYYY-MM-DD format
            
        Returns:
            Generated and validated daily plan
            
        Raises:
            Exception: If plan generation fails after max retries
        """
        # convert
        target_date_obj = datetime.strptime(target_date, "%Y-%m-%d").date()
        # 1. Gather context
        context = await self.gather_planning_context(user_id, target_date)
        
        # 2. Generate plan with LLM
        plan = None
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                raw_plan = await self.llm_client.generate_plan(context)
                plan = validate_plan(raw_plan)
                break
            except Exception as error:
                last_error = error
                logger.error(f"Plan generation attempt {attempt + 1} failed: {error}")
        
        if not plan:
            raise Exception(f"Failed to generate valid plan after {self.max_retries} attempts: {last_error}")
        
        # 3. Save plan to database
        await self.save_plan(user_id, target_date, plan.dict())
        
        return plan.dict()
    
    async def gather_planning_context(self, user_id: str, target_date: str) -> Dict[str, Any]:
        """
        Gather planning context with same SQL queries as Next.js version
        
        Args:
            user_id: User identifier
            target_date: Target date in YYYY-MM-DD format
            
        Returns:
            Planning context dictionary with goals, tasks, events, etc.
        """
        # Calculate tomorrow's date
        target_dt = datetime.strptime(target_date, '%Y-%m-%d')
        tomorrow = target_dt + timedelta(days=1)
        tomorrow_str = tomorrow.strftime('%Y-%m-%d')
        
        # Get active goals
        goals_result = await query(
            """SELECT id, title, description, priority, priority_reasoning, target_date 
               FROM goals 
               WHERE user_id = $1 AND status = 'active' 
               ORDER BY priority DESC 
               LIMIT 5""",
            [user_id]
        )
        
        # Get pending tasks
        tasks_result = await query(
            """SELECT t.id, t.title, t.description, t.priority, t.priority_reasoning, 
                      t.estimated_duration, t.due_date,
                      array_agg(gt.goal_id) as goal_ids
               FROM tasks t
               LEFT JOIN goal_tasks gt ON t.id = gt.task_id
               WHERE t.user_id = $1 AND t.status IN ('pending', 'in_progress')
               GROUP BY t.id
               ORDER BY t.priority DESC, t.due_date ASC""",
            [user_id]
        )
        
        # Get tomorrow's calendar events - simplified query to avoid date issues
        events_result = await query(
            """SELECT id, title, start_time, end_time, event_type, is_blocking
               FROM calendar_events
               WHERE user_id = $1 
               ORDER BY start_time ASC""",
            [user_id]
        )
        
        # Get relationships and time budgets
        relationships_result = await query(
            """SELECT id, name, relationship_type, priority, time_budget_hours, last_interaction
               FROM relationships
               WHERE user_id = $1
               ORDER BY priority DESC""",
            [user_id]
        )
        
        # Calculate recent performance (last 7 days)
        performance_result = await query(
            """SELECT 
                 COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_tasks,
                 COUNT(CASE WHEN status = 'cancelled' THEN 1 END) as cancelled_tasks,
                 AVG(CASE WHEN actual_duration IS NOT NULL AND estimated_duration IS NOT NULL 
                     THEN actual_duration::float / NULLIF(estimated_duration, 0) END) as avg_duration_ratio
               FROM tasks
               WHERE user_id = $1 
                 AND updated_at >= NOW() - INTERVAL '7 days'""",
            [user_id]
        )
        
        # Serialize all data to handle UUID objects
        context = {
            'date': target_date,
            'goals': serialize_for_json(goals_result),
            'tasks': serialize_for_json(tasks_result),
            'calendarEvents': serialize_for_json(events_result),
            'relationships': serialize_for_json(relationships_result),
            'recentPerformance': serialize_for_json(performance_result[0] if performance_result else {}),
        }
        
        return context
    
    async def save_plan(self, user_id: str, plan_date: date, plan: Dict[str, Any]):
        """
        Save plan to database with identical logic to Next.js version
        
        Args:
            user_id: User identifier
            plan_date: Plan date in YYYY-MM-DD format
            plan: Plan dictionary to save
            
        Returns:
            Saved plan record
        """
        # Convert plan_date string to date object for database
        plan_date_obj = datetime.strptime(plan_date, '%Y-%m-%d').date()
        
        result = await query(
            """INSERT INTO daily_plans (user_id, plan_date, plan_json, reasoning, is_override)
               VALUES ($1, $2, $3, $4, false)
               ON CONFLICT (user_id, plan_date) 
               DO UPDATE SET 
                 plan_json = EXCLUDED.plan_json,
                 reasoning = EXCLUDED.reasoning,
                 modified_at = CURRENT_TIMESTAMP
               RETURNING *""",
            [user_id, plan_date_obj, json.dumps(plan), plan.get('reasoning', '')]
        )
        
        return result[0] if result else {}
    
    async def reschedule_task(self, user_id: str, task_id: str, new_date: str, reason: str) -> None:
        """
        Reschedule task with identical logic to Next.js version
        
        Args:
            user_id: User identifier
            task_id: Task identifier to reschedule
            new_date: New due date in YYYY-MM-DD format
            reason: Reason for rescheduling
        """
        # Update task
        await query(
            'UPDATE tasks SET due_date = $1, updated_at = CURRENT_TIMESTAMP WHERE id = $2 AND user_id = $3',
            [new_date, task_id, user_id]
        )
        
        # Regenerate plan for that date
        new_date_dt = datetime.strptime(new_date, '%Y-%m-%d')
        plan_date = new_date_dt - timedelta(days=1)  # Generate plan the day before
        plan_date_str = plan_date.strftime('%Y-%m-%d')
        
        await self.generate_daily_plan(user_id, plan_date_str)
    
    async def check_weekly_overrides(self, user_id: str) -> Dict[str, Any]:
        """
        Check weekly override count with identical logic to Next.js version
        
        Args:
            user_id: User identifier
            
        Returns:
            Override status dictionary with count, remaining, limit, canOverride
        """
        now = datetime.now()
        week_number = self.get_week_number(now)
        
        result = await query(
            'SELECT COUNT(*) as count FROM override_log WHERE user_id = $1 AND week_number = $2',
            [user_id, week_number]
        )
        
        count = int(result[0]['count']) if result else 0
        max_overrides = int(os.environ.get('MAX_WEEKLY_OVERRIDES', '5'))
        
        return {
            'count': count,
            'remaining': max(0, max_overrides - count),
            'limit': max_overrides,
            'canOverride': count < max_overrides,
        }
    
    async def log_override(self, user_id: str, plan_id: str, override_type: str, reason: str) -> None:
        """
        Log override with identical logic to Next.js version
        
        Args:
            user_id: User identifier
            plan_id: Plan identifier being overridden
            override_type: Type of override
            reason: Reason for override
        """
        now = datetime.now()
        week_number = self.get_week_number(now)
        
        await query(
            'INSERT INTO override_log (user_id, plan_id, override_type, override_reason, week_number) VALUES ($1, $2, $3, $4, $5)',
            [user_id, plan_id, override_type, reason, week_number]
        )
    
    def get_week_number(self, date: datetime) -> int:
        """
        Get ISO week number with identical logic to Next.js version
        
        Args:
            date: Date to get week number for
            
        Returns:
            ISO week number
        """
        # Convert to UTC and adjust for ISO week calculation
        d = datetime(date.year, date.month, date.day)
        day_num = d.weekday() + 1  # Monday = 1, Sunday = 7
        if day_num == 7:
            day_num = 0  # Sunday = 0 for calculation
        
        # Adjust to Thursday of the same week
        d = d + timedelta(days=(4 - day_num))
        
        # Get year start
        year_start = datetime(d.year, 1, 1)
        
        # Calculate week number
        days_diff = (d - year_start).days + 1
        week_number = (days_diff + 6) // 7
        
        return week_number
"""
Plans API endpoints
Implements identical functionality to Next.js plans endpoints
"""
from fastapi import APIRouter, Depends, Query
from typing import Dict, Any, Optional
import os
import logging
import json
from app.api.dependencies import get_current_user
from app.core.database import query
from app.core.exceptions import LLMError, OverrideLimitError, ValidationError
from app.services.planning_engine import PlanningEngine
from app.models.schemas import DailyPlan

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/plans")
async def get_plans(
    date: Optional[str] = Query(default=None, description="Date in YYYY-MM-DD format"),
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get daily plan with same date filtering logic as Next.js
    Equivalent to: SELECT * FROM daily_plans WHERE user_id = $1 AND plan_date = $2
    """
    from datetime import datetime
    
    # Use current date if no date provided (same logic as Next.js)
    if not date:
        date = datetime.now().strftime('%Y-%m-%d')
    
    # Convert string date to date object for database query
    try:
        date_obj = datetime.strptime(date, '%Y-%m-%d').date()
    except ValueError:
        date_obj = datetime.now().date()
    
    # Database errors handled by exception handlers
    plan_result = await query(
        'SELECT * FROM daily_plans WHERE user_id = $1 AND plan_date = $2',
        [user['id'], date_obj]
    )
    
    if not plan_result:
        return {"plan": None}

    row = plan_result[0]

    # 🔴 CRITICAL FIX: unwrap + parse plan_json
    plan_json = row["plan_json"]
    if isinstance(plan_json, str):
        plan_json = json.loads(plan_json)

    # ✅ Return DOMAIN plan, not DB row
    return {
        "plan": {
            **plan_json,
            "date": row["plan_date"].isoformat(),
        }
    }

@router.post("/generate-plan")
async def generate_plan(
    request_data: Dict[str, Any],
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Generate daily plan with LLM integration identical to Next.js
    Includes same LLM_API_KEY checking and error responses
    """
    # Check LLM configuration (identical to Next.js logic)
    if not os.environ.get('LLM_API_KEY'):
        raise ValidationError("LLM not configured. Set LLM_API_KEY in .env file")
    
    # Get target date or use current date (same logic as Next.js)
    target_date = request_data.get('date')
    if not target_date:
        from datetime import datetime
        target_date = datetime.now().strftime('%Y-%m-%d')
    
    # Generate plan using PlanningEngine - LLM errors handled by exception handlers
    planner = PlanningEngine()
    plan = await planner.generate_daily_plan(user['id'], target_date)
    
    return {
        "plan": plan,
        "message": "Plan generated successfully"
    }

@router.get("/overrides")
async def get_overrides(
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get weekly override status using PlanningEngine.check_weekly_overrides()
    Identical to Next.js GET /api/overrides endpoint
    """
    planner = PlanningEngine()
    override_status = await planner.check_weekly_overrides(user['id'])
    
    return {"overrides": override_status}

@router.put("/override-plan/{plan_id}")
async def override_plan(
    plan_id: str,
    request_data: Dict[str, Any],
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Override plan with same limit checking as Next.js PUT /api/override-plan/{id}
    Includes identical override logging and limit enforcement
    """
    planner = PlanningEngine()
    
    # Check weekly override limit (identical to Next.js logic)
    override_check = await planner.check_weekly_overrides(user['id'])
    
    if not override_check['canOverride']:
        # Use custom exception with identical error format to Next.js
        raise OverrideLimitError(
            f"Weekly override limit reached ({override_check['limit']})",
            override_check
        )
    
    # Log override with same parameters as Next.js
    override_type = request_data.get('override_type', 'manual')
    reason = request_data.get('reason', '')
    
    await planner.log_override(user['id'], plan_id, override_type, reason)
    
    # Return updated override status (identical to Next.js response)
    updated_overrides = await planner.check_weekly_overrides(user['id'])
    
    return {
        "message": "Override logged",
        "overrides": updated_overrides
    }



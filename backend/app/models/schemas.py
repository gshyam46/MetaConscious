"""
Pydantic validation models
Equivalent to Zod schemas in Next.js implementation
"""
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Literal
from datetime import datetime, date
import re

class TimeBlock(BaseModel):
    """Time block model - equivalent to TimeBlockSchema"""
    start_time: str = Field(..., pattern=r'^\d{2}:\d{2}$')
    end_time: str = Field(..., pattern=r'^\d{2}:\d{2}$')
    task_id: Optional[str] = Field(None, pattern=r'^[0-9a-f-]{36}$')
    activity: str = Field(..., min_length=1)
    priority: int = Field(..., ge=1, le=5)
    reasoning: str = Field(..., min_length=1)

class GoalProgress(BaseModel):
    """Goal progress model - equivalent to GoalProgressSchema"""
    goal_id: str = Field(..., pattern=r'^[0-9a-f-]{36}$')
    status: Literal['on_track', 'at_risk', 'blocked']
    action_needed: str

class SocialTime(BaseModel):
    """Social time allocation model - equivalent to SocialTimeSchema"""
    total_minutes: int = Field(..., ge=0)
    reasoning: str = Field(..., min_length=1)

class DailyPlan(BaseModel):
    """Daily plan model - equivalent to DailyPlanSchema"""
    date: str = Field(..., pattern=r'^\d{4}-\d{2}-\d{2}$')
    reasoning: str = Field(..., min_length=10)
    priority_analysis: str = Field(..., min_length=10)
    time_blocks: List[TimeBlock]
    social_time_allocation: SocialTime
    goal_progress_assessment: List[GoalProgress]
    warnings: List[str]

# Request/Response models for API endpoints

class GoalCreate(BaseModel):
    """Goal creation model"""
    title: str
    description: Optional[str] = None
    priority: int = Field(..., ge=1, le=5)
    priority_reasoning: str = Field(..., min_length=10)
    target_date: Optional[str] = None

class GoalUpdate(BaseModel):
    """Goal update model"""
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[int] = Field(None, ge=1, le=5)
    priority_reasoning: Optional[str] = Field(None, min_length=10)
    target_date: Optional[str] = None
    status: Optional[Literal['active', 'completed', 'paused']] = None

class TaskCreate(BaseModel):
    """Task creation model"""
    title: str
    description: Optional[str] = None
    priority: int = Field(..., ge=1, le=5)
    priority_reasoning: str = Field(..., min_length=1)
    estimated_duration: Optional[int] = None  # minutes
    due_date: Optional[str] = None
    goal_ids: Optional[List[str]] = None

class TaskUpdate(BaseModel):
    """Task update model"""
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[int] = Field(None, ge=1, le=5)
    priority_reasoning: Optional[str] = Field(None, min_length=1)
    estimated_duration: Optional[int] = None
    due_date: Optional[str] = None
    status: Optional[Literal['pending', 'in_progress', 'completed', 'cancelled']] = None
    actual_duration: Optional[int] = None
    goal_ids: Optional[List[str]] = None

class CalendarEventCreate(BaseModel):
    """Calendar event creation model"""
    title: str
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    event_type: Literal['internal', 'external', 'task', 'social'] = 'internal'
    is_blocking: bool = True
    external_id: Optional[str] = None

class CalendarEventUpdate(BaseModel):
    """Calendar event update model"""
    title: Optional[str] = None
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    event_type: Optional[Literal['internal', 'external', 'task', 'social']] = None
    is_blocking: Optional[bool] = None
    external_id: Optional[str] = None

class RelationshipCreate(BaseModel):
    """Relationship creation model"""
    name: str = Field(..., min_length=1, max_length=255)
    relationship_type: Literal['partner', 'friend', 'family', 'other']
    priority: int = Field(..., ge=1, le=5)
    time_budget_hours: Optional[float] = Field(None, ge=0)
    notes: Optional[str] = None

class RelationshipUpdate(BaseModel):
    """Relationship update model"""
    name: Optional[str] = Field(None, max_length=255)
    relationship_type: Optional[Literal['partner', 'friend', 'family', 'other']] = None
    priority: Optional[int] = Field(None, ge=1, le=5)
    time_budget_hours: Optional[float] = Field(None, ge=0)
    last_interaction: Optional[datetime] = None
    emotional_impact_last: Optional[str] = None
    notes: Optional[str] = None

class UserCreate(BaseModel):
    """User creation model"""
    username: str = Field(..., max_length=100)
    password: str = Field(..., min_length=8)

# Response models

class GoalResponse(BaseModel):
    """Goal response model"""
    id: str
    user_id: str
    title: str
    description: Optional[str]
    priority: int
    priority_reasoning: str
    status: str
    target_date: Optional[date]
    created_at: datetime
    updated_at: datetime

class TaskResponse(BaseModel):
    """Task response model"""
    id: str
    user_id: str
    title: str
    description: Optional[str]
    priority: int
    priority_reasoning: str
    status: str
    estimated_duration: Optional[int]
    actual_duration: Optional[int]
    due_date: Optional[date]
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    goal_ids: Optional[List[str]] = None

class CalendarEventResponse(BaseModel):
    """Calendar event response model"""
    id: str
    user_id: str
    title: str
    description: Optional[str]
    start_time: datetime
    end_time: datetime
    event_type: str
    is_blocking: bool
    external_id: Optional[str]
    created_at: datetime
    updated_at: datetime

class RelationshipResponse(BaseModel):
    """Relationship response model"""
    id: str
    user_id: str
    name: str
    relationship_type: str
    priority: int
    time_budget_hours: Optional[float]
    last_interaction: Optional[datetime]
    emotional_impact_last: Optional[str]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

class UserResponse(BaseModel):
    """User response model"""
    id: str
    username: str
    created_at: datetime

# Utility function for plan validation (equivalent to validatePlan in schemas.js)
def validate_plan(plan_data: dict) -> DailyPlan:
    """Validate plan structure - equivalent to validatePlan function"""
    try:
        return DailyPlan(**plan_data)
    except Exception as error:
        raise ValueError(f"Invalid plan structure: {str(error)}")
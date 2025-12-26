"""
SQLAlchemy database models
Matching the existing PostgreSQL schema exactly
"""
from sqlalchemy import Column, String, Integer, Text, DateTime, Date, Boolean, ForeignKey, CheckConstraint, UniqueConstraint, DECIMAL
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()

class User(Base):
    """User model - matches users table"""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    goals = relationship("Goal", back_populates="user", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="user", cascade="all, delete-orphan")
    daily_plans = relationship("DailyPlan", back_populates="user", cascade="all, delete-orphan")
    calendar_events = relationship("CalendarEvent", back_populates="user", cascade="all, delete-orphan")
    relationships = relationship("Relationship", back_populates="user", cascade="all, delete-orphan")

class Goal(Base):
    """Goal model - matches goals table"""
    __tablename__ = "goals"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(Text, nullable=False)
    description = Column(Text)
    priority = Column(Integer, nullable=False)
    priority_reasoning = Column(Text, nullable=False)
    status = Column(String(20), default="active")
    target_date = Column(Date)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Constraints
    __table_args__ = (
        CheckConstraint('priority >= 1 AND priority <= 5', name='goals_priority_check'),
        CheckConstraint("status IN ('active', 'completed', 'paused')", name='goals_status_check'),
    )
    
    # Relationships
    user = relationship("User", back_populates="goals")
    goal_tasks = relationship("GoalTask", back_populates="goal", cascade="all, delete-orphan")

class Task(Base):
    """Task model - matches tasks table"""
    __tablename__ = "tasks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(Text, nullable=False)
    description = Column(Text)
    priority = Column(Integer, nullable=False)
    priority_reasoning = Column(Text, nullable=False)
    status = Column(String(20), default="pending")
    estimated_duration = Column(Integer)  # minutes
    actual_duration = Column(Integer)  # minutes
    due_date = Column(Date)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Constraints
    __table_args__ = (
        CheckConstraint('priority >= 1 AND priority <= 5', name='tasks_priority_check'),
        CheckConstraint("status IN ('pending', 'in_progress', 'completed', 'cancelled')", name='tasks_status_check'),
    )
    
    # Relationships
    user = relationship("User", back_populates="tasks")
    goal_tasks = relationship("GoalTask", back_populates="task", cascade="all, delete-orphan")

class GoalTask(Base):
    """Goal-Task mapping - matches goal_tasks table"""
    __tablename__ = "goal_tasks"
    
    goal_id = Column(UUID(as_uuid=True), ForeignKey("goals.id", ondelete="CASCADE"), primary_key=True)
    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True)
    
    # Relationships
    goal = relationship("Goal", back_populates="goal_tasks")
    task = relationship("Task", back_populates="goal_tasks")

class DailyPlan(Base):
    """Daily plan model - matches daily_plans table"""
    __tablename__ = "daily_plans"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    plan_date = Column(Date, nullable=False)
    plan_json = Column(JSONB, nullable=False)  # Structured plan data
    reasoning = Column(Text, nullable=False)
    generated_at = Column(DateTime, default=datetime.utcnow)
    modified_at = Column(DateTime, default=datetime.utcnow)
    is_override = Column(Boolean, default=False)
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('user_id', 'plan_date', name='daily_plans_user_date_unique'),
    )
    
    # Relationships
    user = relationship("User", back_populates="daily_plans")
    override_logs = relationship("OverrideLog", back_populates="plan", cascade="all, delete-orphan")

class CalendarEvent(Base):
    """Calendar event model - matches calendar_events table"""
    __tablename__ = "calendar_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(Text, nullable=False)
    description = Column(Text)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    event_type = Column(String(20), default="internal")
    is_blocking = Column(Boolean, default=True)
    external_id = Column(String(255))  # For calendar sync
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Constraints
    __table_args__ = (
        CheckConstraint("event_type IN ('internal', 'external', 'task', 'social')", name='calendar_events_type_check'),
    )
    
    # Relationships
    user = relationship("User", back_populates="calendar_events")

class Relationship(Base):
    """Relationship model - matches relationships table"""
    __tablename__ = "relationships"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    relationship_type = Column(String(50), nullable=False)
    priority = Column(Integer, nullable=False)
    time_budget_hours = Column(DECIMAL(5, 2))  # Weekly time budget
    last_interaction = Column(DateTime)
    emotional_impact_last = Column(Text)  # Last interaction sentiment
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Constraints
    __table_args__ = (
        CheckConstraint('priority >= 1 AND priority <= 5', name='relationships_priority_check'),
        CheckConstraint("relationship_type IN ('partner', 'friend', 'family', 'other')", name='relationships_type_check'),
    )
    
    # Relationships
    user = relationship("User", back_populates="relationships")

class OverrideLog(Base):
    """Override log model - matches override_log table"""
    __tablename__ = "override_log"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    plan_id = Column(UUID(as_uuid=True), ForeignKey("daily_plans.id", ondelete="CASCADE"), nullable=False)
    override_type = Column(String(50), nullable=False)
    override_reason = Column(Text)
    override_timestamp = Column(DateTime, default=datetime.utcnow)
    week_number = Column(Integer, nullable=False)
    
    # Relationships
    user = relationship("User")
    plan = relationship("DailyPlan", back_populates="override_logs")

class BehavioralData(Base):
    """Behavioral data model - matches behavioral_data table (scaffold)"""
    __tablename__ = "behavioral_data"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    data_type = Column(String(50), nullable=False)
    data_json = Column(JSONB, nullable=False)
    recorded_at = Column(DateTime, default=datetime.utcnow)
    
    # Constraints
    __table_args__ = (
        CheckConstraint("data_type IN ('phone_usage', 'meal', 'spending')", name='behavioral_data_type_check'),
    )
    
    # Relationships
    user = relationship("User")

class ContextualMemory(Base):
    """Contextual memory model - matches contextual_memory table (scaffold)"""
    __tablename__ = "contextual_memory"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    context_type = Column(String(50), nullable=False)
    context_data = Column(JSONB, nullable=False)
    relevance_score = Column(DECIMAL(3, 2))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User")

class ProceduralMemory(Base):
    """Procedural memory model - matches procedural_memory table (scaffold)"""
    __tablename__ = "procedural_memory"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    procedure_type = Column(String(50), nullable=False)
    procedure_data = Column(JSONB, nullable=False)
    success_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User")

class LongTermMemory(Base):
    """Long-term memory model - matches long_term_memory table (scaffold)"""
    __tablename__ = "long_term_memory"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    memory_type = Column(String(50), nullable=False)
    memory_data = Column(JSONB, nullable=False)
    importance_score = Column(DECIMAL(3, 2))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User")
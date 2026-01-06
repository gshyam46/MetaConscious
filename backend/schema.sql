-- MetaConscious Database Schema
-- Complete schema for autonomous AI planning system

-- Users table (single user system)
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Goals table (max 3-5 active goals)
CREATE TABLE IF NOT EXISTS goals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT,
    priority INTEGER NOT NULL CHECK (priority >= 1 AND priority <= 5),
    reasoning TEXT NOT NULL,
    target_date DATE,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'completed', 'paused', 'cancelled')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tasks table (actionable items with priority reasoning)
CREATE TABLE IF NOT EXISTS tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    goal_id UUID REFERENCES goals(id) ON DELETE SET NULL,
    title TEXT NOT NULL,
    description TEXT,
    priority INTEGER NOT NULL CHECK (priority >= 1 AND priority <= 5),
    difficulty INTEGER NOT NULL CHECK (difficulty >= 1 AND difficulty <= 5),
    estimated_duration INTEGER CHECK (estimated_duration >= 5), -- minutes
    due_date TIMESTAMP WITH TIME ZONE,
    reasoning TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed', 'cancelled')),
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Daily plans table (AI-generated schedules with JSONB storage)
CREATE TABLE IF NOT EXISTS daily_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    plan_data JSONB NOT NULL, -- Stores time blocks, goals, social time, etc.
    reasoning TEXT NOT NULL,
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'completed', 'overridden')),
    UNIQUE(user_id, date)
);

-- Calendar events table (internal + external events)
CREATE TABLE IF NOT EXISTS calendar_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE NOT NULL,
    location TEXT,
    event_type VARCHAR(50) DEFAULT 'personal' CHECK (event_type IN ('personal', 'work', 'social', 'external')),
    external_id TEXT, -- For external calendar sync
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Relationships table (social connections with time budgets)
CREATE TABLE IF NOT EXISTS relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    relationship_type VARCHAR(50) NOT NULL,
    time_budget_minutes INTEGER DEFAULT 0, -- Weekly time budget
    priority INTEGER DEFAULT 3 CHECK (priority >= 1 AND priority <= 5),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Override log table (manual override tracking)
CREATE TABLE IF NOT EXISTS override_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    plan_id UUID REFERENCES daily_plans(id) ON DELETE CASCADE,
    override_type VARCHAR(50) NOT NULL,
    original_data JSONB,
    new_data JSONB,
    reasoning TEXT,
    week_number INTEGER NOT NULL, -- For weekly limit tracking
    year INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Todos table (enhanced task management)
CREATE TABLE IF NOT EXISTS todos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT,
    priority INTEGER NOT NULL CHECK (priority >= 1 AND priority <= 5),
    difficulty INTEGER NOT NULL CHECK (difficulty >= 1 AND difficulty <= 5),
    estimated_duration INTEGER CHECK (estimated_duration >= 5),
    due_date TIMESTAMP WITH TIME ZONE,
    reasoning TEXT NOT NULL,
    subtasks JSONB DEFAULT '[]'::jsonb,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed', 'cancelled')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Memory systems (scaffolded for future development)
CREATE TABLE IF NOT EXISTS contextual_memory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    context_type VARCHAR(100) NOT NULL,
    context_data JSONB NOT NULL,
    relevance_score DECIMAL(3,2) DEFAULT 0.5,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE
);

CREATE TABLE IF NOT EXISTS procedural_memory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    procedure_name VARCHAR(255) NOT NULL,
    procedure_data JSONB NOT NULL,
    success_rate DECIMAL(3,2) DEFAULT 0.0,
    usage_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS long_term_memory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    memory_type VARCHAR(100) NOT NULL,
    memory_data JSONB NOT NULL,
    importance_score DECIMAL(3,2) DEFAULT 0.5,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_accessed TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_goals_user_status ON goals(user_id, status);
CREATE INDEX IF NOT EXISTS idx_goals_priority ON goals(priority DESC);

CREATE INDEX IF NOT EXISTS idx_tasks_user_status ON tasks(user_id, status);
CREATE INDEX IF NOT EXISTS idx_tasks_goal ON tasks(goal_id);
CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority DESC);
CREATE INDEX IF NOT EXISTS idx_tasks_due_date ON tasks(due_date ASC) WHERE due_date IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_daily_plans_user_date ON daily_plans(user_id, date);
CREATE INDEX IF NOT EXISTS idx_daily_plans_date ON daily_plans(date DESC);

CREATE INDEX IF NOT EXISTS idx_calendar_user_time ON calendar_events(user_id, start_time);
CREATE INDEX IF NOT EXISTS idx_calendar_time_range ON calendar_events(start_time, end_time);

CREATE INDEX IF NOT EXISTS idx_relationships_user ON relationships(user_id);
CREATE INDEX IF NOT EXISTS idx_relationships_priority ON relationships(priority DESC);

CREATE INDEX IF NOT EXISTS idx_override_log_user_week ON override_log(user_id, year, week_number);
CREATE INDEX IF NOT EXISTS idx_override_log_plan ON override_log(plan_id);

CREATE INDEX IF NOT EXISTS idx_todos_user_status ON todos(user_id, status);
CREATE INDEX IF NOT EXISTS idx_todos_priority ON todos(priority DESC);
CREATE INDEX IF NOT EXISTS idx_todos_due_date ON todos(due_date ASC) WHERE due_date IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_contextual_memory_user_type ON contextual_memory(user_id, context_type);
CREATE INDEX IF NOT EXISTS idx_contextual_memory_relevance ON contextual_memory(relevance_score DESC);

CREATE INDEX IF NOT EXISTS idx_procedural_memory_user ON procedural_memory(user_id);
CREATE INDEX IF NOT EXISTS idx_procedural_memory_success ON procedural_memory(success_rate DESC);

CREATE INDEX IF NOT EXISTS idx_long_term_memory_user_type ON long_term_memory(user_id, memory_type);
CREATE INDEX IF NOT EXISTS idx_long_term_memory_importance ON long_term_memory(importance_score DESC);

-- Insert default user if none exists
INSERT INTO users (username, password_hash) 
SELECT 'admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RK.PJ/...' 
WHERE NOT EXISTS (SELECT 1 FROM users);
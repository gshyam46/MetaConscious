-- Create todos table for MetaConscious
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

-- Create index for efficient queries
CREATE INDEX IF NOT EXISTS idx_todos_user_status ON todos(user_id, status);
CREATE INDEX IF NOT EXISTS idx_todos_priority ON todos(priority DESC);
CREATE INDEX IF NOT EXISTS idx_todos_due_date ON todos(due_date ASC) WHERE due_date IS NOT NULL;
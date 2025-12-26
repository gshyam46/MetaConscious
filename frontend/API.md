# MetaConscious API Reference

Complete API documentation with examples.

---

## Base URL

```
http://localhost:3000/api
```

---

## Authentication

Single-user system. After initialization, all endpoints require the user to exist.

---

## Endpoints

### System

#### GET /api/status

Check system status and configuration.

**Response:**
```json
{
  "status": "operational",
  "user": {
    "id": "uuid",
    "username": "user"
  },
  "llm_configured": true
}
```

#### POST /api/init

Initialize the single user. Only works if no user exists.

**Request:**
```json
{
  "username": "user",
  "password": "password"
}
```

**Response:**
```json
{
  "message": "User created",
  "user": {
    "id": "uuid",
    "username": "user"
  }
}
```

---

### Goals

#### GET /api/goals

List all goals for the user.

**Response:**
```json
{
  "goals": [
    {
      "id": "uuid",
      "user_id": "uuid",
      "title": "Launch MetaConscious MVP",
      "description": "Build and deploy the system",
      "priority": 1,
      "priority_reasoning": "Critical project with immediate impact",
      "status": "active",
      "target_date": "2025-07-01T00:00:00.000Z",
      "created_at": "2025-06-17T00:00:00.000Z",
      "updated_at": "2025-06-17T00:00:00.000Z"
    }
  ]
}
```

#### POST /api/goals

Create a new goal.

**Request:**
```json
{
  "title": "Complete work project",
  "description": "Finish Q2 deliverables",
  "priority": 1,
  "priority_reasoning": "Critical deadline with stakeholder visibility",
  "target_date": "2025-06-30"
}
```

**Required Fields:**
- `title` (string)
- `priority` (integer 1-5)
- `priority_reasoning` (string, min 10 chars)

**Optional Fields:**
- `description` (string)
- `target_date` (date string YYYY-MM-DD)

**Response:**
```json
{
  "goal": {
    "id": "uuid",
    "title": "Complete work project",
    ...
  }
}
```

#### PUT /api/goals/:id

Update an existing goal.

**Request:**
```json
{
  "title": "Updated title",
  "priority": 2,
  "status": "completed"
}
```

**Response:**
```json
{
  "goal": {
    "id": "uuid",
    ...
  }
}
```

#### DELETE /api/goals/:id

Delete a goal and its task associations.

**Response:**
```json
{
  "message": "Deleted successfully"
}
```

---

### Tasks

#### GET /api/tasks

List tasks filtered by status.

**Query Parameters:**
- `status` (optional): `pending`, `in_progress`, `completed`, `cancelled`
  - Default: `pending`

**Example:**
```bash
GET /api/tasks?status=pending
```

**Response:**
```json
{
  "tasks": [
    {
      "id": "uuid",
      "user_id": "uuid",
      "title": "Write system documentation",
      "description": "Document architecture",
      "priority": 2,
      "priority_reasoning": "Important for maintainability",
      "status": "pending",
      "estimated_duration": 120,
      "actual_duration": null,
      "due_date": "2025-06-18T00:00:00.000Z",
      "completed_at": null,
      "created_at": "2025-06-17T00:00:00.000Z",
      "updated_at": "2025-06-17T00:00:00.000Z",
      "goal_ids": ["uuid1", "uuid2"]
    }
  ]
}
```

#### POST /api/tasks

Create a new task.

**Request:**
```json
{
  "title": "Review quarterly reports",
  "description": "Analyze team performance",
  "priority": 2,
  "priority_reasoning": "Important for next quarter planning",
  "estimated_duration": 90,
  "due_date": "2025-06-18",
  "goal_ids": ["uuid1", "uuid2"]
}
```

**Required Fields:**
- `title` (string)
- `priority` (integer 1-5)
- `priority_reasoning` (string)

**Optional Fields:**
- `description` (string)
- `estimated_duration` (integer, minutes)
- `due_date` (date string)
- `goal_ids` (array of UUIDs)

**Response:**
```json
{
  "task": {
    "id": "uuid",
    ...
  }
}
```

#### PUT /api/tasks/:id

Update an existing task.

**Request:**
```json
{
  "status": "completed",
  "actual_duration": 85
}
```

**Auto-set Fields:**
- `completed_at`: Set to current timestamp when `status` = `completed`

**Response:**
```json
{
  "task": {
    "id": "uuid",
    "status": "completed",
    "completed_at": "2025-06-17T14:30:00.000Z",
    ...
  }
}
```

#### DELETE /api/tasks/:id

Delete a task.

**Response:**
```json
{
  "message": "Deleted successfully"
}
```

---

### Plans

#### GET /api/plans

Get daily plan for a specific date.

**Query Parameters:**
- `date` (optional): YYYY-MM-DD format
  - Default: today

**Example:**
```bash
GET /api/plans?date=2025-06-17
```

**Response:**
```json
{
  "plan": {
    "id": "uuid",
    "user_id": "uuid",
    "plan_date": "2025-06-17",
    "plan_json": {
      "date": "2025-06-17",
      "reasoning": "Based on your active goals and pending tasks...",
      "priority_analysis": "Goal 1 is at risk, increasing time allocation...",
      "time_blocks": [
        {
          "start_time": "09:00",
          "end_time": "11:00",
          "task_id": "uuid",
          "activity": "Write system documentation",
          "priority": 2,
          "reasoning": "Morning hours for deep work"
        }
      ],
      "social_time_allocation": {
        "total_minutes": 120,
        "reasoning": "Standard allocation, no conflicts"
      },
      "goal_progress_assessment": [
        {
          "goal_id": "uuid",
          "status": "on_track",
          "action_needed": "Continue current pace"
        }
      ],
      "warnings": [
        "Task X due tomorrow, not yet scheduled"
      ]
    },
    "reasoning": "System reasoning text",
    "generated_at": "2025-06-16T02:00:00.000Z",
    "modified_at": "2025-06-16T02:00:00.000Z",
    "is_override": false
  }
}
```

**No Plan Response:**
```json
{
  "plan": null
}
```

#### POST /api/generate-plan

Manually trigger plan generation.

**Request:**
```json
{
  "date": "2025-06-17"
}
```

**Optional Fields:**
- `date` (string): Target date for plan, defaults to today

**Response:**
```json
{
  "plan": {
    "date": "2025-06-17",
    "reasoning": "...",
    "time_blocks": [...],
    ...
  },
  "message": "Plan generated successfully"
}
```

**Error Response (LLM not configured):**
```json
{
  "error": "LLM not configured. Set LLM_API_KEY in .env file"
}
```

---

### Calendar

#### GET /api/calendar

Get calendar events for a date range.

**Query Parameters:**
- `start` (required): YYYY-MM-DD
- `end` (optional): YYYY-MM-DD

**Example:**
```bash
GET /api/calendar?start=2025-06-17&end=2025-06-24
```

**Response:**
```json
{
  "events": [
    {
      "id": "uuid",
      "user_id": "uuid",
      "title": "Team meeting",
      "description": "Weekly standup",
      "start_time": "2025-06-17T10:00:00.000Z",
      "end_time": "2025-06-17T11:00:00.000Z",
      "event_type": "internal",
      "is_blocking": true,
      "external_id": null,
      "created_at": "2025-06-17T00:00:00.000Z",
      "updated_at": "2025-06-17T00:00:00.000Z"
    }
  ]
}
```

#### POST /api/calendar

Create a calendar event.

**Request:**
```json
{
  "title": "Doctor appointment",
  "description": "Annual checkup",
  "start_time": "2025-06-18T14:00:00Z",
  "end_time": "2025-06-18T15:00:00Z",
  "event_type": "external",
  "is_blocking": true
}
```

**Required Fields:**
- `title` (string)
- `start_time` (ISO 8601 timestamp)
- `end_time` (ISO 8601 timestamp)

**Optional Fields:**
- `description` (string)
- `event_type` (string): `internal`, `external`, `task`, `social`
  - Default: `internal`
- `is_blocking` (boolean)
  - Default: `true`

**Response:**
```json
{
  "event": {
    "id": "uuid",
    ...
  }
}
```

#### DELETE /api/calendar/:id

Delete a calendar event.

**Response:**
```json
{
  "message": "Deleted successfully"
}
```

---

### Relationships

#### GET /api/relationships

List all relationships.

**Response:**
```json
{
  "relationships": [
    {
      "id": "uuid",
      "user_id": "uuid",
      "name": "Sarah",
      "relationship_type": "partner",
      "priority": 1,
      "time_budget_hours": 14.0,
      "last_interaction": "2025-06-16T18:00:00.000Z",
      "emotional_impact_last": "positive",
      "notes": "Weekly date night on Fridays",
      "created_at": "2025-06-01T00:00:00.000Z",
      "updated_at": "2025-06-16T00:00:00.000Z"
    }
  ]
}
```

#### POST /api/relationships

Add a new relationship.

**Request:**
```json
{
  "name": "John",
  "relationship_type": "friend",
  "priority": 3,
  "time_budget_hours": 4.0,
  "notes": "College friend, monthly meetups"
}
```

**Required Fields:**
- `name` (string)
- `relationship_type` (enum): `partner`, `friend`, `family`, `other`
- `priority` (integer 1-5)

**Optional Fields:**
- `time_budget_hours` (decimal)
- `notes` (string)

**Response:**
```json
{
  "relationship": {
    "id": "uuid",
    ...
  }
}
```

#### DELETE /api/relationships/:id

Delete a relationship.

**Response:**
```json
{
  "message": "Deleted successfully"
}
```

---

### Overrides

#### GET /api/overrides

Check weekly override status.

**Response:**
```json
{
  "overrides": {
    "count": 2,
    "remaining": 3,
    "limit": 5,
    "canOverride": true
  }
}
```

#### PUT /api/override-plan/:id

Log a manual override of a plan.

**Request:**
```json
{
  "override_type": "manual_reschedule",
  "reason": "Unexpected urgent task"
}
```

**Response (Success):**
```json
{
  "message": "Override logged",
  "overrides": {
    "count": 3,
    "remaining": 2,
    "limit": 5,
    "canOverride": true
  }
}
```

**Response (Limit Reached):**
```json
{
  "error": "Weekly override limit reached (5)",
  "overrides": {
    "count": 5,
    "remaining": 0,
    "limit": 5,
    "canOverride": false
  }
}
```
Status: `403 Forbidden`

---

## Error Responses

All errors follow this format:

```json
{
  "error": "Error message describing what went wrong"
}
```

### Common HTTP Status Codes

- `200 OK` - Successful request
- `400 Bad Request` - Invalid input
- `401 Unauthorized` - User not initialized
- `403 Forbidden` - Override limit reached
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

---

## Rate Limiting

Not currently implemented in v0. Consider adding for production:

```javascript
import rateLimit from 'express-rate-limit';

const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // limit each IP to 100 requests per windowMs
});
```

---

## CORS

Enabled for all origins in development:

```javascript
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
Access-Control-Allow-Headers: Content-Type, Authorization
```

For production, restrict to specific origins:

```env
CORS_ORIGINS=https://yourdomain.com
```

---

## Example Usage (curl)

### Initialize System
```bash
curl -X POST http://localhost:3000/api/init \
  -H "Content-Type: application/json" \
  -d '{"username":"user","password":"password"}'
```

### Create Goal
```bash
curl -X POST http://localhost:3000/api/goals \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Learn Spanish",
    "priority": 3,
    "priority_reasoning": "Long-term personal development goal",
    "target_date": "2025-12-31"
  }'
```

### Create Task
```bash
curl -X POST http://localhost:3000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Practice Spanish vocabulary",
    "priority": 3,
    "priority_reasoning": "Daily practice required for language learning",
    "estimated_duration": 30
  }'
```

### Generate Plan
```bash
curl -X POST http://localhost:3000/api/generate-plan \
  -H "Content-Type: application/json" \
  -d '{"date": "2025-06-17"}'
```

### Get Today's Plan
```bash
curl http://localhost:3000/api/plans
```

### Mark Task Complete
```bash
curl -X PUT http://localhost:3000/api/tasks/TASK_ID \
  -H "Content-Type: application/json" \
  -d '{"status": "completed", "actual_duration": 28}'
```

---

## Example Usage (JavaScript)

### Frontend Integration

```javascript
// Get all goals
async function getGoals() {
  const response = await fetch('/api/goals');
  const data = await response.json();
  return data.goals;
}

// Create new task
async function createTask(taskData) {
  const response = await fetch('/api/tasks', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(taskData),
  });
  const data = await response.json();
  return data.task;
}

// Generate plan
async function generatePlan(date) {
  const response = await fetch('/api/generate-plan', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ date }),
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error);
  }
  
  const data = await response.json();
  return data.plan;
}

// Check override status
async function checkOverrides() {
  const response = await fetch('/api/overrides');
  const data = await response.json();
  return data.overrides;
}
```

---

## Webhooks (Future)

Not implemented in v0, but you could add:

### POST /api/webhooks/calendar-sync
Receive external calendar updates

### POST /api/webhooks/task-completed
Trigger on task completion

---

## Batch Operations (Future)

Not implemented in v0, but you could add:

### POST /api/batch/tasks
Create multiple tasks at once

### PUT /api/batch/tasks
Update multiple tasks at once

---

## Export/Import (Future)

Not implemented in v0, but you could add:

### GET /api/export
Export all user data as JSON

### POST /api/import
Import data from JSON

---

**API is stable and ready for client integration.**

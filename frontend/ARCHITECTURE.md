# MetaConscious v0 - Technical Architecture

In-depth technical documentation for developers who want to understand, modify, or extend the system.

---

## 🏛️ System Overview

MetaConscious is an autonomous AI planning system built on three core principles:

1. **Authority**: The AI has final say over scheduling decisions
2. **Modularity**: Components can be replaced without affecting others
3. **Transparency**: All decisions have explicit reasoning

---

## 📐 Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend Layer                       │
│  Next.js Client (React) + shadcn/ui + Tailwind CSS    │
└────────────────────┬────────────────────────────────────┘
                     │
                     │ HTTP/JSON API
                     ▼
┌─────────────────────────────────────────────────────────┐
│                   API Layer (Next.js)                   │
│  Route Handlers: /api/goals, /api/tasks, /api/plans    │
└─────┬───────────────────────────────────────────┬───────┘
      │                                           │
      │                                           │
      ▼                                           ▼
┌─────────────────────┐              ┌────────────────────┐
│  Planning Engine    │              │   LLM Client       │
│  (Isolated Logic)   │◄────────────►│   (Swappable)      │
└──────┬──────────────┘              └────────┬───────────┘
       │                                      │
       │                                      │
       │                                      ▼
       │                            ┌─────────────────────┐
       │                            │   External LLM      │
       │                            │   (Groq/OpenAI)     │
       │                            └─────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────┐
│              Database Layer (PostgreSQL)                │
│  Tables: users, goals, tasks, plans, calendar, etc.    │
└─────────────────────────────────────────────────────────┘
       ▲
       │
       │
┌──────┴──────────────────┐
│  Scheduler (Node-cron)  │
│  Nightly Planning Trigger│
└─────────────────────────┘
```

---

## 🗂️ Project Structure

```
/app
├── lib/                          # Core business logic
│   ├── db/                       # Database layer
│   │   ├── schema.sql           # PostgreSQL schema definition
│   │   └── db.js                # Connection pool & query utilities
│   │
│   ├── llm/                      # LLM abstraction layer
│   │   └── llm-client.js        # OpenAI-compatible client wrapper
│   │
│   └── planner/                  # Planning engine (CORE)
│       ├── planner.js           # Main planning logic (REWRITABLE)
│       ├── schemas.js           # Zod validation schemas
│       └── scheduler.js         # Cron job for nightly planning
│
├── app/                          # Next.js app directory
│   ├── api/[[...path]]/         # API routes (catch-all pattern)
│   │   └── route.js             # All API endpoints
│   ├── page.js                  # Main UI (client component)
│   ├── layout.js                # Root layout
│   └── globals.css              # Global styles
│
├── components/ui/                # shadcn/ui components
├── .env                          # Environment configuration
├── package.json                  # Dependencies
└── README.md                     # User documentation
```

---

## 🔌 Component Descriptions

### 1. Database Layer (`lib/db/`)

**Purpose**: Abstraction over PostgreSQL with connection pooling.

**Key Files**:
- `schema.sql`: Complete database schema with indexes
- `db.js`: Query wrapper and connection management

**Design Decisions**:
- Single connection pool shared across requests
- All queries use parameterized statements (SQL injection protection)
- Simple helper functions for common operations

**Extension Points**:
```javascript
// Add new query helpers in db.js
async function getActiveGoalsWithTasks(userId) {
  const result = await query(`
    SELECT g.*, array_agg(t.id) as task_ids
    FROM goals g
    LEFT JOIN goal_tasks gt ON g.id = gt.goal_id
    LEFT JOIN tasks t ON gt.task_id = t.id
    WHERE g.user_id = $1 AND g.status = 'active'
    GROUP BY g.id
  `, [userId]);
  return result.rows;
}
```

### 2. LLM Client (`lib/llm/llm-client.js`)

**Purpose**: Abstraction layer for LLM API calls. Swappable providers without code changes.

**Key Features**:
- OpenAI SDK under the hood (compatible with Groq, OpenAI, local models)
- Config-driven model selection
- JSON mode support
- Retry logic built-in

**Provider Configuration**:
```javascript
class LLMClient {
  constructor() {
    this.provider = process.env.LLM_PROVIDER;
    this.apiKey = process.env.LLM_API_KEY;
    this.model = process.env.LLM_MODEL;
    this.baseURL = process.env.LLM_BASE_URL;
  }
}
```

**Adding New Providers**:
1. Add provider-specific logic in constructor
2. Override `complete()` method if needed
3. Update prompt templates in `getPlanningSystemPrompt()`

**Example - Adding Anthropic**:
```javascript
if (this.provider === 'anthropic') {
  // Custom Anthropic SDK initialization
  this.client = new Anthropic({ apiKey: this.apiKey });
}
```

### 3. Planning Engine (`lib/planner/planner.js`)

**Purpose**: CORE LOGIC. Generates daily plans based on context.

**Key Methods**:

```javascript
class PlanningEngine {
  // Main entry point
  async generateDailyPlan(userId, targetDate)
  
  // Gather all context for planning
  async gatherPlanningContext(userId, targetDate)
  
  // Save generated plan
  async savePlan(userId, planDate, plan)
  
  // Reschedule task and regenerate plan
  async rescheduleTask(userId, taskId, newDate, reason)
  
  // Check weekly override limit
  async checkWeeklyOverrides(userId)
  
  // Log manual override
  async logOverride(userId, planId, overrideType, reason)
}
```

**Planning Flow**:
```
1. gatherPlanningContext()
   ├─ Active goals (max 5)
   ├─ Pending tasks
   ├─ Tomorrow's calendar events
   ├─ Relationships with time budgets
   └─ Recent performance metrics

2. llmClient.generatePlan(context)
   ├─ Send structured prompt
   ├─ Receive JSON response
   └─ Retry on failure (max 3 attempts)

3. validatePlan(rawPlan)
   └─ Zod schema validation

4. savePlan()
   └─ Upsert to daily_plans table
```

**Design Philosophy**:
- **Isolated**: Can be completely rewritten without touching API or UI
- **Stateless**: No internal state, all data from DB
- **Testable**: Each method can be unit tested
- **Extensible**: Add new context sources easily

**Customization Example**:
```javascript
// Override planning logic
class CustomPlanningEngine extends PlanningEngine {
  async gatherPlanningContext(userId, targetDate) {
    const context = await super.gatherPlanningContext(userId, targetDate);
    
    // Add weather data
    context.weather = await getWeatherForecast(targetDate);
    
    // Add sleep data
    context.sleep = await getSleepQuality(userId);
    
    return context;
  }
}
```

### 4. Validation Schemas (`lib/planner/schemas.js`)

**Purpose**: Zod schemas for LLM output validation.

**Why This Matters**:
- LLMs are non-deterministic
- Invalid output must be caught before saving
- Provides clear error messages for debugging

**Schema Structure**:
```javascript
export const DailyPlanSchema = z.object({
  date: z.string().regex(/^\d{4}-\d{2}-\d{2}$/),
  reasoning: z.string().min(10),
  priority_analysis: z.string().min(10),
  time_blocks: z.array(TimeBlockSchema),
  social_time_allocation: SocialTimeSchema,
  goal_progress_assessment: z.array(GoalProgressSchema),
  warnings: z.array(z.string()),
});
```

**Adding New Fields**:
```javascript
export const DailyPlanSchema = z.object({
  // ... existing fields
  energy_level_estimate: z.enum(['low', 'medium', 'high']),
  focus_time_blocks: z.array(z.object({
    start: z.string(),
    end: z.string(),
  })),
});
```

### 5. Scheduler (`lib/planner/scheduler.js`)

**Purpose**: Background job for nightly autonomous planning.

**Implementation**:
```javascript
const cron = require('node-cron');

export async function startPlanningScheduler() {
  const planningHour = process.env.PLANNING_HOUR || '2';
  const cronExpression = `0 ${planningHour} * * *`;
  
  cron.schedule(cronExpression, async () => {
    const planner = new PlanningEngine();
    const user = await getUser();
    const tomorrow = getTomorrowDate();
    
    await planner.generateDailyPlan(user.id, tomorrow);
  });
}
```

**Alternative Implementations**:
- Replace with Bull Queue for more control
- Use Vercel Cron Jobs if deploying to Vercel
- Integrate with external schedulers (AWS EventBridge, etc.)

### 6. API Layer (`app/api/[[...path]]/route.js`)

**Purpose**: RESTful API endpoints for all operations.

**Routing Pattern**:
```javascript
// Catch-all route: /api/[...path]
export async function GET(request, { params }) {
  const pathParts = params?.path || [];
  const resource = pathParts[0]; // goals, tasks, plans, etc.
  
  switch (resource) {
    case 'goals': return handleGoals();
    case 'tasks': return handleTasks();
    // ...
  }
}
```

**Authentication**:
Simple single-user check:
```javascript
const user = await getUser();
if (!user) {
  return NextResponse.json({ error: 'User not initialized' }, { status: 401 });
}
```

**CORS Headers**:
```javascript
function corsHeaders() {
  return {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization',
  };
}
```

**Adding New Endpoints**:
```javascript
case 'analytics':
  const analyticsResult = await query(`
    SELECT 
      COUNT(*) as total_tasks,
      AVG(actual_duration) as avg_duration
    FROM tasks
    WHERE user_id = $1 AND status = 'completed'
  `, [userId]);
  return NextResponse.json({ analytics: analyticsResult.rows[0] });
```

### 7. Frontend (`app/page.js`)

**Purpose**: Text-first dashboard for viewing and managing data.

**Component Structure**:
```javascript
export default function App() {
  // State management
  const [goals, setGoals] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [plan, setPlan] = useState(null);
  
  // Data loading
  useEffect(() => {
    initializeApp();
  }, []);
  
  // API calls
  async function createGoal(formData) { ... }
  async function generatePlan() { ... }
  
  // UI rendering
  return (
    <Tabs>
      <TabsContent value="daily">...</TabsContent>
      <TabsContent value="goals">...</TabsContent>
      <TabsContent value="tasks">...</TabsContent>
    </Tabs>
  );
}
```

**Design Philosophy**:
- Minimal polish, maximum functionality
- Text-first (no fancy graphics)
- Clear information hierarchy
- shadcn/ui for consistent components

---

## 🗄️ Database Schema Deep Dive

### Core Tables

**users**
```sql
id           UUID PRIMARY KEY
username     VARCHAR(100) UNIQUE
password_hash VARCHAR(255)
created_at   TIMESTAMP
```

**goals** (max 3-5 active)
```sql
id                  UUID PRIMARY KEY
user_id            UUID REFERENCES users
title              TEXT
description        TEXT
priority           INTEGER (1-5)
priority_reasoning TEXT (REQUIRED)
status             VARCHAR(20) -- active, completed, paused
target_date        DATE
```

**tasks**
```sql
id                 UUID PRIMARY KEY
user_id           UUID REFERENCES users
title             TEXT
description       TEXT
priority          INTEGER (1-5)
priority_reasoning TEXT (REQUIRED)
status            VARCHAR(20) -- pending, in_progress, completed, cancelled
estimated_duration INTEGER (minutes)
actual_duration   INTEGER (minutes)
due_date          DATE
completed_at      TIMESTAMP
```

**goal_tasks** (many-to-many)
```sql
goal_id UUID REFERENCES goals
task_id UUID REFERENCES tasks
PRIMARY KEY (goal_id, task_id)
```

**daily_plans**
```sql
id           UUID PRIMARY KEY
user_id     UUID REFERENCES users
plan_date   DATE
plan_json   JSONB (full plan structure)
reasoning   TEXT
generated_at TIMESTAMP
modified_at  TIMESTAMP
is_override  BOOLEAN
UNIQUE(user_id, plan_date)
```

**calendar_events**
```sql
id          UUID PRIMARY KEY
user_id    UUID REFERENCES users
title      TEXT
description TEXT
start_time TIMESTAMP
end_time   TIMESTAMP
event_type VARCHAR(20) -- internal, external, task, social
is_blocking BOOLEAN
external_id VARCHAR(255) -- for calendar sync
```

**relationships**
```sql
id                    UUID PRIMARY KEY
user_id              UUID REFERENCES users
name                 VARCHAR(255)
relationship_type    VARCHAR(50) -- partner, friend, family, other
priority             INTEGER (1-5)
time_budget_hours    DECIMAL(5,2) -- weekly budget
last_interaction     TIMESTAMP
emotional_impact_last TEXT
notes                TEXT
```

**override_log**
```sql
id                UUID PRIMARY KEY
user_id          UUID REFERENCES users
plan_id          UUID REFERENCES daily_plans
override_type    VARCHAR(50)
override_reason  TEXT
override_timestamp TIMESTAMP
week_number      INTEGER
```

### Memory Systems (Scaffolded)

**contextual_memory**
- Stores context-aware information
- Relevance scoring for retrieval
- Not actively used in v0

**procedural_memory**
- Learned procedures and patterns
- Success/failure tracking
- Not actively used in v0

**long_term_memory**
- Historical patterns
- Importance scoring
- Not actively used in v0

---

## 🔄 Data Flow Examples

### Creating a Task

```
1. Frontend Form Submission
   POST /api/tasks
   {
     "title": "Write report",
     "priority": 2,
     "priority_reasoning": "Deadline approaching",
     "estimated_duration": 120
   }

2. API Handler
   - Validates input
   - Checks user authentication
   - Inserts into tasks table

3. Database
   INSERT INTO tasks (user_id, title, priority, ...)
   VALUES ($1, $2, $3, ...)
   RETURNING *

4. Response
   { "task": { id: "...", title: "...", ... } }

5. Frontend Update
   - Adds task to local state
   - Re-renders task list
```

### Generating a Plan

```
1. Trigger
   - Manual: POST /api/generate-plan
   - Automatic: Cron job at configured hour

2. Planning Engine
   a) gatherPlanningContext()
      - Query goals: SELECT * FROM goals WHERE status='active'
      - Query tasks: SELECT * FROM tasks WHERE status='pending'
      - Query events: SELECT * FROM calendar_events WHERE ...
      - Query relationships: SELECT * FROM relationships
      - Calculate performance: AVG(actual_duration/estimated_duration)

3. LLM Integration
   a) Build prompt with context
   b) Call LLM API
      POST https://api.groq.com/openai/v1/chat/completions
      {
        "model": "mixtral-8x7b-32768",
        "messages": [
          { "role": "system", "content": "..." },
          { "role": "user", "content": "..." }
        ],
        "response_format": { "type": "json_object" }
      }
   c) Parse JSON response

4. Validation
   - Run through Zod schema
   - Retry if invalid (max 3 attempts)
   - Throw error if all attempts fail

5. Storage
   INSERT INTO daily_plans (user_id, plan_date, plan_json, reasoning)
   VALUES ($1, $2, $3, $4)
   ON CONFLICT (user_id, plan_date) DO UPDATE ...

6. Response/Notification
   - Return plan to frontend
   - Log success/failure
```

---

## 🔐 Security Considerations

### Current Implementation (Single-User)

- Simple SHA-256 password hashing
- No session management
- Local database only
- No rate limiting

### Production Recommendations

1. **Authentication**
   - Use bcrypt for password hashing
   - Implement JWT or session tokens
   - Add refresh token mechanism

2. **Database**
   - Enable SSL connections
   - Use strong passwords
   - Limit PostgreSQL network access
   - Regular backups

3. **API**
   - Rate limiting (express-rate-limit)
   - Input validation (Zod everywhere)
   - CSRF protection
   - Helmet.js for headers

4. **LLM**
   - Rotate API keys regularly
   - Monitor usage/costs
   - Implement spending limits
   - Validate all LLM outputs

---

## 🧪 Testing Strategies

### Unit Tests
```javascript
// Example: Test planning context gathering
describe('PlanningEngine', () => {
  it('should gather all context for planning', async () => {
    const engine = new PlanningEngine();
    const context = await engine.gatherPlanningContext(userId, '2025-06-17');
    
    expect(context.goals).toBeDefined();
    expect(context.tasks).toBeDefined();
    expect(context.calendarEvents).toBeDefined();
    expect(context.relationships).toBeDefined();
  });
});
```

### Integration Tests
```javascript
// Example: Test full plan generation flow
describe('Plan Generation', () => {
  it('should generate valid plan from end to end', async () => {
    // Create test data
    await createTestGoal();
    await createTestTask();
    
    // Generate plan
    const response = await fetch('/api/generate-plan', {
      method: 'POST',
      body: JSON.stringify({ date: '2025-06-17' })
    });
    
    const { plan } = await response.json();
    expect(plan.time_blocks).toBeDefined();
    expect(plan.reasoning).toBeDefined();
  });
});
```

### Manual API Tests
See SETUP.md for curl commands.

---

## 📊 Performance Considerations

### Database Optimization

1. **Indexes** (already implemented)
   ```sql
   CREATE INDEX idx_goals_user_status ON goals(user_id, status);
   CREATE INDEX idx_tasks_user_status ON tasks(user_id, status);
   CREATE INDEX idx_daily_plans_user_date ON daily_plans(user_id, plan_date);
   ```

2. **Connection Pooling**
   ```javascript
   const pool = new Pool({
     max: 20,
     idleTimeoutMillis: 30000,
     connectionTimeoutMillis: 2000,
   });
   ```

3. **Query Optimization**
   - Use `EXPLAIN ANALYZE` for slow queries
   - Avoid N+1 queries with JOINs
   - Limit result sets

### LLM Optimization

1. **Prompt Engineering**
   - Keep prompts concise
   - Provide structured format examples
   - Use temperature=0.7 for balance

2. **Caching**
   - Cache similar planning contexts
   - Reuse recent plans if context unchanged

3. **Cost Management**
   - Use Groq for free tier
   - Switch to cheaper models for non-critical tasks
   - Implement spending alerts

---

## 🔧 Extension Examples

### Adding Weather Integration

```javascript
// lib/integrations/weather.js
export async function getWeatherForecast(date) {
  const response = await fetch(`https://api.weather.com/forecast?date=${date}`);
  return response.json();
}

// lib/planner/planner.js
async gatherPlanningContext(userId, targetDate) {
  const context = await super.gatherPlanningContext(userId, targetDate);
  context.weather = await getWeatherForecast(targetDate);
  return context;
}
```

### Adding Email Notifications

```javascript
// lib/notifications/email.js
export async function sendPlanEmail(user, plan) {
  await sendEmail({
    to: user.email,
    subject: `Your plan for ${plan.date}`,
    body: formatPlanAsEmail(plan),
  });
}

// lib/planner/scheduler.js
cron.schedule(cronExpression, async () => {
  const plan = await planner.generateDailyPlan(user.id, tomorrow);
  await sendPlanEmail(user, plan);
});
```

### Adding Google Calendar Sync

```javascript
// lib/integrations/google-calendar.js
export async function syncGoogleCalendar(userId) {
  const events = await fetchGoogleEvents(userId);
  
  for (const event of events) {
    await query(`
      INSERT INTO calendar_events (user_id, title, start_time, end_time, external_id, event_type)
      VALUES ($1, $2, $3, $4, $5, 'external')
      ON CONFLICT (external_id) DO UPDATE SET ...
    `, [userId, event.title, event.start, event.end, event.id]);
  }
}
```

---

## 📝 Code Style & Conventions

### Naming
- **Variables**: camelCase
- **Functions**: camelCase
- **Classes**: PascalCase
- **Constants**: UPPER_SNAKE_CASE
- **Database**: snake_case

### File Structure
- One class per file
- Group related functions
- Export at bottom

### Error Handling
```javascript
try {
  const result = await query('SELECT * FROM ...');
  return result.rows;
} catch (error) {
  console.error('Database error:', error);
  throw new Error('Failed to fetch data');
}
```

### Comments
- Explain WHY, not WHAT
- Document complex logic
- Add TODOs for future work

---

## 🚀 Deployment Architecture

### Single Server (Development)
```
┌─────────────────────────┐
│  Single Machine         │
│  ├─ PostgreSQL (5432)   │
│  ├─ Next.js (3000)      │
│  └─ Node-cron scheduler │
└─────────────────────────┘
```

### Production (Scalable)
```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Load        │────▶│  Next.js     │────▶│  PostgreSQL  │
│  Balancer    │     │  Instances   │     │  (RDS/etc)   │
└──────────────┘     └──────────────┘     └──────────────┘
                            │
                            ▼
                     ┌──────────────┐
                     │  Separate    │
                     │  Scheduler   │
                     │  Instance    │
                     └──────────────┘
```

---

## 🎓 Learning Resources

### Technologies Used
- **Next.js**: https://nextjs.org/docs
- **PostgreSQL**: https://www.postgresql.org/docs/
- **shadcn/ui**: https://ui.shadcn.com
- **Zod**: https://zod.dev
- **OpenAI API**: https://platform.openai.com/docs
- **Groq**: https://console.groq.com/docs

### Design Patterns
- Repository Pattern (database layer)
- Strategy Pattern (LLM providers)
- Factory Pattern (planning engine)
- Observer Pattern (scheduler)

---

**System is ready for extension, modification, and improvement.**

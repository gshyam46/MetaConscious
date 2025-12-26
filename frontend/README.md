# MetaConscious v0

**Autonomous AI Planning & Productivity System**

MetaConscious is a private, single-user productivity system where an AI has **FINAL AUTHORITY** over scheduling, planning, and prioritization. This is NOT a chatbot—it's an autonomous planning engine that generates daily schedules, manages priorities, and enforces trade-offs.

---

## 🎯 Core Philosophy

- **System Authority**: The AI makes scheduling decisions autonomously
- **No Non-Negotiables**: Everything is a trade-off
- **Override Limits**: Manual changes are tracked and capped weekly
- **Science-Based**: Factual, confrontational tone—no generic motivation
- **Private & Self-Hosted**: Single user, completely open source

---

## 🏗️ Architecture

### Tech Stack
- **Frontend**: Next.js 14 + shadcn/ui + Tailwind CSS
- **Backend**: Next.js API Routes
- **Database**: PostgreSQL 15
- **LLM Layer**: OpenAI-compatible API (Groq default, swappable)
- **Scheduler**: Node-cron for autonomous nightly planning

### Project Structure
```
/app
├── lib/
│   ├── db/
│   │   ├── schema.sql          # PostgreSQL schema
│   │   └── db.js               # Database utilities
│   ├── llm/
│   │   └── llm-client.js       # LLM abstraction (SWAPPABLE)
│   └── planner/
│       ├── planner.js          # Core planning logic (ISOLATED)
│       ├── schemas.js          # Zod validation schemas
│       └── scheduler.js        # Background job scheduler
├── app/
│   ├── api/[[...path]]/route.js  # API routes
│   ├── page.js                   # Frontend UI
│   └── layout.js
└── .env                          # Configuration
```

---

## 🚀 Quick Start

### 1. Prerequisites
- Node.js 18+
- PostgreSQL 15+
- LLM API key (Groq recommended, OpenAI compatible)

### 2. Environment Setup

Edit `.env`:
```bash
# PostgreSQL (already configured)
DATABASE_URL=postgresql://mcuser:mcpassword@localhost:5432/metaconscious

# LLM Configuration (REQUIRED for planning)
LLM_PROVIDER=groq
LLM_API_KEY=your_groq_api_key_here
LLM_MODEL=mixtral-8x7b-32768
LLM_BASE_URL=https://api.groq.com/openai/v1

# System Configuration
MAX_WEEKLY_OVERRIDES=5
PLANNING_HOUR=2  # Nightly planning at 2 AM
```

### 3. Start the System
```bash
# Install dependencies
yarn install

# Start server (runs on port 3000)
yarn dev
```

### 4. Initialize User
```bash
curl -X POST http://localhost:3000/api/init \
  -H "Content-Type: application/json" \
  -d '{"username":"user","password":"password"}'
```

---

## 📖 API Reference

### System
- `GET /api/status` - System status and LLM config check
- `POST /api/init` - Initialize single user

### Goals (Max 3-5 Active)
- `GET /api/goals` - List all goals
- `POST /api/goals` - Create goal (requires priority_reasoning)
- `PUT /api/goals/:id` - Update goal
- `DELETE /api/goals/:id` - Delete goal

### Tasks
- `GET /api/tasks?status=pending` - List tasks
- `POST /api/tasks` - Create task (requires priority_reasoning)
- `PUT /api/tasks/:id` - Update task
- `DELETE /api/tasks/:id` - Delete task

### Plans
- `GET /api/plans?date=YYYY-MM-DD` - Get plan for date
- `POST /api/generate-plan` - Generate new plan (LLM required)

### Calendar
- `GET /api/calendar?start=YYYY-MM-DD` - Get events
- `POST /api/calendar` - Create event

### Relationships
- `GET /api/relationships` - List relationships
- `POST /api/relationships` - Add relationship

### Overrides
- `GET /api/overrides` - Check weekly override status
- `PUT /api/override-plan/:id` - Log manual override

---

## 🤖 How Planning Works

### Nightly Autonomous Process
1. **Trigger**: Runs daily at configured hour (default 2 AM)
2. **Context Gathering**: Collects goals, tasks, calendar, relationships, performance
3. **LLM Generation**: Sends structured prompt, receives JSON plan
4. **Validation**: Zod schema ensures plan structure is valid
5. **Storage**: Saves to database, accessible next day

### Plan Structure
```json
{
  "date": "YYYY-MM-DD",
  "reasoning": "Why this plan makes sense",
  "priority_analysis": "Trade-offs and decisions",
  "time_blocks": [
    {
      "start_time": "09:00",
      "end_time": "11:00",
      "task_id": "uuid",
      "activity": "Description",
      "priority": 1,
      "reasoning": "Why this slot"
    }
  ],
  "social_time_allocation": {
    "total_minutes": 120,
    "reasoning": "Why this amount"
  },
  "goal_progress_assessment": [...],
  "warnings": ["List of concerns"]
}
```

### Authority & Overrides
- System generates plans without user approval
- User can manually override up to **5 times per week** (configurable)
- Overrides are logged and tracked
- Social time is automatically reduced if goals are threatened

---

## 🔧 LLM Provider Configuration

### Groq (Default - Free Tier Available)
```env
LLM_PROVIDER=groq
LLM_API_KEY=gsk_...
LLM_MODEL=mixtral-8x7b-32768
LLM_BASE_URL=https://api.groq.com/openai/v1
```

### OpenAI
```env
LLM_PROVIDER=openai
LLM_API_KEY=sk-...
LLM_MODEL=gpt-4
LLM_BASE_URL=https://api.openai.com/v1
```

### Other OpenAI-Compatible APIs
Any API compatible with OpenAI's format will work. Just update the `LLM_BASE_URL`.

---

## 📊 Database Schema

### Core Tables
- **users**: Single user authentication
- **goals**: Long-term objectives (max 3-5 active)
- **tasks**: Actionable items with priority reasoning
- **daily_plans**: AI-generated schedules
- **calendar_events**: Internal + external events
- **relationships**: Social connections with time budgets
- **override_log**: Manual override tracking

### Memory Systems (Scaffolded)
- **contextual_memory**: Context-aware data (passive)
- **procedural_memory**: Learned procedures (passive)
- **long_term_memory**: Historical patterns (passive)

**Note**: Memory systems are data models only. No active learning is implemented in v0.

---

## 🛠️ Extension Points

### Modular Design
The system is built for easy modification:

1. **Planner Logic** (`lib/planner/planner.js`)
   - Isolated module, can be completely rewritten
   - Only interface: `generateDailyPlan(userId, date)`
   
2. **LLM Client** (`lib/llm/llm-client.js`)
   - Swappable provider via config
   - Add new providers by extending the class

3. **Scheduler** (`lib/planner/scheduler.js`)
   - Simple cron-based trigger
   - Replace with any job queue system

4. **Behavioral Tracking** (Scaffolded)
   - Phone usage, meals, spending tables exist
   - Ingestion logic not implemented

5. **Calendar Sync** (Scaffolded)
   - Two-way sync interface prepared
   - Integration code pending

---

## 🚧 TODOs for Future Versions

### v0.1 - Refinements
- [ ] Implement behavioral data ingestion
- [ ] Add calendar sync (Google/Outlook)
- [ ] Improve LLM prompt engineering
- [ ] Add weekly/monthly plan views
- [ ] Performance tracking dashboard

### v0.2 - Intelligence
- [ ] Active learning for memory systems
- [ ] Pattern recognition from user behavior
- [ ] Predictive task duration estimation
- [ ] Adaptive priority adjustment

### v0.3 - Advanced Features
- [ ] Multi-goal dependency tracking
- [ ] Conflict resolution algorithms
- [ ] Historical performance analytics
- [ ] Export/backup functionality

---

## 🧪 Testing

### Manual API Tests
```bash
# Check status
curl http://localhost:3000/api/status

# Create goal
curl -X POST http://localhost:3000/api/goals \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Example Goal",
    "priority": 1,
    "priority_reasoning": "Critical for project success"
  }'

# Generate plan (requires LLM_API_KEY)
curl -X POST http://localhost:3000/api/generate-plan \
  -H "Content-Type: application/json" \
  -d '{"date": "2025-06-17"}'
```

---

## 📝 Design Decisions

### Why PostgreSQL?
- Robust JSONB support for flexible plan storage
- Strong ACID guarantees for critical scheduling data
- Excellent performance for single-user workload

### Why Next.js API Routes (Not FastAPI)?
- Simplified deployment (single service)
- Easier development in existing Next.js environment
- Same functionality, less infrastructure complexity
- API endpoints can still be extracted to FastAPI later if needed

### Why Groq Default?
- Fast inference (critical for nightly planning)
- Free tier available for personal use
- OpenAI-compatible API (easy to swap)
- Good performance on planning tasks

### Why No Frontend Polish?
- v0 focuses on **functionality over aesthetics**
- Text-first interface keeps focus on data
- Easy to redesign UI without touching logic
- Minimal distraction from core features

---

## 🔐 Security Notes

### Single-User System
- Simple SHA-256 password hashing (sufficient for personal use)
- No JWT/session complexity needed
- Database credentials are local-only

### Production Recommendations
If deploying publicly:
- Use bcrypt for password hashing
- Add proper authentication middleware
- Enable PostgreSQL SSL connections
- Set strong DB passwords
- Use environment variable management tools

---

## 📜 License

**Free and Open Source**
- Use for personal or commercial projects
- Modify as needed
- Self-host anywhere
- No vendor lock-in

---

## 🤝 Contributing

This is v0—expect rough edges. Contributions welcome:
- Bug fixes
- Documentation improvements
- LLM prompt enhancements
- Additional provider integrations

---

## ⚠️ Important Notes

1. **LLM API Key Required**: Planning features won't work without it
2. **Nightly Scheduler**: Only runs if server is running at configured hour
3. **Override Limits**: Enforced to maintain system authority
4. **Memory Systems**: Scaffolded only, no active learning in v0
5. **Calendar Sync**: Prepared but not implemented

---

## 🎓 Philosophy Deep-Dive

### Why Authority Matters
Traditional productivity apps are assistants—they suggest, recommend, wait for approval. MetaConscious is different: it **decides**.

This creates accountability:
- The system must justify its decisions (priority_reasoning)
- Users must justify overrides (logged and limited)
- Trade-offs are explicit, not hidden

### Why Confrontational?
Generic motivation ("You can do it!") is meaningless. MetaConscious uses:
- Factual performance data
- Science-based insights
- Direct communication about trade-offs
- Explicit warnings when goals are at risk

### Why Trade-Offs?
There are no non-negotiables because:
- Time is finite
- Energy is limited
- Every choice has consequences
- Pretending otherwise is counterproductive

---

## 🆘 Troubleshooting

### "User not initialized"
Run: `curl -X POST http://localhost:3000/api/init -H "Content-Type: application/json" -d '{}'`

### "LLM not configured"
Add `LLM_API_KEY` to `.env` and restart server

### Database connection errors
Check PostgreSQL is running: `sudo service postgresql status`

### Plan generation fails
- Verify LLM API key is valid
- Check Groq API status
- Review logs: `tail -f /var/log/supervisor/nextjs.out.log`

---

**Built with focus. Ready for iteration.**

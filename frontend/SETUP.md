# MetaConscious v0 - Setup Guide

Complete setup instructions for getting MetaConscious running on your local machine or server.

---

## 📋 Prerequisites

Before you begin, ensure you have:

- **Node.js 18+** and **yarn** package manager
- **PostgreSQL 15+** installed and running
- **LLM API Key** (Groq recommended for free tier, or OpenAI)
- Basic command line knowledge

---

## 🚀 Installation Steps

### 1. Clone or Download the Project

```bash
cd /path/to/your/workspace
# Project should be in /app directory
```

### 2. Install Dependencies

```bash
cd /app
yarn install
```

This will install all required packages including:
- Next.js 14
- PostgreSQL client (pg)
- OpenAI SDK
- shadcn/ui components
- Node-cron for scheduling

### 3. Set Up PostgreSQL

#### Install PostgreSQL (if not already installed)

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib
sudo service postgresql start
```

**macOS (Homebrew):**
```bash
brew install postgresql@15
brew services start postgresql@15
```

#### Create Database and User

```bash
# Connect as postgres user
sudo -u postgres psql

# In PostgreSQL shell:
CREATE DATABASE metaconscious;
CREATE USER mcuser WITH PASSWORD 'mcpassword';
GRANT ALL PRIVILEGES ON DATABASE metaconscious TO mcuser;
ALTER DATABASE metaconscious OWNER TO mcuser;
\q
```

#### Initialize Schema

```bash
cd /app
sudo -u postgres psql -d metaconscious -f lib/db/schema.sql
sudo -u postgres psql -d metaconscious -c "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO mcuser;"
sudo -u postgres psql -d metaconscious -c "GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO mcuser;"
```

### 4. Configure Environment Variables

Edit `/app/.env`:

```env
# PostgreSQL Configuration
DATABASE_URL=postgresql://mcuser:mcpassword@localhost:5432/metaconscious

# LLM Configuration (REQUIRED for autonomous planning)
LLM_PROVIDER=groq
LLM_API_KEY=your_actual_api_key_here
LLM_MODEL=mixtral-8x7b-32768
LLM_BASE_URL=https://api.groq.com/openai/v1

# System Configuration
MAX_WEEKLY_OVERRIDES=5
PLANNING_HOUR=2

# Next.js Configuration (already set)
NEXT_PUBLIC_BASE_URL=http://localhost:3000
CORS_ORIGINS=*
```

**⚠️ IMPORTANT:** Replace `your_actual_api_key_here` with your real API key!

### 5. Get Your LLM API Key

#### Option A: Groq (Recommended - Free Tier)

1. Go to [https://console.groq.com](https://console.groq.com)
2. Sign up for a free account
3. Navigate to API Keys
4. Create a new API key
5. Copy and paste into `.env` file

**Groq Configuration:**
```env
LLM_PROVIDER=groq
LLM_API_KEY=gsk_...
LLM_MODEL=mixtral-8x7b-32768
LLM_BASE_URL=https://api.groq.com/openai/v1
```

#### Option B: OpenAI

1. Go to [https://platform.openai.com](https://platform.openai.com)
2. Create API key
3. Add credits to your account

**OpenAI Configuration:**
```env
LLM_PROVIDER=openai
LLM_API_KEY=sk-...
LLM_MODEL=gpt-4o-mini
LLM_BASE_URL=https://api.openai.com/v1
```

### 6. Start the Application

```bash
cd /app
yarn dev
```

The server will start on `http://localhost:3000`

### 7. Initialize Your User

Open a new terminal and run:

```bash
curl -X POST http://localhost:3000/api/init \
  -H "Content-Type: application/json" \
  -d '{"username":"user","password":"password"}'
```

Expected response:
```json
{
  "message": "User created",
  "user": {
    "id": "...",
    "username": "user"
  }
}
```

### 8. Verify Installation

```bash
curl http://localhost:3000/api/status
```

Expected response:
```json
{
  "status": "operational",
  "user": { "id": "...", "username": "user" },
  "llm_configured": true
}
```

✅ **If `llm_configured` is `true`, you're ready to go!**

---

## 🧪 Testing the System

### Create Your First Goal

```bash
curl -X POST http://localhost:3000/api/goals \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Complete work project",
    "description": "Finish the Q2 deliverables",
    "priority": 1,
    "priority_reasoning": "Critical deadline with high stakeholder visibility",
    "target_date": "2025-06-30"
  }'
```

### Create Your First Task

```bash
curl -X POST http://localhost:3000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Review quarterly reports",
    "description": "Analyze team performance metrics",
    "priority": 2,
    "priority_reasoning": "Important for planning next quarter priorities",
    "estimated_duration": 90,
    "due_date": "2025-06-18"
  }'
```

### Generate Your First Plan

```bash
curl -X POST http://localhost:3000/api/generate-plan \
  -H "Content-Type: application/json" \
  -d '{"date": "2025-06-17"}'
```

This will use the LLM to generate an autonomous plan based on your goals and tasks.

---

## 🌐 Access the Web Interface

Open your browser and navigate to:

```
http://localhost:3000
```

You'll see:
- **Today's Plan** tab - View AI-generated daily schedule
- **Goals** tab - Manage long-term objectives (max 5)
- **Tasks** tab - Create and track actionable items
- **Social** tab - Relationship time management

---

## 🤖 Autonomous Planning Schedule

The system automatically generates plans nightly at the configured hour (default 2 AM).

### How It Works:

1. **Cron Job**: Runs daily at `PLANNING_HOUR`
2. **Context**: Gathers goals, tasks, calendar, relationships
3. **LLM Call**: Sends structured prompt to configured LLM
4. **Validation**: Ensures plan meets schema requirements
5. **Storage**: Saves to database for next day

### Manual Plan Generation:

You can trigger planning manually anytime:
- Via UI: Click "Generate Plan" button in Today's Plan tab
- Via API: `POST /api/generate-plan`

---

## 📝 Configuration Options

### Scheduler Configuration

Edit `.env` to change when plans are generated:

```env
PLANNING_HOUR=2  # 2 AM (24-hour format)
```

### Override Limits

Control how many times per week users can manually override plans:

```env
MAX_WEEKLY_OVERRIDES=5
```

### Database Configuration

If you changed PostgreSQL credentials:

```env
DATABASE_URL=postgresql://username:password@host:port/database
```

---

## 🔧 Troubleshooting

### "Connection refused" to PostgreSQL

**Check if PostgreSQL is running:**
```bash
sudo service postgresql status
# or
pg_isready
```

**Start PostgreSQL:**
```bash
sudo service postgresql start
```

### "LLM not configured" in UI

1. Check `.env` file has `LLM_API_KEY` set
2. Verify API key is valid
3. Restart server: `yarn dev`

### Database permission errors

```bash
sudo -u postgres psql -d metaconscious -c "
  ALTER DATABASE metaconscious OWNER TO mcuser;
  GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO mcuser;
  GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO mcuser;
"
```

### Port 3000 already in use

Kill the process:
```bash
lsof -ti:3000 | xargs kill -9
```

Or change the port in `package.json`:
```json
"dev": "next dev --hostname 0.0.0.0 --port 3001"
```

### Schema already exists error

If you need to reset the database:
```bash
sudo -u postgres psql -d metaconscious -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
sudo -u postgres psql -d metaconscious -f lib/db/schema.sql
```

---

## 🚢 Production Deployment

### Environment Checklist

- [ ] Set strong PostgreSQL password
- [ ] Enable PostgreSQL SSL
- [ ] Use environment variable manager (dotenv-vault, etc.)
- [ ] Set `NODE_ENV=production`
- [ ] Configure proper CORS origins
- [ ] Set up backup strategy
- [ ] Monitor LLM API usage/costs

### Build for Production

```bash
cd /app
yarn build
yarn start
```

### Process Management

Use PM2 or systemd to keep the server running:

```bash
# PM2
npm install -g pm2
pm2 start yarn --name metaconscious -- start

# Or systemd
sudo nano /etc/systemd/system/metaconscious.service
```

---

## 📊 Database Management

### Backup Database

```bash
pg_dump -U mcuser metaconscious > backup_$(date +%Y%m%d).sql
```

### Restore Database

```bash
psql -U mcuser metaconscious < backup_20250617.sql
```

### View Database Contents

```bash
sudo -u postgres psql metaconscious

# In PostgreSQL shell:
\dt                    # List all tables
SELECT * FROM users;   # View users
SELECT * FROM goals;   # View goals
SELECT * FROM tasks;   # View tasks
```

---

## 🎛️ Advanced Configuration

### Custom LLM Provider

Any OpenAI-compatible API works. Example with local Ollama:

```env
LLM_PROVIDER=ollama
LLM_API_KEY=not-needed
LLM_MODEL=mixtral
LLM_BASE_URL=http://localhost:11434/v1
```

### Disable Nightly Planning

Comment out scheduler initialization in `/app/api/[[...path]]/route.js`:

```javascript
// await startPlanningScheduler();
```

### Change Scheduling Algorithm

The planning logic is isolated in `/app/lib/planner/planner.js`. You can:
- Modify prompts
- Change validation rules
- Add custom scheduling logic
- Integrate external calendar APIs

---

## 📚 Next Steps

Now that you're set up:

1. **Add More Data**: Create multiple goals and tasks
2. **Generate Plans**: Test the autonomous planning
3. **Track Performance**: Complete tasks and see how the system adapts
4. **Set Relationships**: Add people with time budgets
5. **Monitor Overrides**: Stay within weekly limits

---

## ⚠️ Important Notes

- **Data Privacy**: All data stays on your machine
- **API Costs**: Monitor your LLM provider usage
- **Backups**: Set up automated database backups
- **Updates**: Check for schema changes in future versions

---

## 🆘 Getting Help

If you encounter issues:

1. Check logs: `tail -f /var/log/supervisor/nextjs.out.log` (if using supervisor)
2. Review this guide thoroughly
3. Verify all prerequisites are met
4. Check PostgreSQL and Node.js versions

---

**System is ready. Let MetaConscious take control of your schedule.**

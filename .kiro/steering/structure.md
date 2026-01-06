# MetaConscious Project Structure

## Root Directory Layout
```
/app                          # Next.js application root
├── lib/                      # Core business logic (isolated modules)
├── app/                      # Next.js App Router directory
├── components/ui/            # shadcn/ui components
├── hooks/                    # Custom React hooks
├── tests/                    # Test files
├── .env                      # Environment configuration
├── package.json              # Dependencies and scripts
└── *.config.js               # Build configuration files
```

## Core Library Structure (`/lib`)
**Critical**: All business logic lives here, isolated from UI concerns.

```
lib/
├── db/
│   ├── schema.sql           # PostgreSQL schema definition
│   └── db.js                # Database connection and query utilities
├── llm/
│   └── llm-client.js        # LLM abstraction layer (swappable providers)
└── planner/
    ├── planner.js           # Core planning engine (REWRITABLE)
    ├── schemas.js           # Zod validation schemas
    └── scheduler.js         # Background job scheduler
```

## App Router Structure (`/app`)
```
app/
├── api/[[...path]]/         # Catch-all API routes
│   └── route.js             # All REST endpoints in single file
├── page.js                  # Main dashboard UI
├── layout.js                # Root layout with fonts/providers
└── globals.css              # Global styles and CSS variables
```

## Component Organization
- **UI Components**: `/components/ui/` (shadcn/ui managed)
- **Custom Hooks**: `/hooks/` (reusable React logic)
- **Utilities**: `/lib/utils.js` (shared helper functions)

## Configuration Files
- **next.config.js**: Next.js build configuration with CORS headers
- **tailwind.config.js**: Tailwind CSS theme and component styles
- **jsconfig.json**: Path aliases for imports (`@/lib/*`, `@/components/*`)
- **components.json**: shadcn/ui configuration
- **postcss.config.js**: CSS processing pipeline

## Database Schema Organization
**Single file approach**: All tables in `lib/db/schema.sql`

### Core Tables
- `users` - Single user authentication
- `goals` - Long-term objectives (max 3-5 active)
- `tasks` - Actionable items with priority reasoning
- `daily_plans` - AI-generated schedules (JSONB storage)
- `calendar_events` - Internal + external events
- `relationships` - Social connections with time budgets
- `override_log` - Manual override tracking

### Memory Systems (Scaffolded)
- `contextual_memory` - Context-aware data
- `procedural_memory` - Learned procedures
- `long_term_memory` - Historical patterns

## Import Path Conventions
```javascript
// Absolute imports using jsconfig.json aliases
import { PlanningEngine } from '@/lib/planner/planner';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

// Relative imports for same directory
import { validatePlan } from './schemas';
```

## File Naming Conventions
- **Components**: PascalCase (`Button.jsx`)
- **Utilities**: kebab-case (`llm-client.js`)
- **Hooks**: kebab-case with prefix (`use-mobile.jsx`)
- **Config**: kebab-case (`next.config.js`)

## Extension Points
**Modular design allows easy replacement**:

1. **Planning Engine** (`lib/planner/planner.js`)
   - Isolated module, complete rewrite possible
   - Interface: `generateDailyPlan(userId, date)`

2. **LLM Client** (`lib/llm/llm-client.js`)
   - Provider-agnostic wrapper
   - Add new providers via configuration

3. **Database Layer** (`lib/db/db.js`)
   - Simple query wrapper
   - Easy to extend with new operations

## Development Workflow
1. **Business Logic**: Start in `/lib` modules
2. **API Endpoints**: Add to `/app/api/[[...path]]/route.js`
3. **UI Components**: Use shadcn/ui in `/components/ui`
4. **Database Changes**: Update `schema.sql` and migration scripts
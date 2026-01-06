# MetaConscious Tech Stack

## Framework & Runtime
- **Next.js 14**: Full-stack React framework with App Router
- **Node.js 18+**: JavaScript runtime
- **React 18**: Frontend library with Server Components

## Database
- **PostgreSQL 15+**: Primary database with JSONB support for flexible plan storage
- **Connection Pooling**: Built-in PostgreSQL connection management

## UI & Styling
- **shadcn/ui**: Component library (New York style)
- **Tailwind CSS**: Utility-first CSS framework
- **Radix UI**: Headless UI primitives
- **Lucide React**: Icon library
- **Sonner**: Toast notifications

## LLM Integration
- **OpenAI SDK**: Compatible client for multiple providers
- **Groq**: Default LLM provider (free tier available)
- **Swappable Providers**: OpenAI, Groq, or any OpenAI-compatible API

## Key Dependencies
- **Zod**: Schema validation for LLM outputs
- **node-cron**: Background job scheduling
- **axios**: HTTP client
- **react-hook-form**: Form management
- **date-fns**: Date utilities

## Build System & Package Management
- **Yarn**: Package manager (v1.22.22)
- **PostCSS**: CSS processing
- **Autoprefixer**: CSS vendor prefixes

## Common Commands

### Development
```bash
# Start development server
yarn dev

# Start without hot reload (performance)
yarn dev:no-reload

# Build for production
yarn build

# Start production server
yarn start
```

### Database Setup
```bash
# Initialize PostgreSQL database
psql -U postgres -c "CREATE DATABASE metaconscious;"
psql -U postgres -d metaconscious -f lib/db/schema.sql
```

### Environment Configuration
Required `.env` variables:
```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/metaconscious

# LLM (required for planning)
LLM_PROVIDER=groq
LLM_API_KEY=your_api_key
LLM_MODEL=mixtral-8x7b-32768
LLM_BASE_URL=https://api.groq.com/openai/v1

# System
MAX_WEEKLY_OVERRIDES=5
PLANNING_HOUR=2
```

## Architecture Patterns
- **Modular Design**: Isolated planning engine, swappable LLM client
- **API-First**: RESTful endpoints with catch-all routing
- **Single Responsibility**: Each module has clear, focused purpose
- **Configuration-Driven**: Environment variables for all external dependencies
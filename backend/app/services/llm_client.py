
"""
LLM abstraction layer using LiteLLM
Provider: Groq
Maintains identical interface and behavior to original LLMClient
"""

import json
import logging
import asyncio
import uuid
from datetime import datetime, date
from typing import Dict, Any, Optional

from litellm import acompletion

from app.core.config import settings
from app.core.exceptions import LLMError

logger = logging.getLogger(__name__)


# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------

def safe_json_dumps(obj, **kwargs):
    """JSON dumps with UUID and datetime serialization support"""
    def default_serializer(o):
        if isinstance(o, uuid.UUID):
            return str(o)
        if isinstance(o, (datetime, date)):
            return o.isoformat()
        raise TypeError(f"Object of type {type(o)} is not JSON serializable")

    return json.dumps(obj, default=default_serializer, **kwargs)


# -------------------------------------------------------------------
# LLM Client
# -------------------------------------------------------------------

class LLMClient:
    """
    Async-safe LiteLLM client for Groq.
    No env mutation. No OpenAI assumptions.
    """

    def __init__(self):
        self.provider = settings.llm_provider        # groq
        self.api_key = settings.llm_api_key
        self.base_model = settings.llm_model
        self.base_url = settings.llm_base_url

        self.max_retries = 3
        self.retry_delay = 1.0

        if not self.api_key:
            raise LLMError("LLM_API_KEY not configured")

        # Final LiteLLM model format
        # groq/llama-3.3-70b-versatile
        if "/" in self.base_model:
            self.model = self.base_model
        else:
            self.model = f"{self.provider}/{self.base_model}"

        logger.info(
            "LLMClient initialized | provider=%s model=%s",
            self.provider,
            self.model,
        )

    # -------------------------------------------------------------------
    # Core completion
    # -------------------------------------------------------------------

    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        options: Optional[Dict[str, Any]] = None,
    ) -> str:
        if options is None:
            options = {}

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        params = {
            "model": self.model,
            "messages": messages,
            "api_key": self.api_key,  # ✅ explicit key, no env mutation
            "temperature": options.get("temperature", 0.7),
            "max_tokens": options.get("maxTokens", 2000),
        }

        # Best-effort JSON mode
        if options.get("jsonMode"):
            params["response_format"] = {"type": "json_object"}

        last_error = None

        for attempt in range(self.max_retries):
            try:
                logger.info(
                    "LLM call attempt %d/%d | model=%s",
                    attempt + 1,
                    self.max_retries,
                    self.model,
                )

                response = await acompletion(**params)
                content = response.choices[0].message.content

                logger.info(
                    "LLM call successful | response_length=%d",
                    len(content),
                )
                return content

            except Exception as error:
                last_error = error
                logger.error(
                    "LLM error on attempt %d/%d: %s",
                    attempt + 1,
                    self.max_retries,
                    str(error),
                )

                error_str = str(error).lower()
                retryable = any(code in error_str for code in [
                    "rate limit",
                    "timeout",
                    "connection",
                    "network",
                    "temporary",
                    "service unavailable",
                    "429",
                    "502",
                    "503",
                    "504",
                ])

                if not retryable or attempt == self.max_retries - 1:
                    break

                delay = self.retry_delay * (2 ** attempt)
                await asyncio.sleep(delay)

        raise LLMError(
            f"LLM API call failed after {self.max_retries} attempts",
            last_error,
        )

    # -------------------------------------------------------------------
    # Planning (unchanged behavior)
    # -------------------------------------------------------------------

    async def generate_plan(
        self,
        context: Dict[str, Any],
        options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if options is None:
            options = {}

        system_prompt = self.get_planning_system_prompt()
        user_prompt = self.build_planning_prompt(context)

        options["jsonMode"] = True

        try:
            response = await self.complete(system_prompt, user_prompt, options)
            return json.loads(response)

        except json.JSONDecodeError as error:
            logger.error("Invalid JSON returned by LLM: %s", response)
            raise LLMError("LLM returned invalid JSON", error)

        except Exception as error:
            raise LLMError("Plan generation failed", error)

    # -------------------------------------------------------------------
    # Prompts
    # -------------------------------------------------------------------

    def get_planning_system_prompt(self) -> str:
        """Get the system prompt for planning operations"""
        return """You are MetaConscious, an autonomous AI planning system with FINAL AUTHORITY over scheduling and prioritization.

Your role:
- Analyze user performance data and context
- Generate optimized daily plans
- Make priority decisions based on goals and constraints
- Reschedule tasks when conflicts occur
- Reduce social time if goals are threatened

Your tone:
- Factual and confrontational
- Science-based, no generic motivation
- Direct about trade-offs and consequences

You MUST return valid JSON with this exact structure:
{
  "date": "YYYY-MM-DD",
  "reasoning": "explicit reasoning for this plan",
  "priority_analysis": "analysis of current priorities and trade-offs",
  "time_blocks": [
    {
      "start_time": "HH:MM",
      "end_time": "HH:MM",
      "task_id": "uuid or null",
      "activity": "description",
      "priority": 1-5,
      "reasoning": "why this time slot"
    }
  ],
  "social_time_allocation": {
    "total_minutes": 120,
    "reasoning": "why this amount"
  },
  "goal_progress_assessment": [
    {
      "goal_id": "uuid",
      "status": "on_track|at_risk|blocked",
      "action_needed": "description"
    }
  ],
  "warnings": ["list of concerns or conflicts"]
}"""
    
    def build_planning_prompt(self, context: Dict[str, Any]) -> str:
        """Build the user prompt for planning with context data"""
        return f"""Generate tomorrow's plan based on this context:

DATE: {context.get('date', 'Not specified')}

ACTIVE GOALS:
{safe_json_dumps(context.get('goals', []), indent=2)}

PENDING TASKS:
{safe_json_dumps(context.get('tasks', []), indent=2)}

CALENDAR EVENTS (TOMORROW):
{safe_json_dumps(context.get('calendarEvents', []), indent=2)}

RELATIONSHIPS & TIME BUDGETS:
{safe_json_dumps(context.get('relationships', []), indent=2)}

RECENT PERFORMANCE:
{safe_json_dumps(context.get('recentPerformance', {}), indent=2)}

CONSTRAINTS:
- Max 3-5 active goals
- Social time has hard cap
- Everything is a trade-off
- No non-negotiables

Generate the optimal plan for tomorrow."""




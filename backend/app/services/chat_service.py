"""
Context-aware chat service for MetaConscious AI assistant
Provides intelligent responses based on user's actual planning data
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, date

from .llm_client import LLMClient
from .planning_engine import PlanningEngine
from ..core.database import query
from ..core.exceptions import LLMError

logger = logging.getLogger(__name__)

class ChatService:
    """Context-aware chat service that integrates with user's planning data"""
    
    def __init__(self):
        self.llm_client = LLMClient()
        self.planning_engine = PlanningEngine()
        
    async def process_message(self, user_id: str, message: str) -> Dict[str, Any]:
        """
        Process user message with full context awareness
        
        Args:
            user_id: User identifier
            message: User's chat message
            
        Returns:
            Chat response with AI reply and potential actions
        """
        try:
            # Gather current user context
            context = await self.gather_user_context(user_id)
            
            # Check if message is requesting plan generation
            if self._is_plan_generation_request(message):
                return await self._handle_plan_generation(user_id, message, context)
            
            # Check if message contains project/goal information that should be structured
            if self._contains_project_information(message):
                return await self._handle_project_structuring(user_id, message, context)
            
            # Build context-aware prompt
            system_prompt = self._build_system_prompt()
            user_prompt = self._build_context_aware_prompt(message, context)
            
            # Get AI response
            response = await self.llm_client.complete(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                options={"temperature": 0.7, "maxTokens": 500}
            )
            
            return {
                "response": response,
                "timestamp": datetime.utcnow().isoformat(),
                "actions": [],
                "context_used": {
                    "goals_count": len(context.get("goals", [])),
                    "tasks_count": len(context.get("tasks", [])),
                    "has_plan": context.get("current_plan") is not None,
                    "override_status": context.get("override_status", {})
                },
                "plan_updated": False
            }
            
        except LLMError as e:
            logger.error(f"LLM error in chat processing: {e}")
            return {
                "response": "I'm temporarily having trouble processing your request. Please try again in a moment.",
                "timestamp": datetime.utcnow().isoformat(),
                "actions": [],
                "context_used": None,
                "plan_updated": False
            }
        except Exception as e:
            logger.error(f"Unexpected error in chat processing: {e}")
            return {
                "response": "I encountered an unexpected issue. Please try again.",
                "timestamp": datetime.utcnow().isoformat(),
                "actions": [],
                "context_used": None,
                "plan_updated": False
            }
    
    async def gather_user_context(self, user_id: str) -> Dict[str, Any]:
        """
        Gather current user context for AI responses
        
        Args:
            user_id: User identifier
            
        Returns:
            Dictionary containing user's current goals, tasks, plans, etc.
        """
        try:
            # Get active goals
            goals_result = await query(
                """SELECT id, title, description, priority, priority_reasoning, target_date, status
                   FROM goals 
                   WHERE user_id = $1 AND status = 'active' 
                   ORDER BY priority DESC 
                   LIMIT 5""",
                [user_id]
            )
            
            # Get pending tasks
            tasks_result = await query(
                """SELECT id, title, description, priority, priority_reasoning, 
                          estimated_duration, due_date, status
                   FROM tasks 
                   WHERE user_id = $1 AND status IN ('pending', 'in_progress')
                   ORDER BY priority DESC, due_date ASC
                   LIMIT 10""",
                [user_id]
            )
            
            # Get current plan (today's plan)
            today = datetime.now().date()
            plan_result = await query(
                """SELECT plan_json, reasoning, plan_date, modified_at
                   FROM daily_plans 
                   WHERE user_id = $1 AND plan_date = $2""",
                [user_id, today]
            )
            
            # Get override status
            override_status = await self.planning_engine.check_weekly_overrides(user_id)
            
            # Get relationships
            relationships_result = await query(
                """SELECT id, name, relationship_type, priority, time_budget_hours
                   FROM relationships
                   WHERE user_id = $1
                   ORDER BY priority DESC
                   LIMIT 5""",
                [user_id]
            )
            
            return {
                "goals": goals_result or [],
                "tasks": tasks_result or [],
                "current_plan": plan_result[0] if plan_result else None,
                "override_status": override_status,
                "relationships": relationships_result or [],
                "context_timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error gathering user context: {e}")
            return {
                "goals": [],
                "tasks": [],
                "current_plan": None,
                "override_status": {"count": 0, "remaining": 5, "limit": 5, "canOverride": True},
                "relationships": [],
                "context_timestamp": datetime.utcnow().isoformat()
            }
    
    def _contains_project_information(self, message: str) -> bool:
        """Check if message contains project/goal information that should be structured"""
        project_indicators = [
            "i have to", "i need to", "project", "build", "finish", "complete",
            "mvp", "research paper", "portfolio", "website", "interview prep",
            "certification", "deadline", "months", "priority"
        ]
        message_lower = message.lower()
        return any(indicator in message_lower for indicator in project_indicators) and len(message.split()) > 10
    
    async def _handle_project_structuring(self, user_id: str, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle messages that contain project information and structure them into goals/tasks"""
        try:
            # Use LLM to extract structured goals and tasks from the message
            structure_prompt = f"""You are MetaConscious, an autonomous AI planning system. The user has described their projects and goals. Extract and structure this information into specific goals and tasks with priorities.

User message: "{message}"

Based on this message, create a structured plan with:
1. Main goals (3-5 maximum) with priorities 1-5 and reasoning
2. Key tasks for each goal with priorities and estimated durations
3. Suggested deadlines based on the user's timeline

Return ONLY valid JSON in this exact format:
{{
  "goals": [
    {{
      "title": "Goal title",
      "description": "Detailed description",
      "priority": 1-5,
      "priority_reasoning": "Why this priority is justified",
      "target_date": "YYYY-MM-DD or null"
    }}
  ],
  "tasks": [
    {{
      "title": "Task title", 
      "description": "Task description",
      "priority": 1-5,
      "priority_reasoning": "Why this priority",
      "estimated_duration": 60,
      "due_date": "YYYY-MM-DD or null",
      "goal_relation": "Which goal this supports"
    }}
  ],
  "reasoning": "Overall reasoning for priorities and timeline"
}}

Guidelines:
- Priority 5 = Critical/Urgent (job search deadline)
- Priority 4 = High (major projects with deadlines)  
- Priority 3 = Medium (important but flexible)
- Priority 2 = Low (nice to have)
- Priority 1 = Optional (can be deferred)
- Estimate realistic durations in minutes
- Consider the 3-month job search deadline as highest priority driver"""

            response = await self.llm_client.complete(
                system_prompt="You are a planning assistant that extracts structured information from user messages.",
                user_prompt=structure_prompt,
                options={"temperature": 0.3, "maxTokens": 1000, "jsonMode": True}
            )
            
            import json
            structured_data = json.loads(response)
            
            # Format the response for user approval
            goals_summary = "\n".join([
                f"• {goal['title']} (Priority {goal['priority']}): {goal['priority_reasoning']}"
                for goal in structured_data.get('goals', [])
            ])
            
            tasks_summary = "\n".join([
                f"• {task['title']} (Priority {task['priority']}, {task.get('estimated_duration', 'N/A')}min): {task['priority_reasoning']}"
                for task in structured_data.get('tasks', [])[:8]  # Show first 8 tasks
            ])
            
            response_text = f"""I've analyzed your projects and structured them into goals and tasks. Here's what I propose:

**GOALS:**
{goals_summary}

**KEY TASKS:**
{tasks_summary}

**REASONING:**
{structured_data.get('reasoning', 'Prioritized based on your 3-month job search deadline.')}

Would you like me to create these goals and tasks in your system? I can also regenerate today's plan to incorporate these new priorities."""

            return {
                "response": response_text,
                "timestamp": datetime.utcnow().isoformat(),
                "actions": [
                    {
                        "type": "create_structured_plan",
                        "label": "Create Goals & Tasks",
                        "data": structured_data
                    },
                    {
                        "type": "create_and_plan",
                        "label": "Create & Generate Plan",
                        "data": {**structured_data, "regenerate_plan": True}
                    }
                ],
                "context_used": context,
                "plan_updated": False
            }
            
        except Exception as e:
            logger.error(f"Error in project structuring: {e}")
            return {
                "response": f"I can see you have multiple important projects to manage. Let me help you structure them properly. Could you tell me more about your top 3 priorities and their deadlines?",
                "timestamp": datetime.utcnow().isoformat(),
                "actions": [],
                "context_used": context,
                "plan_updated": False
            }
        """Check if message is requesting plan generation"""
        plan_keywords = [
            "generate plan", "create plan", "make plan", "plan my day",
            "schedule my day", "plan today", "plan tomorrow", "generate schedule"
        ]
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in plan_keywords)
    
    async def _handle_plan_generation(self, user_id: str, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle plan generation requests through chat"""
        try:
            # Check if plan already exists for today
            if context.get("current_plan"):
                plan_date = context["current_plan"]["plan_date"]
                modified_at = context["current_plan"]["modified_at"]
                
                # If plan was created/modified today, suggest using existing plan
                if isinstance(modified_at, datetime) and modified_at.date() == datetime.now().date():
                    return {
                        "response": f"I already generated a plan for {plan_date} today. You can view it in the 'Today's Plan' tab. Would you like me to regenerate it or would you prefer to see the current plan first?",
                        "timestamp": datetime.utcnow().isoformat(),
                        "actions": [
                            {
                                "type": "view_plan",
                                "label": "View Current Plan",
                                "data": {"plan_date": str(plan_date)}
                            },
                            {
                                "type": "regenerate_plan", 
                                "label": "Regenerate Plan",
                                "data": {"plan_date": str(datetime.now().date())}
                            }
                        ],
                        "context_used": context,
                        "plan_updated": False
                    }
            
            # Generate new plan
            today_str = datetime.now().strftime('%Y-%m-%d')
            plan = await self.planning_engine.generate_daily_plan(user_id, today_str)
            
            return {
                "response": f"I've generated a new daily plan for today! The plan includes {len(plan.get('time_blocks', []))} scheduled activities. You can view the complete plan in the 'Today's Plan' tab. The plan prioritizes your {len(context.get('goals', []))} active goals and {len(context.get('tasks', []))} pending tasks.",
                "timestamp": datetime.utcnow().isoformat(),
                "actions": [
                    {
                        "type": "view_plan",
                        "label": "View Generated Plan",
                        "data": {"plan_date": today_str}
                    }
                ],
                "context_used": context,
                "plan_updated": True
            }
            
        except Exception as e:
            logger.error(f"Error handling plan generation: {e}")
            return {
                "response": "I encountered an issue while generating your plan. Please try using the 'Generate Plan' button in the Today's Plan tab, or check that your LLM configuration is correct.",
                "timestamp": datetime.utcnow().isoformat(),
                "actions": [],
                "context_used": context,
                "plan_updated": False
            }
    
    def _build_system_prompt(self) -> str:
        """Build system prompt for context-aware chat"""
        return """You are MetaConscious, an autonomous AI planning assistant with FINAL AUTHORITY over scheduling and prioritization.

Your role in chat:
- Help users understand their current planning situation based on their actual data
- Provide specific advice about their goals, tasks, and schedule
- Explain your autonomous planning decisions with clear reasoning
- Be direct and factual, not motivational
- Always consider trade-offs and constraints
- Reference the user's actual data when giving advice

Your tone:
- Professional and slightly confrontational when needed
- Science-based, no generic motivation
- Direct about trade-offs and consequences
- Authoritative about scheduling decisions

Key principles:
- Everything is a trade-off with explicit reasoning
- No non-negotiables - system has final authority
- Override limits are enforced (max 5 per week)
- Social time has hard caps
- Max 3-5 active goals at any time

When discussing plans or schedules, always reference the user's actual current situation."""
    
    def _build_context_aware_prompt(self, message: str, context: Dict[str, Any]) -> str:
        """Build context-aware prompt with user's actual data"""
        
        # Format goals
        goals_summary = ""
        if context.get("goals"):
            goals_summary = f"\nACTIVE GOALS ({len(context['goals'])}):\n"
            for goal in context["goals"][:3]:  # Show top 3
                goals_summary += f"- {goal['title']} (Priority {goal['priority']}): {goal['priority_reasoning']}\n"
        else:
            goals_summary = "\nACTIVE GOALS: None currently set"
        
        # Format tasks
        tasks_summary = ""
        if context.get("tasks"):
            tasks_summary = f"\nPENDING TASKS ({len(context['tasks'])}):\n"
            for task in context["tasks"][:5]:  # Show top 5
                duration = f" ({task['estimated_duration']}min)" if task.get('estimated_duration') else ""
                due = f" - Due: {task['due_date']}" if task.get('due_date') else ""
                tasks_summary += f"- {task['title']} (P{task['priority']}){duration}{due}\n"
        else:
            tasks_summary = "\nPENDING TASKS: None currently"
        
        # Format current plan
        plan_summary = ""
        if context.get("current_plan"):
            plan_date = context["current_plan"]["plan_date"]
            plan_summary = f"\nCURRENT PLAN: Generated for {plan_date}"
            if context["current_plan"].get("reasoning"):
                plan_summary += f"\nPlan reasoning: {context['current_plan']['reasoning'][:200]}..."
        else:
            plan_summary = "\nCURRENT PLAN: No plan generated yet"
        
        # Format override status
        override_info = context.get("override_status", {})
        override_summary = f"\nOVERRIDE STATUS: {override_info.get('count', 0)}/{override_info.get('limit', 5)} used this week"
        
        return f"""User message: "{message}"

CURRENT USER CONTEXT:{goals_summary}{tasks_summary}{plan_summary}{override_summary}

Provide a helpful response based on their actual current situation. Reference specific goals, tasks, or plans when relevant. If they're asking about something not in their current data, let them know and suggest how to add it."""
    
    def _is_plan_generation_request(self, message: str) -> bool:
        """Check if message is requesting plan generation"""
        plan_keywords = [
            "generate plan", "create plan", "make plan", "plan my day",
            "schedule my day", "plan today", "plan tomorrow", "generate schedule"
        ]
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in plan_keywords)
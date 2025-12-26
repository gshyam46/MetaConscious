"""
Background job scheduler for nightly planning using APScheduler
Identical functionality to Next.js node-cron implementation
"""
import os
import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from ..core.database import get_user
from .planning_engine import PlanningEngine

logger = logging.getLogger(__name__)

class PlanningScheduler:
    """Planning scheduler using APScheduler - identical to Next.js implementation"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.scheduler_started = False
        self.planning_engine = PlanningEngine()
    
    async def start_planning_scheduler(self) -> None:
        """
        Start planning scheduler with same cron expressions and timing as Next.js
        Implements singleton pattern identical to Next.js version
        """
        if self.scheduler_started:
            logger.info('Scheduler already running')
            return
        
        planning_hour = int(os.environ.get('PLANNING_HOUR', '2'))
        
        # Create cron trigger identical to Next.js: `0 ${planningHour} * * *`
        trigger = CronTrigger(hour=planning_hour, minute=0)
        
        # Add the nightly planning job
        self.scheduler.add_job(
            self._nightly_planning_job,
            trigger=trigger,
            id='nightly_planning',
            name='Nightly Planning Job',
            replace_existing=True
        )
        
        # Start the scheduler
        self.scheduler.start()
        self.scheduler_started = True
        
        logger.info(f"Planning scheduler started: runs daily at {planning_hour:02d}:00")
    
    async def _nightly_planning_job(self) -> None:
        """
        Nightly planning job with identical logic to Next.js version
        """
        logger.info(f"Running nightly planning at {datetime.now().isoformat()}")
        
        try:
            # Get user (same logic as Next.js)
            user = await get_user()
            if not user:
                logger.info('No user found, skipping planning')
                return
            
            # Calculate tomorrow's date (same logic as Next.js)
            tomorrow = datetime.now() + timedelta(days=1)
            target_date = tomorrow.strftime('%Y-%m-%d')
            
            # Generate plan using PlanningEngine
            plan = await self.planning_engine.generate_daily_plan(user['id'], target_date)
            logger.info(f"Plan generated successfully for {target_date}")
            
        except Exception as error:
            logger.error(f'Nightly planning failed: {error}')
    
    def stop_planning_scheduler(self) -> None:
        """
        Stop planning scheduler with same logic as Next.js version
        """
        if self.scheduler.is_running:
            self.scheduler.shutdown()
        
        self.scheduler_started = False
        logger.info('Planning scheduler stopped')
    
    def is_running(self) -> bool:
        """Check if scheduler is running"""
        return self.scheduler_started and self.scheduler.running

# Global scheduler instance (singleton pattern like Next.js)
_scheduler_instance = None

async def start_planning_scheduler() -> None:
    """
    Global function to start planning scheduler - matches Next.js export
    Implements singleton pattern identical to Next.js version
    """
    global _scheduler_instance
    
    if _scheduler_instance is None:
        _scheduler_instance = PlanningScheduler()
    
    await _scheduler_instance.start_planning_scheduler()

def stop_planning_scheduler() -> None:
    """
    Global function to stop planning scheduler - matches Next.js export
    """
    global _scheduler_instance
    
    if _scheduler_instance is not None:
        _scheduler_instance.stop_planning_scheduler()

def get_scheduler_status() -> dict:
    """Get scheduler status for monitoring"""
    global _scheduler_instance
    
    if _scheduler_instance is None:
        return {
            'running': False,
            'planning_hour': int(os.environ.get('PLANNING_HOUR', '2')),
            'next_run': None
        }
    
    next_run = None
    if _scheduler_instance.scheduler.running:
        job = _scheduler_instance.scheduler.get_job('nightly_planning')
        if job and job.next_run_time:
            next_run = job.next_run_time.isoformat()
    
    return {
        'running': _scheduler_instance.is_running(),
        'planning_hour': int(os.environ.get('PLANNING_HOUR', '2')),
        'next_run': next_run
    }
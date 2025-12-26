"""
Migration Orchestrator
Coordinates the complete migration from Next.js to FastAPI backend
"""
import asyncio
import sys
import os
import json
from pathlib import Path
from typing import Dict, List, Optional
import subprocess
import time

from frontend_config_updater import FrontendConfigUpdater
from nextjs_cleanup import NextJSCleanup
from test_runner import TestRunner

class MigrationOrchestrator:
    """Orchestrates the complete migration process"""
    
    def __init__(self, frontend_dir: str = "../app", backend_dir: str = "."):
        self.frontend_dir = Path(frontend_dir)
        self.backend_dir = Path(backend_dir)
        self.migration_state = {
            'phase': 'not_started',
            'completed_steps': [],
            'failed_steps': [],
            'rollback_info': {}
        }
        self.state_file = self.backend_dir / "migration_state.json"
        
        # Initialize components
        self.frontend_updater = FrontendConfigUpdater(str(self.frontend_dir))
        self.nextjs_cleanup = NextJSCleanup(str(self.frontend_dir))
        self.test_runner = TestRunner()
        
        # Load existing state if available
        self.load_migration_state()
    
    def save_migration_state(self):
        """Save current migration state"""
        try:
            with open(self.state_file, 'w') as f:
                json.dump(self.migration_state, f, indent=2, default=str)
        except Exception as e:
            print(f"Warning: Could not save migration state: {e}")
    
    def load_migration_state(self):
        """Load migration state from file"""
        try:
            if self.state_file.exists():
                with open(self.state_file, 'r') as f:
                    self.migration_state = json.load(f)
                print(f"Loaded migration state: {self.migration_state['phase']}")
        except Exception as e:
            print(f"Warning: Could not load migration state: {e}")
    
    def update_phase(self, phase: str, step: str = None, success: bool = True):
        """Update migration phase and step status"""
        self.migration_state['phase'] = phase
        
        if step:
            if success:
                if step not in self.migration_state['completed_steps']:
                    self.migration_state['completed_steps'].append(step)
                # Remove from failed if it was there
                if step in self.migration_state['failed_steps']:
                    self.migration_state['failed_steps'].remove(step)
            else:
                if step not in self.migration_state['failed_steps']:
                    self.migration_state['failed_steps'].append(step)
        
        self.save_migration_state()
    
    def check_prerequisites(self) -> Dict:
        """Check if all prerequisites are met for migration"""
        print("Checking migration prerequisites...")
        
        issues = []
        
        # Check if FastAPI backend exists and is properly configured
        main_py = self.backend_dir / "app" / "main.py"
        if not main_py.exists():
            issues.append("FastAPI main.py not found")
        
        # Check if requirements.txt exists
        requirements = self.backend_dir / "requirements.txt"
        if not requirements.exists():
            issues.append("requirements.txt not found")
        
        # Check if frontend exists
        if not self.frontend_dir.exists():
            issues.append(f"Frontend directory not found: {self.frontend_dir}")
        
        # Check if package.json exists
        package_json = self.frontend_dir / "package.json"
        if not package_json.exists():
            issues.append("Frontend package.json not found")
        
        # Check database configuration
        if not os.getenv('DATABASE_URL'):
            issues.append("DATABASE_URL environment variable not set")
        
        # Check if ports are available
        if self.is_port_in_use(3000):
            issues.append("Port 3000 is already in use")
        
        if self.is_port_in_use(8000):
            issues.append("Port 8000 is already in use")
        
        return {
            'ready': len(issues) == 0,
            'issues': issues
        }
    
    def is_port_in_use(self, port: int) -> bool:
        """Check if a port is currently in use"""
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', port)) == 0
    
    async def run_comparative_tests(self) -> Dict:
        """Run comprehensive comparative tests"""
        print("\n" + "="*60)
        print("PHASE 1: COMPARATIVE TESTING")
        print("="*60)
        
        self.update_phase('comparative_testing')
        
        try:
            # Run the full test suite
            results = await self.test_runner.run_full_test_suite()
            
            if results.get('comparative_tests', {}).get('success', False):
                self.update_phase('comparative_testing', 'comparative_tests', True)
                print("✓ Comparative tests passed")
                return {'success': True, 'results': results}
            else:
                self.update_phase('comparative_testing', 'comparative_tests', False)
                print("✗ Comparative tests failed")
                return {'success': False, 'results': results}
                
        except Exception as e:
            self.update_phase('comparative_testing', 'comparative_tests', False)
            print(f"✗ Error running comparative tests: {e}")
            return {'success': False, 'error': str(e)}
    
    async def migrate_frontend_configuration(self) -> Dict:
        """Migrate frontend to use FastAPI backend"""
        print("\n" + "="*60)
        print("PHASE 2: FRONTEND MIGRATION")
        print("="*60)
        
        self.update_phase('frontend_migration')
        
        try:
            # Update frontend to use FastAPI
            result = self.frontend_updater.migrate_to_fastapi()
            
            if result['success']:
                self.update_phase('frontend_migration', 'frontend_config', True)
                self.migration_state['rollback_info']['frontend_changes'] = result['changes_made']
                self.save_migration_state()
                print("✓ Frontend configuration updated")
                return {'success': True, 'result': result}
            else:
                self.update_phase('frontend_migration', 'frontend_config', False)
                print("✗ Frontend configuration update failed")
                return {'success': False, 'result': result}
                
        except Exception as e:
            self.update_phase('frontend_migration', 'frontend_config', False)
            print(f"✗ Error updating frontend configuration: {e}")
            return {'success': False, 'error': str(e)}
    
    async def test_migrated_frontend(self) -> Dict:
        """Test the migrated frontend with FastAPI backend"""
        print("\n" + "="*60)
        print("PHASE 3: FRONTEND VALIDATION")
        print("="*60)
        
        self.update_phase('frontend_validation')
        
        try:
            # Run tests with the migrated frontend
            results = await self.test_runner.run_full_test_suite()
            
            # Check if FastAPI backend is working with the migrated frontend
            fastapi_working = (
                results.get('database_consistency', {}).get('FastAPI', {}).get('success', False) and
                results.get('comparative_tests', {}).get('success', False)
            )
            
            if fastapi_working:
                self.update_phase('frontend_validation', 'frontend_tests', True)
                print("✓ Migrated frontend working with FastAPI")
                return {'success': True, 'results': results}
            else:
                self.update_phase('frontend_validation', 'frontend_tests', False)
                print("✗ Migrated frontend not working properly")
                return {'success': False, 'results': results}
                
        except Exception as e:
            self.update_phase('frontend_validation', 'frontend_tests', False)
            print(f"✗ Error testing migrated frontend: {e}")
            return {'success': False, 'error': str(e)}
    
    async def cleanup_nextjs_backend(self, safe_mode: bool = True) -> Dict:
        """Clean up Next.js backend logic"""
        print("\n" + "="*60)
        print("PHASE 4: NEXT.JS CLEANUP")
        print("="*60)
        
        self.update_phase('nextjs_cleanup')
        
        try:
            # Perform cleanup
            result = self.nextjs_cleanup.perform_cleanup(safe_mode=safe_mode)
            
            if result['success']:
                self.update_phase('nextjs_cleanup', 'backend_removal', True)
                self.migration_state['rollback_info']['cleanup_info'] = result
                self.save_migration_state()
                print("✓ Next.js backend cleanup completed")
                return {'success': True, 'result': result}
            else:
                self.update_phase('nextjs_cleanup', 'backend_removal', False)
                print("✗ Next.js backend cleanup failed")
                return {'success': False, 'result': result}
                
        except Exception as e:
            self.update_phase('nextjs_cleanup', 'backend_removal', False)
            print(f"✗ Error during Next.js cleanup: {e}")
            return {'success': False, 'error': str(e)}
    
    async def final_validation(self) -> Dict:
        """Final validation of the complete migration"""
        print("\n" + "="*60)
        print("PHASE 5: FINAL VALIDATION")
        print("="*60)
        
        self.update_phase('final_validation')
        
        try:
            # Run final tests
            results = await self.test_runner.run_full_test_suite()
            
            # Validate that only FastAPI backend is working
            fastapi_working = results.get('database_consistency', {}).get('FastAPI', {}).get('success', False)
            nextjs_removed = 'backend_removal' in self.migration_state['completed_steps']
            
            if fastapi_working and nextjs_removed:
                self.update_phase('completed', 'final_validation', True)
                print("✓ Migration completed successfully")
                return {'success': True, 'results': results}
            else:
                self.update_phase('final_validation', 'final_validation', False)
                print("✗ Final validation failed")
                return {'success': False, 'results': results}
                
        except Exception as e:
            self.update_phase('final_validation', 'final_validation', False)
            print(f"✗ Error during final validation: {e}")
            return {'success': False, 'error': str(e)}
    
    async def rollback_migration(self) -> Dict:
        """Rollback the migration to original state"""
        print("\n" + "="*60)
        print("ROLLING BACK MIGRATION")
        print("="*60)
        
        rollback_success = True
        
        try:
            # Rollback Next.js cleanup
            if 'cleanup_info' in self.migration_state.get('rollback_info', {}):
                print("Rolling back Next.js cleanup...")
                if self.nextjs_cleanup.rollback_cleanup():
                    print("✓ Next.js cleanup rolled back")
                else:
                    print("✗ Failed to rollback Next.js cleanup")
                    rollback_success = False
            
            # Rollback frontend changes
            if 'frontend_changes' in self.migration_state.get('rollback_info', {}):
                print("Rolling back frontend changes...")
                if self.frontend_updater.rollback_changes():
                    print("✓ Frontend changes rolled back")
                else:
                    print("✗ Failed to rollback frontend changes")
                    rollback_success = False
            
            if rollback_success:
                # Reset migration state
                self.migration_state = {
                    'phase': 'rolled_back',
                    'completed_steps': [],
                    'failed_steps': [],
                    'rollback_info': {}
                }
                self.save_migration_state()
                print("✓ Migration rolled back successfully")
            
            return {'success': rollback_success}
            
        except Exception as e:
            print(f"✗ Error during rollback: {e}")
            return {'success': False, 'error': str(e)}
    
    async def run_complete_migration(self, safe_cleanup: bool = True) -> Dict:
        """Run the complete migration process"""
        print("="*60)
        print("METACONSCIOUS NEXT.JS TO FASTAPI MIGRATION")
        print("="*60)
        
        # Check prerequisites
        prereq_check = self.check_prerequisites()
        if not prereq_check['ready']:
            print("✗ Prerequisites not met:")
            for issue in prereq_check['issues']:
                print(f"  - {issue}")
            return {'success': False, 'error': 'Prerequisites not met', 'issues': prereq_check['issues']}
        
        print("✓ Prerequisites check passed")
        
        migration_results = {}
        
        try:
            # Phase 1: Comparative Testing
            if 'comparative_tests' not in self.migration_state['completed_steps']:
                result = await self.run_comparative_tests()
                migration_results['comparative_tests'] = result
                if not result['success']:
                    return {'success': False, 'phase': 'comparative_testing', 'results': migration_results}
            
            # Phase 2: Frontend Migration
            if 'frontend_config' not in self.migration_state['completed_steps']:
                result = await self.migrate_frontend_configuration()
                migration_results['frontend_migration'] = result
                if not result['success']:
                    return {'success': False, 'phase': 'frontend_migration', 'results': migration_results}
            
            # Phase 3: Frontend Validation
            if 'frontend_tests' not in self.migration_state['completed_steps']:
                result = await self.test_migrated_frontend()
                migration_results['frontend_validation'] = result
                if not result['success']:
                    return {'success': False, 'phase': 'frontend_validation', 'results': migration_results}
            
            # Phase 4: Next.js Cleanup
            if 'backend_removal' not in self.migration_state['completed_steps']:
                result = await self.cleanup_nextjs_backend(safe_mode=safe_cleanup)
                migration_results['nextjs_cleanup'] = result
                if not result['success']:
                    return {'success': False, 'phase': 'nextjs_cleanup', 'results': migration_results}
            
            # Phase 5: Final Validation
            if 'final_validation' not in self.migration_state['completed_steps']:
                result = await self.final_validation()
                migration_results['final_validation'] = result
                if not result['success']:
                    return {'success': False, 'phase': 'final_validation', 'results': migration_results}
            
            # Migration completed successfully
            print("\n" + "="*60)
            print("MIGRATION COMPLETED SUCCESSFULLY!")
            print("="*60)
            print("✓ FastAPI backend is now handling all requests")
            print("✓ Frontend is configured to use FastAPI")
            print("✓ Next.js backend logic has been removed")
            print("✓ All tests are passing")
            
            return {'success': True, 'results': migration_results}
            
        except Exception as e:
            print(f"\n✗ Migration failed with error: {e}")
            return {'success': False, 'error': str(e), 'results': migration_results}
    
    def print_migration_status(self):
        """Print current migration status"""
        print("\n" + "="*60)
        print("MIGRATION STATUS")
        print("="*60)
        
        print(f"Current Phase: {self.migration_state['phase']}")
        
        if self.migration_state['completed_steps']:
            print(f"\nCompleted Steps:")
            for step in self.migration_state['completed_steps']:
                print(f"  ✓ {step}")
        
        if self.migration_state['failed_steps']:
            print(f"\nFailed Steps:")
            for step in self.migration_state['failed_steps']:
                print(f"  ✗ {step}")

async def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="MetaConscious Migration Orchestrator")
    parser.add_argument("--migrate", action="store_true", help="Run complete migration")
    parser.add_argument("--rollback", action="store_true", help="Rollback migration")
    parser.add_argument("--status", action="store_true", help="Show migration status")
    parser.add_argument("--test-only", action="store_true", help="Run tests only")
    parser.add_argument("--safe-cleanup", action="store_true", default=True, help="Use safe cleanup mode")
    parser.add_argument("--frontend-dir", default="../app", help="Frontend directory")
    parser.add_argument("--backend-dir", default=".", help="Backend directory")
    
    args = parser.parse_args()
    
    orchestrator = MigrationOrchestrator(args.frontend_dir, args.backend_dir)
    
    try:
        if args.status:
            orchestrator.print_migration_status()
            
        elif args.test_only:
            result = await orchestrator.run_comparative_tests()
            print(f"Test result: {'PASS' if result['success'] else 'FAIL'}")
            sys.exit(0 if result['success'] else 1)
            
        elif args.rollback:
            result = await orchestrator.rollback_migration()
            print(f"Rollback result: {'SUCCESS' if result['success'] else 'FAILED'}")
            sys.exit(0 if result['success'] else 1)
            
        elif args.migrate:
            result = await orchestrator.run_complete_migration(safe_cleanup=args.safe_cleanup)
            
            # Save final results
            results_file = Path("migration_results.json")
            with open(results_file, 'w') as f:
                json.dump(result, f, indent=2, default=str)
            
            print(f"\nDetailed results saved to: {results_file}")
            print(f"Migration result: {'SUCCESS' if result['success'] else 'FAILED'}")
            
            sys.exit(0 if result['success'] else 1)
            
        else:
            parser.print_help()
            
    except KeyboardInterrupt:
        print("\nMigration interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Migration error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
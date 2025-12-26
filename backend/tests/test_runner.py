"""
Comprehensive Test Runner for FastAPI Migration
Manages both backends and runs comparative tests
"""
import asyncio
import subprocess
import time
import os
import sys
import signal
import psutil
from pathlib import Path
from typing import Optional, Dict, List
import httpx
import json
from contextlib import asynccontextmanager

class BackendManager:
    """Manages backend processes for testing"""
    
    def __init__(self):
        self.nextjs_process: Optional[subprocess.Popen] = None
        self.fastapi_process: Optional[subprocess.Popen] = None
        self.processes = []
        
    def start_nextjs_backend(self, frontend_dir: str = "../app") -> bool:
        """Start the Next.js backend"""
        try:
            print("Starting Next.js backend...")
            
            # Change to frontend directory and start dev server
            env = os.environ.copy()
            env['NODE_OPTIONS'] = '--max-old-space-size=512'
            
            self.nextjs_process = subprocess.Popen(
                ["yarn", "dev"],
                cwd=frontend_dir,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            self.processes.append(self.nextjs_process)
            
            # Wait for server to start
            if self._wait_for_server("http://localhost:3000", timeout=60):
                print("✓ Next.js backend started successfully")
                return True
            else:
                print("✗ Next.js backend failed to start")
                self.stop_nextjs_backend()
                return False
                
        except Exception as e:
            print(f"Error starting Next.js backend: {e}")
            return False
    
    def start_fastapi_backend(self, backend_dir: str = ".") -> bool:
        """Start the FastAPI backend"""
        try:
            print("Starting FastAPI backend...")
            
            # Start uvicorn server
            self.fastapi_process = subprocess.Popen(
                [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"],
                cwd=backend_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            self.processes.append(self.fastapi_process)
            
            # Wait for server to start
            if self._wait_for_server("http://localhost:8000", timeout=60):
                print("✓ FastAPI backend started successfully")
                return True
            else:
                print("✗ FastAPI backend failed to start")
                self.stop_fastapi_backend()
                return False
                
        except Exception as e:
            print(f"Error starting FastAPI backend: {e}")
            return False
    
    def _wait_for_server(self, url: str, timeout: int = 30) -> bool:
        """Wait for a server to become available"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = httpx.get(url, timeout=5.0)
                if response.status_code < 500:  # Any non-server-error response means server is up
                    return True
            except:
                pass
            
            time.sleep(2)
        
        return False
    
    def stop_nextjs_backend(self):
        """Stop the Next.js backend"""
        if self.nextjs_process:
            try:
                print("Stopping Next.js backend...")
                self._terminate_process_tree(self.nextjs_process.pid)
                self.nextjs_process = None
                print("✓ Next.js backend stopped")
            except Exception as e:
                print(f"Error stopping Next.js backend: {e}")
    
    def stop_fastapi_backend(self):
        """Stop the FastAPI backend"""
        if self.fastapi_process:
            try:
                print("Stopping FastAPI backend...")
                self._terminate_process_tree(self.fastapi_process.pid)
                self.fastapi_process = None
                print("✓ FastAPI backend stopped")
            except Exception as e:
                print(f"Error stopping FastAPI backend: {e}")
    
    def _terminate_process_tree(self, pid: int):
        """Terminate a process and all its children"""
        try:
            parent = psutil.Process(pid)
            children = parent.children(recursive=True)
            
            # Terminate children first
            for child in children:
                try:
                    child.terminate()
                except psutil.NoSuchProcess:
                    pass
            
            # Wait for children to terminate
            gone, alive = psutil.wait_procs(children, timeout=5)
            
            # Kill any remaining children
            for child in alive:
                try:
                    child.kill()
                except psutil.NoSuchProcess:
                    pass
            
            # Terminate parent
            try:
                parent.terminate()
                parent.wait(timeout=5)
            except psutil.TimeoutExpired:
                parent.kill()
            except psutil.NoSuchProcess:
                pass
                
        except psutil.NoSuchProcess:
            pass
    
    def stop_all(self):
        """Stop all managed processes"""
        self.stop_nextjs_backend()
        self.stop_fastapi_backend()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop_all()

class TestRunner:
    """Main test runner for the migration validation"""
    
    def __init__(self):
        self.backend_manager = BackendManager()
        self.test_results = {}
        
    async def run_comparative_tests(self) -> Dict:
        """Run the comparative test suite"""
        print("\n" + "="*60)
        print("RUNNING COMPARATIVE TEST SUITE")
        print("="*60)
        
        # Run pytest with the comparative test suite
        try:
            result = subprocess.run([
                sys.executable, "-m", "pytest", 
                "test_comparative_suite.py", 
                "-v", 
                "--tb=short",
                "--json-report",
                "--json-report-file=test_results.json"
            ], capture_output=True, text=True, timeout=300)
            
            print("STDOUT:")
            print(result.stdout)
            
            if result.stderr:
                print("STDERR:")
                print(result.stderr)
            
            # Load test results if available
            results_file = Path("test_results.json")
            if results_file.exists():
                try:
                    with open(results_file) as f:
                        test_data = json.load(f)
                    
                    self.test_results['comparative'] = {
                        'passed': test_data.get('summary', {}).get('passed', 0),
                        'failed': test_data.get('summary', {}).get('failed', 0),
                        'total': test_data.get('summary', {}).get('total', 0),
                        'duration': test_data.get('duration', 0)
                    }
                except Exception as e:
                    print(f"Error loading test results: {e}")
            
            return {
                'success': result.returncode == 0,
                'returncode': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr
            }
            
        except subprocess.TimeoutExpired:
            print("Tests timed out after 5 minutes")
            return {'success': False, 'error': 'timeout'}
        except Exception as e:
            print(f"Error running tests: {e}")
            return {'success': False, 'error': str(e)}
    
    async def test_llm_functionality(self) -> Dict:
        """Test LLM functionality on both backends"""
        print("\n" + "="*60)
        print("TESTING LLM FUNCTIONALITY")
        print("="*60)
        
        if not os.getenv('LLM_API_KEY'):
            print("⚠️  LLM_API_KEY not configured - skipping LLM tests")
            return {'success': True, 'skipped': True, 'reason': 'No LLM_API_KEY'}
        
        results = {}
        
        # Test both backends
        for name, url in [("Next.js", "http://localhost:3000"), ("FastAPI", "http://localhost:8000")]:
            try:
                print(f"\nTesting {name} LLM integration...")
                
                async with httpx.AsyncClient(timeout=30.0) as client:
                    # Test plan generation
                    response = await client.post(
                        f"{url}/api/generate-plan",
                        json={"date": "2024-12-25"},
                        headers={"Content-Type": "application/json"}
                    )
                    
                    results[name] = {
                        'status_code': response.status_code,
                        'success': response.status_code == 200,
                        'response': response.json() if response.status_code == 200 else response.text
                    }
                    
                    if response.status_code == 200:
                        print(f"✓ {name} LLM integration working")
                    else:
                        print(f"✗ {name} LLM integration failed: {response.status_code}")
                        
            except Exception as e:
                print(f"✗ {name} LLM test error: {e}")
                results[name] = {'success': False, 'error': str(e)}
        
        return results
    
    async def validate_database_consistency(self) -> Dict:
        """Validate that both backends work with the same database"""
        print("\n" + "="*60)
        print("VALIDATING DATABASE CONSISTENCY")
        print("="*60)
        
        results = {}
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Test database access on both backends
                for name, url in [("Next.js", "http://localhost:3000"), ("FastAPI", "http://localhost:8000")]:
                    try:
                        # Test status endpoint (requires database)
                        response = await client.get(f"{url}/api/status")
                        
                        results[name] = {
                            'status_code': response.status_code,
                            'success': response.status_code == 200,
                            'has_user': False
                        }
                        
                        if response.status_code == 200:
                            data = response.json()
                            results[name]['has_user'] = data.get('user') is not None
                            print(f"✓ {name} database connection working")
                        else:
                            print(f"✗ {name} database connection failed")
                            
                    except Exception as e:
                        print(f"✗ {name} database test error: {e}")
                        results[name] = {'success': False, 'error': str(e)}
            
            return results
            
        except Exception as e:
            print(f"Database validation error: {e}")
            return {'error': str(e)}
    
    async def run_full_test_suite(self) -> Dict:
        """Run the complete test suite"""
        print("Starting comprehensive migration test suite...")
        
        # Start both backends
        with self.backend_manager:
            # Start Next.js backend
            if not self.backend_manager.start_nextjs_backend():
                return {'success': False, 'error': 'Failed to start Next.js backend'}
            
            # Start FastAPI backend
            if not self.backend_manager.start_fastapi_backend():
                return {'success': False, 'error': 'Failed to start FastAPI backend'}
            
            # Wait a bit for both servers to fully initialize
            print("Waiting for backends to fully initialize...")
            await asyncio.sleep(10)
            
            # Run all tests
            results = {
                'database_consistency': await self.validate_database_consistency(),
                'comparative_tests': await self.run_comparative_tests(),
                'llm_functionality': await self.test_llm_functionality(),
                'test_results': self.test_results
            }
            
            # Print summary
            self.print_test_summary(results)
            
            return results
    
    def print_test_summary(self, results: Dict):
        """Print a summary of all test results"""
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        
        # Database consistency
        db_results = results.get('database_consistency', {})
        print(f"Database Consistency:")
        for backend, result in db_results.items():
            if isinstance(result, dict):
                status = "✓" if result.get('success') else "✗"
                print(f"  {status} {backend}: {result.get('status_code', 'N/A')}")
        
        # Comparative tests
        comp_results = results.get('comparative_tests', {})
        print(f"\nComparative Tests:")
        if comp_results.get('success'):
            print("  ✓ All comparative tests passed")
        else:
            print("  ✗ Some comparative tests failed")
        
        # LLM functionality
        llm_results = results.get('llm_functionality', {})
        print(f"\nLLM Functionality:")
        if llm_results.get('skipped'):
            print("  ⚠️  Skipped (no LLM_API_KEY)")
        else:
            for backend, result in llm_results.items():
                if isinstance(result, dict):
                    status = "✓" if result.get('success') else "✗"
                    print(f"  {status} {backend}")
        
        # Overall status
        overall_success = (
            comp_results.get('success', False) and
            all(r.get('success', False) for r in db_results.values() if isinstance(r, dict))
        )
        
        print(f"\nOverall Status: {'✓ PASS' if overall_success else '✗ FAIL'}")

async def main():
    """Main function"""
    runner = TestRunner()
    
    try:
        results = await runner.run_full_test_suite()
        
        # Save results to file
        with open("migration_test_results.json", "w") as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\nDetailed results saved to: migration_test_results.json")
        
        # Exit with appropriate code
        overall_success = results.get('comparative_tests', {}).get('success', False)
        sys.exit(0 if overall_success else 1)
        
    except KeyboardInterrupt:
        print("\nTest suite interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Test suite error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
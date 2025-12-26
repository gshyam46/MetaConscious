"""
Install Test Dependencies
Installs additional dependencies needed for the comparative testing suite
"""
import subprocess
import sys
from pathlib import Path

def install_dependencies():
    """Install required test dependencies"""
    
    # Additional dependencies for testing
    test_dependencies = [
        "pytest-json-report",  # For JSON test reports
        "psutil",  # For process management
        "httpx",   # Already in requirements.txt but ensure it's there
    ]
    
    print("Installing test dependencies...")
    
    for dep in test_dependencies:
        try:
            print(f"Installing {dep}...")
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", dep
            ], check=True, capture_output=True, text=True)
            print(f"✓ {dep} installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"✗ Failed to install {dep}: {e}")
            print(f"Error output: {e.stderr}")
            return False
    
    print("✓ All test dependencies installed successfully")
    return True

def check_existing_dependencies():
    """Check if required dependencies are already installed"""
    
    required_deps = [
        "pytest",
        "pytest-asyncio", 
        "httpx",
        "fastapi",
        "uvicorn"
    ]
    
    print("Checking existing dependencies...")
    
    missing_deps = []
    
    for dep in required_deps:
        try:
            result = subprocess.run([
                sys.executable, "-m", "pip", "show", dep
            ], check=True, capture_output=True, text=True)
            print(f"✓ {dep} is installed")
        except subprocess.CalledProcessError:
            print(f"✗ {dep} is missing")
            missing_deps.append(dep)
    
    if missing_deps:
        print(f"\nMissing dependencies: {', '.join(missing_deps)}")
        print("Please install them with: pip install -r requirements.txt")
        return False
    
    return True

def main():
    """Main function"""
    print("Setting up test environment...")
    
    # Check if we're in the right directory
    if not Path("requirements.txt").exists():
        print("Error: requirements.txt not found. Please run from the backend directory.")
        sys.exit(1)
    
    # Check existing dependencies
    if not check_existing_dependencies():
        print("\nPlease install basic dependencies first:")
        print("pip install -r requirements.txt")
        sys.exit(1)
    
    # Install additional test dependencies
    if install_dependencies():
        print("\n✓ Test environment setup complete!")
        print("\nYou can now run:")
        print("  python test_runner.py                    # Run comparative tests")
        print("  python migration_orchestrator.py --migrate  # Run full migration")
    else:
        print("\n✗ Test environment setup failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
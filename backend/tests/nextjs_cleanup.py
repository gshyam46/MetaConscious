"""
Next.js Backend Cleanup Tool
Safely removes backend logic from Next.js application after FastAPI migration
"""
import os
import shutil
from pathlib import Path
from typing import List, Dict, Optional
import json

class NextJSCleanup:
    """Handles cleanup of Next.js backend components after migration"""
    
    def __init__(self, frontend_dir: str = "../app"):
        self.frontend_dir = Path(frontend_dir)
        self.backup_dir = self.frontend_dir / ".migration_backup"
        self.cleanup_log = []
        
    def create_backup(self) -> bool:
        """Create a backup of files before cleanup"""
        try:
            if self.backup_dir.exists():
                shutil.rmtree(self.backup_dir)
            
            self.backup_dir.mkdir(exist_ok=True)
            
            # Backup API routes
            api_dir = self.frontend_dir / "api"
            if api_dir.exists():
                backup_api_dir = self.backup_dir / "api"
                shutil.copytree(api_dir, backup_api_dir)
                print(f"✓ Backed up API routes to {backup_api_dir}")
            
            # Backup lib directory (contains business logic)
            lib_dir = self.frontend_dir / "lib"
            if lib_dir.exists():
                backup_lib_dir = self.backup_dir / "lib"
                shutil.copytree(lib_dir, backup_lib_dir)
                print(f"✓ Backed up lib directory to {backup_lib_dir}")
            
            # Backup package.json
            package_json = self.frontend_dir / "package.json"
            if package_json.exists():
                shutil.copy2(package_json, self.backup_dir / "package.json")
                print(f"✓ Backed up package.json")
            
            return True
            
        except Exception as e:
            print(f"Error creating backup: {e}")
            return False
    
    def identify_backend_files(self) -> Dict[str, List[Path]]:
        """Identify files that contain backend logic"""
        backend_files = {
            'api_routes': [],
            'business_logic': [],
            'database_files': [],
            'scheduler_files': [],
            'llm_files': []
        }
        
        # API routes
        api_dir = self.frontend_dir / "api"
        if api_dir.exists():
            for file_path in api_dir.rglob("*.js"):
                backend_files['api_routes'].append(file_path)
        
        # Business logic in lib directory
        lib_dir = self.frontend_dir / "lib"
        if lib_dir.exists():
            # Database files
            db_dir = lib_dir / "db"
            if db_dir.exists():
                for file_path in db_dir.rglob("*.js"):
                    backend_files['database_files'].append(file_path)
            
            # Planner files
            planner_dir = lib_dir / "planner"
            if planner_dir.exists():
                for file_path in planner_dir.rglob("*.js"):
                    if "scheduler" in file_path.name:
                        backend_files['scheduler_files'].append(file_path)
                    else:
                        backend_files['business_logic'].append(file_path)
            
            # LLM files
            llm_dir = lib_dir / "llm"
            if llm_dir.exists():
                for file_path in llm_dir.rglob("*.js"):
                    backend_files['llm_files'].append(file_path)
        
        return backend_files
    
    def remove_backend_dependencies(self) -> bool:
        """Remove backend-specific dependencies from package.json"""
        package_json_path = self.frontend_dir / "package.json"
        
        if not package_json_path.exists():
            return True
        
        try:
            with open(package_json_path, 'r') as f:
                package_data = json.load(f)
            
            # Dependencies to remove (backend-specific)
            backend_deps = [
                'pg',  # PostgreSQL client
                'mongodb',  # MongoDB client (if any)
                'node-cron',  # Scheduler
                'openai',  # LLM client
                'uuid',  # UUID generation (if only used in backend)
                'zod'  # Validation (if only used in backend)
            ]
            
            removed_deps = []
            dependencies = package_data.get('dependencies', {})
            
            for dep in backend_deps:
                if dep in dependencies:
                    removed_deps.append(f"{dep}@{dependencies[dep]}")
                    del dependencies[dep]
            
            if removed_deps:
                # Write updated package.json
                with open(package_json_path, 'w') as f:
                    json.dump(package_data, f, indent=2)
                
                self.cleanup_log.append({
                    'action': 'removed_dependencies',
                    'dependencies': removed_deps,
                    'file': str(package_json_path)
                })
                
                print(f"✓ Removed backend dependencies: {', '.join(removed_deps)}")
                return True
            
        except Exception as e:
            print(f"Error updating package.json: {e}")
            return False
        
        return True
    
    def remove_backend_files(self, backend_files: Dict[str, List[Path]], 
                           categories_to_remove: List[str] = None) -> bool:
        """Remove specified categories of backend files"""
        
        if categories_to_remove is None:
            categories_to_remove = ['api_routes', 'business_logic', 'database_files', 
                                  'scheduler_files', 'llm_files']
        
        try:
            for category in categories_to_remove:
                files = backend_files.get(category, [])
                
                for file_path in files:
                    if file_path.exists():
                        file_path.unlink()
                        self.cleanup_log.append({
                            'action': 'removed_file',
                            'category': category,
                            'file': str(file_path)
                        })
                        print(f"✓ Removed {category}: {file_path.name}")
                
                # Remove empty directories
                if category == 'api_routes':
                    api_dir = self.frontend_dir / "api"
                    if api_dir.exists() and not any(api_dir.iterdir()):
                        api_dir.rmdir()
                        print(f"✓ Removed empty API directory")
                
                elif category in ['database_files', 'business_logic', 'scheduler_files', 'llm_files']:
                    # Remove empty subdirectories in lib
                    lib_dir = self.frontend_dir / "lib"
                    if lib_dir.exists():
                        for subdir in ['db', 'planner', 'llm']:
                            subdir_path = lib_dir / subdir
                            if subdir_path.exists() and not any(subdir_path.iterdir()):
                                subdir_path.rmdir()
                                print(f"✓ Removed empty directory: {subdir}")
            
            return True
            
        except Exception as e:
            print(f"Error removing backend files: {e}")
            return False
    
    def update_next_config_for_frontend_only(self) -> bool:
        """Update Next.js config for frontend-only operation"""
        next_config_path = self.frontend_dir / "next.config.js"
        
        if not next_config_path.exists():
            return True
        
        try:
            content = next_config_path.read_text(encoding='utf-8')
            
            # Remove any API-related configurations
            # Add configuration for static export if needed
            frontend_only_config = """/** @type {import('next').NextConfig} */
const nextConfig = {
  // Frontend-only configuration
  trailingSlash: true,
  
  // API requests are now handled by FastAPI backend
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/api/:path*',
      },
    ];
  },
  
  // CORS headers for development
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'Access-Control-Allow-Origin',
            value: '*',
          },
          {
            key: 'Access-Control-Allow-Methods',
            value: 'GET, POST, PUT, DELETE, OPTIONS',
          },
          {
            key: 'Access-Control-Allow-Headers',
            value: 'Content-Type, Authorization',
          },
        ],
      },
    ];
  },
};

module.exports = nextConfig;
"""
            
            next_config_path.write_text(frontend_only_config, encoding='utf-8')
            
            self.cleanup_log.append({
                'action': 'updated_next_config',
                'file': str(next_config_path)
            })
            
            print("✓ Updated Next.js config for frontend-only operation")
            return True
            
        except Exception as e:
            print(f"Error updating next.config.js: {e}")
            return False
    
    def create_readme_update(self) -> bool:
        """Create updated README with new architecture information"""
        readme_path = self.frontend_dir / "README_MIGRATION.md"
        
        readme_content = """# MetaConscious - Post-Migration Architecture

## Overview

This Next.js application has been migrated to use a FastAPI backend. The frontend now operates as a pure client-side application that communicates with the FastAPI backend via HTTP API calls.

## Architecture Changes

### Before Migration
- Next.js with API routes handling backend logic
- Business logic in `/lib` directory
- Database operations in Next.js API routes
- LLM integration in Next.js backend

### After Migration
- Next.js frontend-only application
- FastAPI backend handling all business logic
- Database operations in FastAPI backend
- LLM integration in FastAPI backend

## Running the Application

### Prerequisites
1. FastAPI backend must be running on port 8000
2. PostgreSQL database must be accessible to FastAPI backend

### Development
```bash
# Start FastAPI backend (in backend directory)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Start Next.js frontend (in this directory)
yarn dev
```

### Production
```bash
# Build frontend
yarn build

# Start frontend
yarn start
```

## API Configuration

The frontend is configured to proxy all `/api/*` requests to the FastAPI backend at `http://localhost:8000`.

This is configured in `next.config.js`:

```javascript
async rewrites() {
  return [
    {
      source: '/api/:path*',
      destination: 'http://localhost:8000/api/:path*',
    },
  ];
}
```

## Migration Backup

All removed backend files have been backed up to `.migration_backup/` directory.

## Rollback

To rollback to the original Next.js backend:
1. Stop the FastAPI backend
2. Restore files from `.migration_backup/`
3. Reinstall backend dependencies: `yarn install`
4. Start Next.js: `yarn dev`

## Environment Variables

The following environment variables are no longer needed in the frontend:
- `DATABASE_URL` (now handled by FastAPI)
- `LLM_API_KEY` (now handled by FastAPI)
- `LLM_PROVIDER` (now handled by FastAPI)

These should be configured in the FastAPI backend's `.env` file.
"""
        
        try:
            readme_path.write_text(readme_content, encoding='utf-8')
            print(f"✓ Created migration README: {readme_path}")
            return True
        except Exception as e:
            print(f"Error creating README: {e}")
            return False
    
    def perform_cleanup(self, safe_mode: bool = True) -> Dict:
        """Perform the complete cleanup process"""
        print("Starting Next.js backend cleanup...")
        
        # Create backup first
        if not self.create_backup():
            return {'success': False, 'error': 'Failed to create backup'}
        
        # Identify backend files
        backend_files = self.identify_backend_files()
        
        print(f"\nFound backend files:")
        for category, files in backend_files.items():
            if files:
                print(f"  {category}: {len(files)} files")
        
        if safe_mode:
            # In safe mode, only remove API routes and update configs
            categories_to_remove = ['api_routes']
        else:
            # In full mode, remove all backend logic
            categories_to_remove = ['api_routes', 'business_logic', 'database_files', 
                                  'scheduler_files', 'llm_files']
        
        # Remove backend files
        if not self.remove_backend_files(backend_files, categories_to_remove):
            return {'success': False, 'error': 'Failed to remove backend files'}
        
        # Update package.json
        if not self.remove_backend_dependencies():
            return {'success': False, 'error': 'Failed to update package.json'}
        
        # Update Next.js config
        if not self.update_next_config_for_frontend_only():
            return {'success': False, 'error': 'Failed to update next.config.js'}
        
        # Create documentation
        if not self.create_readme_update():
            return {'success': False, 'error': 'Failed to create README'}
        
        # Save cleanup log
        log_path = self.frontend_dir / "migration_cleanup.json"
        try:
            with open(log_path, 'w') as f:
                json.dump(self.cleanup_log, f, indent=2)
            print(f"✓ Cleanup log saved to: {log_path}")
        except Exception as e:
            print(f"Warning: Could not save cleanup log: {e}")
        
        return {
            'success': True,
            'backup_location': str(self.backup_dir),
            'cleanup_log': self.cleanup_log,
            'files_removed': len(self.cleanup_log)
        }
    
    def rollback_cleanup(self) -> bool:
        """Rollback the cleanup by restoring from backup"""
        if not self.backup_dir.exists():
            print("No backup found to rollback from")
            return False
        
        try:
            print("Rolling back Next.js cleanup...")
            
            # Restore API directory
            backup_api = self.backup_dir / "api"
            if backup_api.exists():
                api_dir = self.frontend_dir / "api"
                if api_dir.exists():
                    shutil.rmtree(api_dir)
                shutil.copytree(backup_api, api_dir)
                print("✓ Restored API routes")
            
            # Restore lib directory
            backup_lib = self.backup_dir / "lib"
            if backup_lib.exists():
                lib_dir = self.frontend_dir / "lib"
                if lib_dir.exists():
                    shutil.rmtree(lib_dir)
                shutil.copytree(backup_lib, lib_dir)
                print("✓ Restored lib directory")
            
            # Restore package.json
            backup_package = self.backup_dir / "package.json"
            if backup_package.exists():
                shutil.copy2(backup_package, self.frontend_dir / "package.json")
                print("✓ Restored package.json")
            
            print("Rollback completed successfully")
            return True
            
        except Exception as e:
            print(f"Error during rollback: {e}")
            return False

def main():
    """Main function for command-line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Cleanup Next.js backend after FastAPI migration")
    parser.add_argument("--cleanup", action="store_true", help="Perform cleanup")
    parser.add_argument("--rollback", action="store_true", help="Rollback cleanup")
    parser.add_argument("--safe-mode", action="store_true", help="Safe mode (only remove API routes)")
    parser.add_argument("--frontend-dir", default="../app", help="Frontend directory path")
    
    args = parser.parse_args()
    
    cleanup = NextJSCleanup(args.frontend_dir)
    
    if args.cleanup:
        result = cleanup.perform_cleanup(safe_mode=args.safe_mode)
        print(f"\nCleanup result: {result}")
        
    elif args.rollback:
        success = cleanup.rollback_cleanup()
        print(f"Rollback {'successful' if success else 'failed'}")
        
    else:
        # Just identify backend files
        backend_files = cleanup.identify_backend_files()
        print("Backend files found:")
        for category, files in backend_files.items():
            if files:
                print(f"\n{category}:")
                for file_path in files:
                    print(f"  {file_path}")

if __name__ == "__main__":
    main()
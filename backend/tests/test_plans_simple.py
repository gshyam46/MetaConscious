"""
Simple test for plans module
Tests that the plans module is correctly structured
"""
import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

def test_plans_import():
    """Test that plans module can be imported"""
    print("Testing plans module import...")
    
    try:
        from app.api.routes import plans
        print("✓ Plans module imported successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to import plans module: {e}")
        return False

def test_plans_router():
    """Test that plans router is properly configured"""
    print("Testing plans router configuration...")
    
    try:
        from app.api.routes.plans import router
        
        # Check that router exists
        assert router is not None
        print("✓ Plans router exists")
        
        # Check that routes are registered
        routes = [route.path for route in router.routes]
        print(f"Routes found: {routes}")
        
        # Should have /plans and /generate-plan routes
        expected_routes = ["/plans", "/generate-plan"]
        for expected_route in expected_routes:
            if expected_route in routes:
                print(f"✓ Route {expected_route} found")
            else:
                print(f"❌ Route {expected_route} not found")
                return False
        
        return True
    except Exception as e:
        print(f"❌ Failed to test plans router: {e}")
        return False

def test_plans_functions():
    """Test that plans functions are properly defined"""
    print("Testing plans endpoint functions...")
    
    try:
        from app.api.routes.plans import get_plans, generate_plan
        
        # Check functions exist
        assert callable(get_plans)
        assert callable(generate_plan)
        
        print("✓ get_plans function exists and is callable")
        print("✓ generate_plan function exists and is callable")
        
        return True
    except Exception as e:
        print(f"❌ Failed to test plans functions: {e}")
        return False

def test_main_app_includes_plans():
    """Test that main app includes plans router"""
    print("Testing main app includes plans router...")
    
    try:
        from app.main import app
        
        # Check that app exists
        assert app is not None
        print("✓ FastAPI app exists")
        
        # Check routes include plans endpoints
        routes = []
        for route in app.routes:
            if hasattr(route, 'path'):
                routes.append(route.path)
        
        print(f"App routes: {[r for r in routes if 'api' in r]}")
        
        # Should have plans routes
        plans_routes_found = any('/api/plans' in route or '/api/generate-plan' in route for route in routes)
        if plans_routes_found:
            print("✓ Plans routes found in main app")
        else:
            print("❌ Plans routes not found in main app")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Failed to test main app: {e}")
        return False

def run_tests():
    """Run all tests"""
    print("Testing Plans Module Structure")
    print("=" * 50)
    print("Verifying plans module is correctly implemented")
    print()
    
    tests = [
        test_plans_import,
        test_plans_router,
        test_plans_functions,
        test_main_app_includes_plans
    ]
    
    passed = 0
    total = len(tests)
    
    for i, test in enumerate(tests, 1):
        try:
            print(f"Test {i}/{total}: {test.__name__}")
            if test():
                passed += 1
                print("✅ PASSED")
            else:
                print("❌ FAILED")
        except Exception as e:
            print(f"❌ FAILED with exception: {e}")
        print()
    
    print("=" * 50)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All plans module tests passed!")
        print("✅ Plans module is correctly structured and integrated")
        return True
    else:
        print("❌ Some tests failed")
        return False

if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)
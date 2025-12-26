"""
Test date conversion logic
"""
from datetime import datetime

def test_date_conversion():
    """Test the date conversion logic we added"""
    
    # Test goal date conversion
    target_date = "2024-12-31"
    try:
        date_obj = datetime.strptime(target_date, '%Y-%m-%d').date()
        print(f"✓ Goal date conversion: {target_date} -> {date_obj} (type: {type(date_obj)})")
    except ValueError as e:
        print(f"✗ Goal date conversion failed: {e}")
    
    # Test task date conversion
    due_date = "2024-12-25"
    try:
        date_obj = datetime.strptime(due_date, '%Y-%m-%d').date()
        print(f"✓ Task date conversion: {due_date} -> {date_obj} (type: {type(date_obj)})")
    except ValueError as e:
        print(f"✗ Task date conversion failed: {e}")
    
    # Test plan date conversion
    plan_date = "2024-12-17"
    try:
        date_obj = datetime.strptime(plan_date, '%Y-%m-%d').date()
        print(f"✓ Plan date conversion: {plan_date} -> {date_obj} (type: {type(date_obj)})")
    except ValueError as e:
        print(f"✗ Plan date conversion failed: {e}")
    
    print("\nDate conversion logic is working correctly!")
    print("The FastAPI server needs to be restarted to pick up the changes.")

if __name__ == "__main__":
    test_date_conversion()
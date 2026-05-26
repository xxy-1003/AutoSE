"""
Test script to verify FastAPI backend implementation.
"""

import asyncio
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from autose_platform.backend import FastAPIBackend
from autose_platform.models import RequirementRequest


async def test_backend():
    """Test the FastAPIBackend class."""
    print("Testing FastAPIBackend implementation...")
    
    try:
        # Initialize backend
        backend = FastAPIBackend()
        print("✓ FastAPIBackend initialized successfully")
        
        # Test requirement analysis
        test_text = "Deploy an AI security system supporting 100 cameras with GPU acceleration"
        print(f"\nTesting with requirement: {test_text}")
        
        result = await backend.analyze_requirement(test_text)
        
        # Check result structure
        required_keys = ["markdown", "json", "timestamp", "requirements", "selected_products", "validation"]
        missing_keys = [key for key in required_keys if key not in result]
        
        if missing_keys:
            print(f"✗ Missing keys in result: {missing_keys}")
            return False
        
        print("✓ Result contains all required keys")
        
        # Check data types
        assert isinstance(result["markdown"], str), "markdown should be string"
        assert isinstance(result["json"], dict), "json should be dict"
        assert isinstance(result["timestamp"], str), "timestamp should be string"
        assert isinstance(result["requirements"], dict), "requirements should be dict"
        assert isinstance(result["selected_products"], list), "selected_products should be list"
        assert isinstance(result["validation"], dict), "validation should be dict"
        
        print("✓ All result fields have correct data types")
        
        # Check that markdown is not empty
        assert len(result["markdown"]) > 0, "markdown should not be empty"
        
        # Check that JSON has required structure
        json_keys = ["requirements", "selected_products", "validation", "reasoning", "optimization_suggestions"]
        for key in json_keys:
            assert key in result["json"], f"json should contain {key}"
        
        print("✓ JSON structure is correct")
        
        print("\n✅ FastAPIBackend implementation test PASSED!")
        return True
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_models():
    """Test the data models."""
    print("\nTesting data models...")
    
    try:
        # Test RequirementRequest model
        req = RequirementRequest(text="Test requirement")
        assert req.text == "Test requirement"
        print("✓ RequirementRequest model works")
        
        # Test that validation works
        try:
            RequirementRequest(text="")  # Should fail validation
            print("✗ RequirementRequest validation failed - empty text should not be allowed")
            return False
        except ValueError:
            print("✓ RequirementRequest validation works (rejects empty text)")
        
        print("✅ Data models test PASSED!")
        return True
        
    except Exception as e:
        print(f"✗ Data models test failed: {e}")
        return False


async def main():
    """Run all tests."""
    print("=" * 60)
    print("Testing Task 1.2: FastAPI Backend Orchestrator")
    print("=" * 60)
    
    model_test_passed = await test_models()
    backend_test_passed = await test_backend()
    
    print("\n" + "=" * 60)
    print("Test Summary:")
    print(f"  Data Models: {'PASS' if model_test_passed else 'FAIL'}")
    print(f"  FastAPIBackend: {'PASS' if backend_test_passed else 'FAIL'}")
    
    all_passed = model_test_passed and backend_test_passed
    print(f"\nOverall: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    print("=" * 60)
    
    return all_passed


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
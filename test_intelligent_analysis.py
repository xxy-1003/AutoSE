"""
Test script for intelligent AutoSE analysis.
Run this to test the flood detector and alert system request.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from src.autose_platform.backend import FastAPIBackend

async def test_flood_detector():
    """Test the flood detector and alert system request."""
    print("Testing intelligent AutoSE analysis...")
    print("=" * 60)
    
    # Initialize backend
    backend = FastAPIBackend()
    
    # Test case 1: Flood detector and alert system
    test_cases = [
        "I need a flood detector and alert system",
        "I want a water leak detection system with alerts",
        "Set up flood detection for my basement",
        "I need temperature sensors for my server room",  # This should NOT recommend flood detector
        "I want door sensors for my office",  # This should NOT recommend flood detector
    ]
    
    for i, text in enumerate(test_cases, 1):
        print(f"\nTest Case {i}: '{text}'")
        print("-" * 40)
        
        try:
            result = await backend.analyze_intelligently(text)
            
            if result.get("no_exact_match", False):
                print("❌ No exact match found")
                print(f"Message: {result.get('message', '')}")
                if result.get("options"):
                    print("Options:")
                    for option in result.get("options", []):
                        if isinstance(option, dict):
                            print(f"  - {option.get('description', '')}")
                        else:
                            print(f"  - {option}")
            else:
                print("✅ Intelligent analysis successful")
                print(f"Goal: {result.get('analysis', {}).get('goal', 'N/A')}")
                
                # Check for irrelevant recommendations
                selected_products = result.get("selected_products", [])
                product_names = [p.get("name", "").lower() for p in selected_products]
                
                # Check for Part 7 violations
                if "flood" in text.lower() or "water" in text.lower():
                    if "temperature sensor" in " ".join(product_names):
                        print("❌ VIOLATION: Temperature Sensor recommended for Flood request!")
                    if "door sensor" in " ".join(product_names):
                        print("❌ VIOLATION: Door Sensor recommended for Flood request!")
                    if "light controller" in " ".join(product_names):
                        print("❌ VIOLATION: Light Controller recommended for Flood request!")
                
                # Show products
                if selected_products:
                    print(f"Recommended Products ({len(selected_products)}):")
                    for product in selected_products:
                        print(f"  - {product.get('name')} (${product.get('price', 0)})")
                
                # Show explanations
                explanations = result.get("explanations", [])
                if explanations:
                    print("Explanations:")
                    for exp in explanations[:2]:  # Show first 2
                        if isinstance(exp, dict):
                            print(f"  - {exp.get('product_name')}: {exp.get('explanation', '')[:80]}...")
                
                # Show alert questions if any
                if result.get("has_alert_questions", False):
                    print("Alert System Questions:")
                    for q in result.get("alert_system_questions", []):
                        print(f"  - {q}")
            
            print(f"Total Cost: ${result.get('total_cost', 0):,}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("Test completed!")

if __name__ == "__main__":
    asyncio.run(test_flood_detector())
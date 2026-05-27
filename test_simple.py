"""
Simple test to verify the intelligent AutoSE is working.
"""

import requests
import json

def test_intelligent_analysis():
    """Test the intelligent analysis endpoint."""
    print("Testing AutoSE Intelligent Analysis API...")
    print("=" * 60)
    
    # API endpoint
    api_endpoint = "http://localhost:8000"
    
    # Test cases
    test_cases = [
        "I need a flood detector and alert system",
        "I want water leak detection with phone alerts",
        "Set up flood detection for my home",
    ]
    
    for i, text in enumerate(test_cases, 1):
        print(f"\nTest {i}: '{text}'")
        print("-" * 40)
        
        try:
            # Make request
            response = requests.post(
                f"{api_endpoint}/api/analyze_intelligently",
                json={"text": text},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get("no_exact_match", False):
                    print("Response: No exact match found")
                    print(f"Message: {result.get('message', '')}")
                else:
                    print("✅ Success!")
                    print(f"Goal: {result.get('analysis', {}).get('goal', 'N/A')}")
                    
                    # Check products
                    products = result.get("selected_products", [])
                    if products:
                        print(f"Products recommended: {len(products)}")
                        for p in products:
                            print(f"  - {p.get('name')} (${p.get('price', 0)})")
                    
                    # Check explanations
                    explanations = result.get("explanations", [])
                    if explanations:
                        print(f"Explanations provided: {len(explanations)}")
                    
                    # Check for flood detector
                    product_names = [p.get("name", "").lower() for p in products]
                    if "flood" in text.lower() and any("flood" in name for name in product_names):
                        print("✅ Flood detector correctly recommended!")
                    
                    # Check for irrelevant products (Part 7)
                    irrelevant = ["temperature sensor", "door sensor", "light controller"]
                    for irr in irrelevant:
                        if any(irr in name for name in product_names):
                            print(f"❌ VIOLATION: {irr.title()} recommended for flood request!")
            else:
                print(f"❌ API Error: {response.status_code}")
                print(response.text)
                
        except requests.exceptions.ConnectionError:
            print("❌ Cannot connect to API. Make sure the backend is running:")
            print(f"  Run: python -m src.autose_platform.main")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("To start the backend server:")
    print("1. Open a new terminal")
    print("2. Run: cd \"c:\\Assignment\\APU hackathon\"")
    print("3. Run: python -m src.autose_platform.main")
    print("\nTo test with the web interface:")
    print("1. Start the backend server (above)")
    print("2. Open another terminal")
    print("3. Run: streamlit run chat_frontend.py")
    print("4. Open http://localhost:8501 in your browser")
    print("5. Type: 'I need a flood detector and alert system'")

if __name__ == "__main__":
    test_intelligent_analysis()
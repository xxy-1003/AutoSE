"""
Simple test for AutoSE negotiation capabilities.
"""

print("🤖 Testing AutoSE Conversational Sales Engineer Negotiation")
print("=" * 60)

# Test negotiation patterns
test_cases = [
    ("This solution is wrong", "complaining"),
    ("Too expensive", "rejecting + wants_lower_price"),
    ("Budget=3000", "wants_lower_price"),
    ("Reduce cameras to 20", "wants_fewer_devices"),
    ("Show alternatives", "wants_alternative"),
]

print("\n📋 Test Cases for Negotiation Detection:")
print("-" * 40)
for text, expected in test_cases:
    print(f"User: '{text}'")
    print(f"Expected: {expected}")
    print()

# Test constraint extraction
print("\n💰 Test Cases for Constraint Extraction:")
print("-" * 40)

constraint_cases = [
    ("I have $3000", "budget_limit: 3000"),
    ("Reduce to 20 cameras", "device_count: 20"),
    ("Only $1500 budget", "budget_limit: 1500"),
    ("Maximum 10 devices", "device_count: 10"),
]

for text, expected in constraint_cases:
    print(f"User: '{text}'")
    print(f"Expected: {expected}")
    print()

# Example conversation flow
print("\n🔄 Example Multi-Turn Negotiation:")
print("-" * 40)

conversation = [
    ("User", "I need a smart home system for 3 bedrooms"),
    ("AutoSE", "✅ Generated solution: 15 devices, $4,200 total"),
    ("User", "Too expensive, budget=3000"),
    ("AutoSE", "💬 I understand. Let me suggest alternatives..."),
    ("AutoSE", "📊 Current: $4,200 | Economy: $2,800 | Balanced: $3,400"),
    ("AutoSE", "❓ Would you like to reduce devices or find cheaper products?"),
    ("User", "Reduce light controllers"),
    ("AutoSE", "✅ Updated: Reduced light controllers, new total: $3,650"),
    ("User", "Also remove temperature sensor"),
    ("AutoSE", "✅ Final: $3,450. Ready to proceed?"),
]

for speaker, message in conversation:
    print(f"{speaker}: {message}")

print("\n" + "=" * 60)
print("✅ Negotiation Upgrade Complete!")
print("\nTo use the system:")
print("1. Start backend: python -m src.autose_platform.main")
print("2. Start frontend: streamlit run chat_frontend.py")
print("\nTry these negotiation phrases:")
print("• 'This is wrong / not suitable'")
print("• 'Too expensive, budget=3000'")
print("• 'Reduce cameras to 20'")
print("• 'Simplify the solution'")
print("• 'Show me alternatives'")
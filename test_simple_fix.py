#!/usr/bin/env python3
"""
Simple test to verify the Product object fix.
"""

import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

print("=" * 60)
print("Testing Product object fix")
print("=" * 60)

# Test 1: Check Product class exists
try:
    from autose_platform.models import Product
    print("✓ Product class imported successfully")
    
    # Create a test product
    test_product = Product(
        name="Test Server",
        power_w=1000,
        gpu_count=4,
        price=10000,
        max_cameras=50,
        port_count=8,
        capacity_w=0
    )
    
    print(f"✓ Created Product: {test_product.name}")
    print(f"  - price: ${test_product.price}")
    print(f"  - power_w: {test_product.power_w}W")
    print(f"  - gpu_count: {test_product.gpu_count}")
    print(f"  - max_cameras: {test_product.max_cameras}")
    
    # Test attribute access (not .get())
    print("✓ Attribute access works (not .get())")
    
except Exception as e:
    print(f"✗ Error: {e}")
    sys.exit(1)

# Test 2: Check product_retriever
try:
    from autose_platform.product_retriever import ProductRetriever
    print("\n✓ ProductRetriever imported successfully")
    
    retriever = ProductRetriever()
    print(f"✓ Created ProductRetriever")
    print(f"  - Catalog size: {len(retriever.catalog)}")
    
    # Check if catalog contains Product objects or dictionaries
    if retriever.catalog:
        first_item = retriever.catalog[0]
        if hasattr(first_item, 'name'):
            print(f"  - First item is a Product object: {first_item.name}")
        elif isinstance(first_item, dict):
            print(f"  - First item is a dictionary: {first_item.get('name', 'Unknown')}")
        else:
            print(f"  - First item type: {type(first_item)}")
    
except Exception as e:
    print(f"✗ Error: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("✓ Basic Product object test passed!")
print("=" * 60)
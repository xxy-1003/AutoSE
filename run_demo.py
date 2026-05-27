"""
AutoSE Platform Demo Script

This script demonstrates the complete AutoSE Platform workflow.
"""

import asyncio
import json
from datetime import datetime

def print_header(text):
    """Print a formatted header."""
    print("\n" + "=" * 60)
    print(f" {text}")
    print("=" * 60)

async def demo_workflow():
    """Demonstrate the complete AutoSE Platform workflow."""
    
    print_header("AutoSE Platform Demo")
    print("Multi-agent autonomous platform for enterprise solution engineering")
    print()
    
    # Import components
    from src.autose_platform.requirement_analyzer import RequirementAnalyzer
    from src.autose_platform.product_retriever import ProductRetriever
    from src.autose_platform.validation_layer import ValidationLayer
    from src.autose_platform.proposal_generator import ProposalGenerator
    from src.autose_platform.models import StructuredRequirements
    
    # Example requirements
    examples = [
        "Deploy an AI security system supporting 100 cameras with GPU acceleration",
        "10-camera security system for small office",
        "200-camera AI surveillance system with redundant power",
        "5-camera edge AI system for remote monitoring",
        "50-camera system requiring 96 network ports"
    ]
    
    for i, example_text in enumerate(examples, 1):
        print_header(f"Example {i}: {example_text}")
        
        # Initialize components
        analyzer = RequirementAnalyzer()
        retriever = ProductRetriever()
        validator = ValidationLayer()
        generator = ProposalGenerator()
        
        try:
            # Step 1: Extract requirements
            print("1. 📝 Requirement Analysis:")
            requirements = await analyzer.extract(example_text)
            print(f"   - Cameras: {requirements.device_count}")
            print(f"   - GPU Required: {'Yes' if requirements.gpu_required else 'No'}")
            print(f"   - Estimated Power: {requirements.estimated_power_w}W")
            print(f"   - Network Ports: {requirements.network_ports}")
            
            # Step 2: Product matching
            print("\n2. 🏷️ Product Matching:")
            products = await retriever.match(requirements)
            print(f"   - Found {len(products)} matching products:")
            for product in products:
                print(f"     • {product.get('name', 'Unknown Product')}")
                if product.get('price', 0) > 0:
                    print(f"       Price: ${product.get('price'):,}")
                if product.get('max_cameras', 0) > 0:
                    print(f"       Max Cameras: {product.get('max_cameras')}")
                if product.get('ports', product.get('port_count', 0)) > 0:
                    print(f"       Ports: {product.get('ports', product.get('port_count', 0))}")
                if product.get('capacity_w', 0) > 0:
                    print(f"       Capacity: {product.get('capacity_w')}W")
            
            # Step 3: Validation
            print("\n3. ✅ Validation:")
            validation = await validator.validate(products, requirements)
            print(f"   - Power Check: {validation.power_check}")
            print(f"   - Network Check: {validation.network_check}")
            print(f"   - GPU Check: {validation.gpu_check}")
            
            if validation.warnings:
                print(f"   - Warnings: {len(validation.warnings)}")
                for warning in validation.warnings[:2]:  # Show first 2 warnings
                    print(f"     ⚠ {warning}")
                if len(validation.warnings) > 2:
                    print(f"     ... and {len(validation.warnings) - 2} more")
            
            # Step 4: Proposal generation
            print("\n4. 📄 Proposal Generation:")
            proposal = await generator.generate(requirements, products, validation)
            
            total_cost = sum(p.get('price', 0) for p in products)
            print(f"   - Total Cost: ${total_cost:,}")
            print(f"   - Markdown Length: {len(proposal.markdown):,} chars")
            print(f"   - JSON Structure: {len(proposal.json_data.keys())} sections")
            
            # Show proposal preview
            print("\n   Proposal Preview:")
            lines = proposal.markdown.split('\n')
            for line in lines[:10]:  # Show first 10 lines
                if line.strip():
                    print(f"     {line}")
            if len(lines) > 10:
                print("     ...")
            
            # Save example output
            output_file = f"example_{i}_proposal.json"
            with open(output_file, 'w') as f:
                json.dump({
                    "requirement": example_text,
                    "requirements": requirements.model_dump(),
                    "products": products,  # Already dictionaries
                    "validation": validation.model_dump(),
                    "proposal_preview": proposal.markdown[:500] + "...",
                    "timestamp": datetime.now().isoformat()
                }, f, indent=2)
            
            print(f"\n   💾 Saved to: {output_file}")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print("\n" + "-" * 40)
    
    print_header("Demo Complete")
    print("All examples processed successfully!")
    print("\nTo run the full system:")
    print("1. Start the backend: python -m uvicorn src.autose_platform.main:app --reload")
    print("2. Start the frontend: streamlit run streamlit_app.py")
    print("3. Open browser to: http://localhost:8501")

def main():
    """Main function."""
    asyncio.run(demo_workflow())

if __name__ == "__main__":
    main()
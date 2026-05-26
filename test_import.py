"""
Test that all modified modules can be imported.
"""
import sys
sys.path.insert(0, '.')

try:
    from src.autose_platform.requirement_analyzer import RequirementAnalyzer
    print("✅ RequirementAnalyzer imported")
except Exception as e:
    print(f"❌ RequirementAnalyzer import failed: {e}")

try:
    from src.autose_platform.product_retriever import ProductRetriever
    print("✅ ProductRetriever imported")
except Exception as e:
    print(f"❌ ProductRetriever import failed: {e}")

try:
    from src.autose_platform.proposal_generator import ProposalGenerator
    print("✅ ProposalGenerator imported")
except Exception as e:
    print(f"❌ ProposalGenerator import failed: {e}")

try:
    from src.autose_platform.backend import FastAPIBackend
    print("✅ FastAPIBackend imported")
except Exception as e:
    print(f"❌ FastAPIBackend import failed: {e}")

print("\n✅ All imports tested!")
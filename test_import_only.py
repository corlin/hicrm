"""
Test just the import
"""

print("Starting import test...")

try:
    print("Importing MarketAgent...")
    from src.agents.professional.market_agent import MarketAgent
    print("✓ MarketAgent imported successfully")
    
    print("Creating instance...")
    agent = MarketAgent()
    print("✓ MarketAgent instance created")
    
except Exception as e:
    print(f"❌ Failed: {e}")
    import traceback
    traceback.print_exc()
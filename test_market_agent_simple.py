"""
Simple test for MarketAgent to check basic functionality
"""

import asyncio
from src.agents.professional.market_agent import MarketAgent, MarketAnalysisType, CompetitorType
from src.agents.base import AgentMessage, MessageType

async def test_basic_functionality():
    """Test basic MarketAgent functionality"""
    try:
        # Create MarketAgent instance
        agent = MarketAgent(
            agent_id="test_market_agent",
            name="测试市场专家"
        )
        print(f"✓ MarketAgent created successfully: {agent.name}")
        
        # Test capabilities
        print(f"✓ Agent has {len(agent.capabilities)} capabilities")
        for cap in agent.capabilities:
            print(f"  - {cap.name}: {cap.description}")
        
        # Test task analysis
        message = AgentMessage(
            type=MessageType.TASK,
            sender_id="test_user",
            content="请分析制造业的市场趋势",
            metadata={"industry": "制造业"}
        )
        
        analysis = await agent.analyze_task(message)
        print(f"✓ Task analysis completed: {analysis['task_type']}")
        
        # Test enum values
        print(f"✓ MarketAnalysisType enum: {list(MarketAnalysisType)}")
        print(f"✓ CompetitorType enum: {list(CompetitorType)}")
        
        print("\n🎉 All basic tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_basic_functionality())
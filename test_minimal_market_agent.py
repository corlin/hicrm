"""
Minimal MarketAgent test
"""

import asyncio
from src.agents.base import BaseAgent, AgentMessage, AgentResponse, AgentCapability

class MinimalMarketAgent(BaseAgent):
    """Minimal MarketAgent for testing"""
    
    def __init__(self, agent_id: str = "market_agent", name: str = "市场专家"):
        capabilities = [
            AgentCapability(
                name="score_lead",
                description="智能评估线索质量和转化潜力"
            )
        ]
        
        super().__init__(
            agent_id=agent_id,
            name=name,
            specialty="市场分析与线索管理",
            capabilities=capabilities
        )
        
        print(f"MinimalMarketAgent {self.name} 初始化完成")
    
    async def analyze_task(self, message: AgentMessage):
        return {
            "task_type": "general",
            "needs_collaboration": False
        }
    
    async def execute_task(self, message: AgentMessage, analysis):
        return {
            "success": True,
            "data": "test result"
        }
    
    async def generate_response(self, task_result=None, collaboration_result=None):
        return AgentResponse(
            content="测试响应",
            confidence=0.8,
            suggestions=["建议1", "建议2"]
        )

async def test_minimal_agent():
    try:
        print("Creating minimal market agent...")
        agent = MinimalMarketAgent()
        print("✓ Agent created successfully")
        
        message = AgentMessage(
            type="task",
            sender_id="test",
            content="测试消息"
        )
        
        print("Testing analyze_task...")
        analysis = await agent.analyze_task(message)
        print(f"✓ Analysis: {analysis}")
        
        print("Testing execute_task...")
        result = await agent.execute_task(message, analysis)
        print(f"✓ Result: {result}")
        
        print("Testing generate_response...")
        response = await agent.generate_response(result)
        print(f"✓ Response: {response.content}")
        
        print("🎉 All tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_minimal_agent())
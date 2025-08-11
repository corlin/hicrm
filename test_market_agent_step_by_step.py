"""
Step by step MarketAgent test
"""

print("Step 1: Import modules...")
import asyncio
from src.agents.base import BaseAgent, AgentMessage, AgentResponse, AgentCapability, MessageType

print("Step 2: Import enums...")
from enum import Enum

class MarketAnalysisType(str, Enum):
    """市场分析类型枚举"""
    INDUSTRY_TREND = "industry_trend"
    COMPETITIVE_LANDSCAPE = "competitive_landscape"

class CompetitorType(str, Enum):
    """竞争对手类型枚举"""
    DIRECT = "direct"
    INDIRECT = "indirect"

print("Step 3: Create basic MarketAgent class...")

class TestMarketAgent(BaseAgent):
    """Test MarketAgent"""
    
    def __init__(self, agent_id: str = "market_agent", name: str = "市场专家"):
        print(f"Initializing {name}...")
        
        capabilities = [
            AgentCapability(
                name="score_lead",
                description="智能评估线索质量和转化潜力"
            ),
            AgentCapability(
                name="analyze_market_trend",
                description="分析中文市场趋势和行业发展方向"
            )
        ]
        
        super().__init__(
            agent_id=agent_id,
            name=name,
            specialty="市场分析与线索管理",
            capabilities=capabilities
        )
        
        print(f"MarketAgent {self.name} 初始化完成")
    
    async def analyze_task(self, message: AgentMessage):
        content = message.content.lower()
        
        if "线索评分" in content:
            task_type = "lead_scoring"
        elif "市场趋势" in content:
            task_type = "market_trend_analysis"
        else:
            task_type = "general"
        
        return {
            "task_type": task_type,
            "needs_collaboration": False,
            "context": {}
        }
    
    async def execute_task(self, message: AgentMessage, analysis):
        return {
            "success": True,
            "analysis_type": analysis["task_type"],
            "data": {"result": "测试结果"}
        }
    
    async def generate_response(self, task_result=None, collaboration_result=None):
        if not task_result or not task_result.get("success"):
            return AgentResponse(
                content="处理失败",
                confidence=0.1,
                suggestions=["重试"]
            )
        
        return AgentResponse(
            content=f"分析完成: {task_result.get('analysis_type', 'unknown')}",
            confidence=0.8,
            suggestions=["查看详细结果", "进一步分析"]
        )

async def test_agent():
    try:
        print("Step 4: Create agent instance...")
        agent = TestMarketAgent()
        
        print("Step 5: Test task analysis...")
        message = AgentMessage(
            type=MessageType.TASK,
            sender_id="test_user",
            content="请分析制造业的市场趋势"
        )
        
        analysis = await agent.analyze_task(message)
        print(f"✓ Analysis result: {analysis}")
        
        print("Step 6: Test task execution...")
        result = await agent.execute_task(message, analysis)
        print(f"✓ Execution result: {result}")
        
        print("Step 7: Test response generation...")
        response = await agent.generate_response(result)
        print(f"✓ Response: {response.content}")
        print(f"✓ Confidence: {response.confidence}")
        print(f"✓ Suggestions: {response.suggestions}")
        
        print("🎉 All tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_agent())
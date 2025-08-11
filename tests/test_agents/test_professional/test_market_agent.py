"""
市场Agent单元测试
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
from typing import Dict, Any, List

from src.agents.professional.market_agent import (
    MarketAgent, 
    MarketAnalysisType,
    CompetitorType,
    LeadScoreDetail,
    MarketTrend,
    CompetitiveAnalysis,
    MarketingStrategy
)
from src.agents.base import AgentMessage, AgentResponse, MessageType


class TestMarketAgent:
    """市场Agent测试类"""
    
    @pytest.fixture
    def market_agent(self):
        """创建市场Agent实例"""
        return MarketAgent(
            agent_id="test_market_agent",
            name="测试市场专家"
        )
    
    @pytest.fixture
    def sample_message(self):
        """创建示例消息"""
        return AgentMessage(
            type=MessageType.TASK,
            sender_id="user_123",
            content="请分析制造业的市场趋势",
            metadata={
                "user_role": "marketing_manager",
                "industry": "制造业"
            }
        )
    
    @pytest.fixture
    def sample_lead_data(self):
        """创建示例线索数据"""
        return {
            "id": "lead_123",
            "name": "张经理",
            "company": "ABC制造公司",
            "industry": "制造业",
            "budget": 500000,
            "timeline": "3个月",
            "requirements": "需要ERP系统",
            "source": "website",
            "status": "new"
        }
    
    def test_market_agent_initialization(self, market_agent):
        """测试市场Agent初始化"""
        assert market_agent.name == "测试市场专家"
        assert market_agent.specialty == "市场分析与线索管理"
        assert len(market_agent.capabilities) == 5
        
        # 检查能力名称
        capability_names = [cap.name for cap in market_agent.capabilities]
        expected_capabilities = [
            "score_lead",
            "analyze_market_trend", 
            "competitive_analysis",
            "recommend_marketing_strategy",
            "market_data_analysis"
        ]
        
        for expected in expected_capabilities:
            assert expected in capability_names
    
    @pytest.mark.asyncio
    async def test_analyze_task_lead_scoring(self, market_agent, sample_message):
        """测试线索评分任务分析"""
        message = AgentMessage(
            type=MessageType.TASK,
            sender_id="user_123",
            content="请评估这个线索的质量",
            metadata={"lead_id": "lead_123"}
        )
        
        analysis = await market_agent.analyze_task(message)
        
        assert analysis["task_type"] == "lead_scoring"
        assert analysis["needs_collaboration"] == False
        assert analysis["context"]["lead_id"] == "lead_123"
    
    @pytest.mark.asyncio
    async def test_analyze_task_market_trend(self, market_agent, sample_message):
        """测试市场趋势分析任务分析"""
        analysis = await market_agent.analyze_task(sample_message)
        
        assert analysis["task_type"] == "market_trend_analysis"
        assert analysis["context"]["industry"] == "制造业"
    
    @pytest.mark.asyncio
    async def test_analyze_task_competitive_analysis(self, market_agent):
        """测试竞争分析任务分析"""
        message = AgentMessage(
            type=MessageType.TASK,
            sender_id="user_123",
            content="分析竞争对手华为的情况",
            metadata={"competitor": "华为"}
        )
        
        analysis = await market_agent.analyze_task(message)
        
        assert analysis["task_type"] == "competitive_analysis"
        assert analysis["context"]["competitor"] == "华为"
    
    @pytest.mark.asyncio
    async def test_analyze_task_with_collaboration_needed(self, market_agent):
        """测试需要协作的任务分析"""
        message = AgentMessage(
            type=MessageType.TASK,
            sender_id="user_123",
            content="分析市场趋势并制定销售策略",
            metadata={}
        )
        
        analysis = await market_agent.analyze_task(message)
        
        assert analysis["needs_collaboration"] == True
        assert "sales_agent" in analysis["required_agents"]
    
    @pytest.mark.asyncio
    @patch('src.agents.professional.market_agent.get_db')
    @patch('src.agents.professional.market_agent.rag_service')
    @patch('src.agents.professional.market_agent.llm_service')
    async def test_score_lead(self, mock_llm, mock_rag, mock_db, market_agent, sample_lead_data):
        """测试线索评分功能"""
        # Mock数据库和服务
        mock_db_session = AsyncMock()
        mock_db.return_value.__aenter__.return_value = mock_db_session
        
        # Mock线索数据
        mock_lead = Mock()
        for key, value in sample_lead_data.items():
            setattr(mock_lead, key, value)
        
        market_agent.lead_service.get_lead = AsyncMock(return_value=mock_lead)
        
        # Mock评分服务
        mock_base_score = Mock()
        mock_base_score.total_score = 85.0
        mock_base_score.score_factors = [
            {"name": "预算", "score": 90, "reason": "预算充足"},
            {"name": "时间线", "score": 80, "reason": "时间合理"}
        ]
        market_agent.scoring_service.calculate_lead_score = AsyncMock(return_value=mock_base_score)
        
        # Mock RAG服务
        mock_rag.query.return_value = Mock(
            answer="制造业线索评分要点...",
            confidence=0.8,
            sources=[]
        )
        
        # Mock LLM服务
        mock_llm.chat_completion.return_value = {
            "content": """
            转化概率评估：85%
            关键评分因子分析：
            • 预算因子：90分 - 预算充足，符合项目需求
            • 时间线因子：80分 - 时间安排合理
            风险因素识别：
            • 决策周期可能较长
            • 需要多方决策者参与
            跟进建议：
            • 尽快安排产品演示
            • 了解决策流程
            • 建立多层级关系
            """
        }
        
        # 执行测试
        result = await market_agent.score_lead("lead_123")
        
        # 验证结果
        assert isinstance(result, LeadScoreDetail)
        assert result.lead_id == "lead_123"
        assert result.total_score == 85.0
        assert result.confidence > 0.0
        assert len(result.score_factors) > 0
        assert len(result.recommendations) > 0
        assert len(result.risk_factors) > 0
        
        # 验证服务调用
        market_agent.lead_service.get_lead.assert_called_once_with("lead_123", mock_db_session)
        mock_rag.query.assert_called_once()
        mock_llm.chat_completion.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('src.agents.professional.market_agent.rag_service')
    @patch('src.agents.professional.market_agent.llm_service')
    async def test_analyze_market_trend(self, mock_llm, mock_rag, market_agent):
        """测试市场趋势分析功能"""
        # Mock RAG服务
        mock_rag.query.side_effect = [
            Mock(
                answer="制造业市场趋势向好，预计增长12%...",
                confidence=0.85,
                sources=[]
            ),
            Mock(
                answer="制造业行业报告显示...",
                confidence=0.80,
                sources=[]
            )
        ]
        
        # Mock LLM服务
        mock_llm.chat_completion.return_value = {
            "content": """
            行业发展趋势：上升
            市场增长率预测：12.5%
            关键驱动因素：
            • 数字化转型需求增长
            • 政策支持力度加大
            • 技术创新推动
            市场规模分析：
            市场规模：5000亿元
            未来3-5年预测：
            2024年：增长15%
            2025年：增长12%
            市场机会识别：
            • 智能制造领域
            • 绿色制造转型
            潜在威胁分析：
            • 国际竞争加剧
            • 原材料成本上升
            """
        }
        
        # 执行测试
        result = await market_agent.analyze_market_trend("制造业")
        
        # 验证结果
        assert isinstance(result, MarketTrend)
        assert result.industry == "制造业"
        assert result.trend_direction == "up"
        assert result.growth_rate == 12.5
        assert len(result.key_drivers) > 0
        assert len(result.opportunities) > 0
        assert len(result.threats) > 0
        assert result.confidence_score > 0.0
        
        # 验证服务调用
        assert mock_rag.query.call_count == 2
        mock_llm.chat_completion.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('src.agents.professional.market_agent.rag_service')
    @patch('src.agents.professional.market_agent.llm_service')
    async def test_generate_competitive_analysis(self, mock_llm, mock_rag, market_agent):
        """测试竞争分析功能"""
        # Mock RAG服务
        mock_rag.query.side_effect = [
            Mock(
                answer="华为竞争分析：技术实力强...",
                confidence=0.85,
                sources=[]
            ),
            Mock(
                answer="通信设备行业竞争格局...",
                confidence=0.80,
                sources=[]
            )
        ]
        
        # Mock LLM服务
        mock_llm.chat_completion.return_value = {
            "content": """
            竞争对手类型：直接竞争对手
            市场份额估算：25%
            核心优势分析：
            • 技术研发实力强
            • 品牌知名度高
            • 全球化布局完善
            主要劣势识别：
            • 国际市场受限
            • 成本控制压力
            产品/服务组合：
            产品：通信设备、智能手机、云服务
            定价策略分析：
            采用价值定价策略，注重技术溢价
            目标客户群体：
            • 大型企业客户
            • 政府机构
            • 运营商
            竞争优势评估：
            • 技术创新能力
            • 研发投入大
            威胁等级判断：高威胁
            """
        }
        
        # 执行测试
        result = await market_agent.generate_competitive_analysis("华为")
        
        # 验证结果
        assert isinstance(result, CompetitiveAnalysis)
        assert result.competitor_name == "华为"
        assert result.competitor_type == CompetitorType.DIRECT
        assert result.market_share == 25.0
        assert len(result.strengths) > 0
        assert len(result.weaknesses) > 0
        assert result.threat_level == "high"
        
        # 验证服务调用
        assert mock_rag.query.call_count == 2
        mock_llm.chat_completion.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('src.agents.professional.market_agent.rag_service')
    @patch('src.agents.professional.market_agent.llm_service')
    async def test_recommend_marketing_strategy(self, mock_llm, mock_rag, market_agent):
        """测试营销策略推荐功能"""
        # Mock RAG服务
        mock_rag.query.side_effect = [
            Mock(
                answer="制造业营销最佳实践...",
                confidence=0.85,
                sources=[]
            ),
            Mock(
                answer="制造业客户细分特征...",
                confidence=0.80,
                sources=[]
            )
        ]
        
        # Mock LLM服务
        mock_llm.chat_completion.return_value = {
            "content": """
            目标客户细分：
            大中型制造企业，年收入1-10亿元
            市场定位策略：
            专业的数字化转型解决方案提供商
            核心营销信息：
            • 提升生产效率
            • 降低运营成本
            • 数字化转型专家
            营销渠道组合：
            • 行业展会
            • 数字营销
            • 合作伙伴渠道
            • 直销团队
            具体营销战术：
            • 内容营销
            • 案例分享
            • 技术研讨会
            预算分配建议：
            数字营销：40%
            展会活动：30%
            内容制作：20%
            其他：10%
            执行时间表：
            第一阶段：市场调研
            第二阶段：策略执行
            第三阶段：效果评估
            成功指标设定：
            • 线索转化率提升20%
            • 品牌知名度提升15%
            • 销售额增长25%
            预期投资回报率：300%
            """
        }
        
        # 执行测试
        target_market = {
            "industry": "制造业",
            "region": "中国",
            "user_query": "制定制造业营销策略"
        }
        
        result = await market_agent.recommend_marketing_strategy(target_market)
        
        # 验证结果
        assert isinstance(result, MarketingStrategy)
        assert "制造企业" in result.target_segment
        assert len(result.key_messages) > 0
        assert len(result.channels) > 0
        assert len(result.success_metrics) > 0
        assert result.expected_roi == 300.0
        
        # 验证服务调用
        assert mock_rag.query.call_count == 2
        mock_llm.chat_completion.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_task_lead_scoring(self, market_agent):
        """测试执行线索评分任务"""
        message = AgentMessage(
            type=MessageType.TASK,
            sender_id="user_123",
            content="评估线索lead_123的质量"
        )
        
        context = {
            "lead_id": "lead_123",
            "user_role": "marketing_manager"
        }
        
        # Mock score_lead方法
        mock_score_detail = LeadScoreDetail(
            lead_id="lead_123",
            total_score=85.0,
            confidence=0.8,
            score_factors=[],
            recommendations=["建议1", "建议2"],
            risk_factors=["风险1"],
            scoring_date=datetime.now(),
            algorithm_version="v1.0"
        )
        
        market_agent.score_lead = AsyncMock(return_value=mock_score_detail)
        
        # 执行测试
        result = await market_agent._execute_lead_scoring(message, context)
        
        # 验证结果
        assert result["success"] == True
        assert result["analysis_type"] == "lead_scoring"
        assert result["response_type"] == "scoring_result"
        assert result["data"] == mock_score_detail
        
        # 验证方法调用
        market_agent.score_lead.assert_called_once_with("lead_123")
    
    @pytest.mark.asyncio
    async def test_execute_task_market_trend_analysis(self, market_agent):
        """测试执行市场趋势分析任务"""
        message = AgentMessage(
            type=MessageType.TASK,
            sender_id="user_123",
            content="分析制造业市场趋势"
        )
        
        context = {
            "industry": "制造业",
            "user_role": "marketing_manager"
        }
        
        # Mock analyze_market_trend方法
        mock_trend = MarketTrend(
            industry="制造业",
            trend_direction="up",
            growth_rate=12.5,
            key_drivers=["数字化", "政策支持"],
            market_size={"value": 5000, "unit": "亿"},
            forecast={"2024": 15.0},
            opportunities=["智能制造"],
            threats=["竞争加剧"],
            analysis_date=datetime.now(),
            confidence_score=0.85
        )
        
        market_agent.analyze_market_trend = AsyncMock(return_value=mock_trend)
        
        # 执行测试
        result = await market_agent._execute_market_trend_analysis(message, context)
        
        # 验证结果
        assert result["success"] == True
        assert result["analysis_type"] == "market_trend"
        assert result["response_type"] == "trend_analysis"
        assert result["data"] == mock_trend
        
        # 验证方法调用
        market_agent.analyze_market_trend.assert_called_once_with("制造业")
    
    @pytest.mark.asyncio
    async def test_generate_response_success(self, market_agent):
        """测试成功生成响应"""
        # Mock格式化方法
        market_agent._format_scoring_result_response = AsyncMock(
            return_value=("评分结果：85分", ["建议1", "建议2"])
        )
        market_agent._calculate_response_confidence = Mock(return_value=0.85)
        market_agent._generate_next_actions = Mock(return_value=["行动1", "行动2"])
        
        task_result = {
            "success": True,
            "analysis_type": "lead_scoring",
            "response_type": "scoring_result",
            "data": {"score": 85}
        }
        
        # 执行测试
        response = await market_agent.generate_response(task_result)
        
        # 验证结果
        assert isinstance(response, AgentResponse)
        assert response.content == "评分结果：85分"
        assert response.confidence == 0.85
        assert len(response.suggestions) == 2
        assert len(response.next_actions) == 2
    
    @pytest.mark.asyncio
    async def test_generate_response_failure(self, market_agent):
        """测试失败情况下的响应生成"""
        task_result = {
            "success": False,
            "error": "测试错误",
            "fallback_response": "处理失败"
        }
        
        # 执行测试
        response = await market_agent.generate_response(task_result)
        
        # 验证结果
        assert isinstance(response, AgentResponse)
        assert response.content == "处理失败"
        assert response.confidence == 0.1
        assert "测试错误" in str(response.metadata)
    
    @pytest.mark.asyncio
    async def test_mcp_tool_get_market_data(self, market_agent):
        """测试获取市场数据MCP工具"""
        # Mock RAG服务
        with patch('src.agents.professional.market_agent.rag_service') as mock_rag:
            mock_rag.query.return_value = Mock(
                answer="市场数据分析结果...",
                confidence=0.8,
                sources=[]
            )
            
            # 执行测试
            result = await market_agent._handle_get_market_data(
                data_source="industry_report",
                industry="制造业",
                region="中国"
            )
            
            # 验证结果
            assert result["success"] == True
            assert result["data"]["industry"] == "制造业"
            assert result["data"]["region"] == "中国"
            assert result["data"]["confidence"] == 0.8
    
    @pytest.mark.asyncio
    async def test_mcp_tool_analyze_competitor(self, market_agent):
        """测试分析竞争对手MCP工具"""
        # Mock generate_competitive_analysis方法
        mock_analysis = CompetitiveAnalysis(
            competitor_name="华为",
            competitor_type=CompetitorType.DIRECT,
            market_share=25.0,
            strengths=["技术强"],
            weaknesses=["成本高"],
            products=[],
            pricing_strategy="价值定价",
            target_customers=["企业"],
            competitive_advantages=["创新"],
            threat_level="high",
            analysis_date=datetime.now()
        )
        
        market_agent.generate_competitive_analysis = AsyncMock(return_value=mock_analysis)
        
        # 执行测试
        result = await market_agent._handle_analyze_competitor(competitor="华为")
        
        # 验证结果
        assert result["success"] == True
        assert result["competitor_analysis"]["competitor_name"] == "华为"
        assert result["competitor_analysis"]["threat_level"] == "high"
    
    @pytest.mark.asyncio
    async def test_mcp_tool_score_lead_batch(self, market_agent):
        """测试批量线索评分MCP工具"""
        # Mock score_lead方法
        mock_score_detail = LeadScoreDetail(
            lead_id="lead_123",
            total_score=85.0,
            confidence=0.8,
            score_factors=[],
            recommendations=["建议1", "建议2", "建议3"],
            risk_factors=[],
            scoring_date=datetime.now(),
            algorithm_version="v1.0"
        )
        
        market_agent.score_lead = AsyncMock(return_value=mock_score_detail)
        
        # 执行测试
        result = await market_agent._handle_score_lead_batch(
            lead_ids=["lead_123", "lead_456"]
        )
        
        # 验证结果
        assert result["success"] == True
        assert len(result["batch_results"]) == 2
        assert result["summary"]["total"] == 2
        assert result["summary"]["success"] == 2
    
    def test_extract_lead_id_from_message(self, market_agent):
        """测试从消息中提取线索ID"""
        content = "请评估线索lead_123的质量"
        lead_id = market_agent._extract_lead_id_from_message(content)
        assert lead_id == "123"
    
    def test_extract_industry_from_message(self, market_agent):
        """测试从消息中提取行业信息"""
        content = "分析制造业的市场趋势"
        industry = market_agent._extract_industry_from_message(content)
        assert industry == "制造业"
    
    def test_extract_competitor_from_message(self, market_agent):
        """测试从消息中提取竞争对手名称"""
        content = "分析华为公司的竞争情况"
        competitor = market_agent._extract_competitor_from_message(content)
        assert competitor == "华为"
    
    def test_extract_trend_direction(self, market_agent):
        """测试提取趋势方向"""
        content_up = "市场呈现上升趋势，增长明显"
        content_down = "市场下降，出现衰退"
        content_stable = "市场保持稳定"
        
        assert market_agent._extract_trend_direction(content_up) == "up"
        assert market_agent._extract_trend_direction(content_down) == "down"
        assert market_agent._extract_trend_direction(content_stable) == "stable"
    
    def test_extract_growth_rate(self, market_agent):
        """测试提取增长率"""
        content = "预计增长率为12.5%"
        growth_rate = market_agent._extract_growth_rate(content)
        assert growth_rate == 12.5
    
    def test_extract_market_share(self, market_agent):
        """测试提取市场份额"""
        content = "该公司市场份额为25.5%"
        market_share = market_agent._extract_market_share(content)
        assert market_share == 25.5
    
    def test_extract_threat_level(self, market_agent):
        """测试提取威胁等级"""
        content_high = "这是一个高威胁的竞争对手"
        content_medium = "中等威胁水平"
        content_low = "威胁较小"
        
        assert market_agent._extract_threat_level(content_high) == "high"
        assert market_agent._extract_threat_level(content_medium) == "medium"
        assert market_agent._extract_threat_level(content_low) == "low"
    
    def test_calculate_response_confidence(self, market_agent):
        """测试计算响应置信度"""
        task_result = {
            "analysis_type": "lead_scoring",
            "success": True
        }
        
        confidence = market_agent._calculate_response_confidence(task_result)
        assert confidence == 0.8  # lead_scoring类型的基础置信度
        
        # 测试协作结果提升置信度
        collaboration_result = {"success": True}
        confidence_with_collab = market_agent._calculate_response_confidence(
            task_result, collaboration_result
        )
        assert confidence_with_collab == 0.9
    
    def test_generate_next_actions(self, market_agent):
        """测试生成下一步行动建议"""
        task_result = {"analysis_type": "lead_scoring"}
        actions = market_agent._generate_next_actions(task_result)
        
        assert len(actions) == 3
        assert "制定线索跟进计划" in actions
        assert "分配高分线索给销售团队" in actions
        assert "优化线索评分模型" in actions


@pytest.mark.asyncio
class TestMarketAgentIntegration:
    """市场Agent集成测试"""
    
    @pytest.fixture
    def market_agent(self):
        """创建市场Agent实例"""
        return MarketAgent()
    
    @pytest.mark.asyncio
    async def test_full_lead_scoring_workflow(self, market_agent):
        """测试完整的线索评分工作流"""
        # 创建测试消息
        message = AgentMessage(
            type=MessageType.TASK,
            sender_id="user_123",
            content="请评估线索lead_123的质量",
            metadata={"lead_id": "lead_123"}
        )
        
        # Mock所有依赖服务
        with patch.multiple(
            'src.agents.professional.market_agent',
            get_db=AsyncMock(),
            rag_service=Mock(),
            llm_service=Mock()
        ) as mocks:
            # 配置Mock
            mock_db_session = AsyncMock()
            mocks['get_db'].return_value.__aenter__.return_value = mock_db_session
            
            # Mock线索数据
            mock_lead = Mock()
            mock_lead.id = "lead_123"
            mock_lead.name = "张经理"
            mock_lead.company = "ABC公司"
            mock_lead.industry = "制造业"
            mock_lead.budget = 500000
            
            market_agent.lead_service.get_lead = AsyncMock(return_value=mock_lead)
            
            # Mock评分服务
            mock_base_score = Mock()
            mock_base_score.total_score = 85.0
            mock_base_score.score_factors = []
            market_agent.scoring_service.calculate_lead_score = AsyncMock(return_value=mock_base_score)
            
            # Mock RAG和LLM
            mocks['rag_service'].query.return_value = Mock(
                answer="评分指导...", confidence=0.8, sources=[]
            )
            mocks['llm_service'].chat_completion.return_value = {
                "content": "评分分析结果..."
            }
            
            # 执行完整工作流
            response = await market_agent.process_message(message)
            
            # 验证响应
            assert isinstance(response, AgentResponse)
            assert response.confidence > 0.0
            assert len(response.suggestions) > 0
    
    @pytest.mark.asyncio
    async def test_error_handling(self, market_agent):
        """测试错误处理"""
        message = AgentMessage(
            type=MessageType.TASK,
            sender_id="user_123",
            content="无效的请求内容"
        )
        
        # 执行测试
        response = await market_agent.process_message(message)
        
        # 验证错误处理
        assert isinstance(response, AgentResponse)
        assert response.confidence >= 0.0
        assert "error" in response.metadata or response.content is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
"""
销售Agent测试

测试销售Agent的各项功能，包括客户分析、话术生成、机会评估等
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
from typing import Dict, Any

from src.agents.professional.sales_agent import (
    SalesAgent, CustomerAnalysis, TalkingPoint, OpportunityAssessment,
    ActionRecommendation, SalesStage, TalkingPointType
)
from src.agents.base import AgentMessage, MessageType
from src.models.customer import Customer, CompanySize, CustomerStatus
from src.models.opportunity import Opportunity


class TestSalesAgent:
    """销售Agent测试类"""
    
    @pytest.fixture
    async def sales_agent(self):
        """创建销售Agent实例"""
        agent = SalesAgent()
        return agent
    
    @pytest.fixture
    def sample_customer(self):
        """示例客户数据"""
        return Customer(
            id="customer_123",
            name="张经理",
            company="科技有限公司",
            industry="软件开发",
            size=CompanySize.MEDIUM,
            contact={
                "email": "zhang@example.com",
                "phone": "13800138000"
            },
            profile={
                "decision_making_style": "数据驱动",
                "communication_preference": "邮件+电话",
                "business_priorities": ["降本增效", "数字化转型"],
                "pain_points": ["系统集成复杂", "数据孤岛"],
                "budget": {"range": "50-100万", "decision_cycle": "3-6个月"}
            },
            status=CustomerStatus.QUALIFIED
        )
    
    @pytest.fixture
    def sample_opportunity(self):
        """示例销售机会数据"""
        return Opportunity(
            id="opp_123",
            name="CRM系统项目",
            customer_id="customer_123",
            value=800000.0,
            probability=0.6,
            expected_close_date=datetime.now(),
            stage=Mock(name="需求确认", order=2, probability=0.6)
        )
    
    @pytest.fixture
    def sample_message(self):
        """示例消息"""
        return AgentMessage(
            type=MessageType.TASK,
            sender_id="user_123",
            content="请分析客户ABC公司的情况",
            metadata={
                "customer_id": "customer_123",
                "user_role": "sales_rep"
            }
        )
    
    async def test_agent_initialization(self, sales_agent):
        """测试Agent初始化"""
        assert sales_agent.name == "销售专家"
        assert sales_agent.specialty == "销售专业支持"
        assert len(sales_agent.capabilities) == 5
        
        # 检查能力配置
        capability_names = [cap.name for cap in sales_agent.capabilities]
        expected_capabilities = [
            "customer_analysis",
            "generate_talking_points", 
            "assess_opportunity",
            "recommend_next_action",
            "crm_operations"
        ]
        
        for expected in expected_capabilities:
            assert expected in capability_names
    
    async def test_analyze_task_customer_analysis(self, sales_agent, sample_message):
        """测试客户分析任务识别"""
        message = AgentMessage(
            type=MessageType.TASK,
            sender_id="user_123",
            content="请帮我分析一下这个客户的情况",
            metadata={"customer_id": "customer_123"}
        )
        
        analysis = await sales_agent.analyze_task(message)
        
        assert analysis["task_type"] == "customer_analysis"
        assert analysis["needs_collaboration"] == False
        assert analysis["context"]["customer_id"] == "customer_123"
    
    async def test_analyze_task_talking_points(self, sales_agent):
        """测试话术生成任务识别"""
        message = AgentMessage(
            type=MessageType.TASK,
            sender_id="user_123",
            content="给我一些销售话术，怎么和客户开场比较好？"
        )
        
        analysis = await sales_agent.analyze_task(message)
        
        assert analysis["task_type"] == "talking_points"
        assert analysis["needs_collaboration"] == False
    
    async def test_analyze_task_opportunity_assessment(self, sales_agent):
        """测试机会评估任务识别"""
        message = AgentMessage(
            type=MessageType.TASK,
            sender_id="user_123",
            content="这个销售机会的成交概率怎么样？",
            metadata={"opportunity_id": "opp_123"}
        )
        
        analysis = await sales_agent.analyze_task(message)
        
        assert analysis["task_type"] == "opportunity_assessment"
        assert analysis["context"]["opportunity_id"] == "opp_123"
    
    async def test_analyze_task_with_collaboration_needed(self, sales_agent):
        """测试需要协作的任务识别"""
        message = AgentMessage(
            type=MessageType.TASK,
            sender_id="user_123",
            content="这个客户需要什么产品方案，市场竞争情况如何？"
        )
        
        analysis = await sales_agent.analyze_task(message)
        
        assert analysis["needs_collaboration"] == True
        assert "product_agent" in analysis["required_agents"]
        assert "market_agent" in analysis["required_agents"]
    
    @patch('src.agents.professional.sales_agent.get_db')
    @patch('src.agents.professional.sales_agent.rag_service')
    @patch('src.agents.professional.sales_agent.llm_service')
    async def test_analyze_customer(self, mock_llm, mock_rag, mock_db, sales_agent, sample_customer):
        """测试客户分析功能"""
        # Mock数据库查询
        mock_db_session = AsyncMock()
        mock_db.return_value.__aenter__.return_value = mock_db_session
        
        mock_customer_service = Mock()
        mock_customer_service.get_customer = AsyncMock(return_value=sample_customer)
        
        # Mock RAG服务
        mock_rag.query = AsyncMock(return_value=Mock(
            answer="客户分析最佳实践...",
            confidence=0.8
        ))
        
        # Mock LLM服务
        mock_llm.chat_completion = AsyncMock(return_value={
            "content": """
            客户画像总结：
            张经理是一位数据驱动的决策者，注重ROI分析。
            
            主要痛点：
            - 系统集成复杂，影响工作效率
            - 数据孤岛问题严重，缺乏统一视图
            
            购买信号：
            - 已明确表达数字化转型需求
            - 有明确的预算范围
            
            风险因素：
            - 决策周期较长，需要多方论证
            - 对新技术接受度需要评估
            
            推荐销售策略：
            建议采用顾问式销售方法，重点展示ROI价值。
            """
        })
        
        with patch('src.services.customer_service.CustomerService', return_value=mock_customer_service):
            analysis = await sales_agent.analyze_customer("customer_123")
        
        assert isinstance(analysis, CustomerAnalysis)
        assert analysis.customer_id == "customer_123"
        assert len(analysis.pain_points) > 0
        assert len(analysis.buying_signals) > 0
        assert analysis.confidence_score > 0
    
    @patch('src.agents.professional.sales_agent.rag_service')
    @patch('src.agents.professional.sales_agent.llm_service')
    async def test_generate_talking_points(self, mock_llm, mock_rag, sales_agent):
        """测试话术生成功能"""
        # Mock RAG服务
        mock_rag.query = AsyncMock(return_value=Mock(
            answer="销售话术模板...",
            confidence=0.8
        ))
        
        # Mock LLM服务
        mock_llm.chat_completion = AsyncMock(return_value={
            "content": """
            1. 开场白话术
            张经理您好，我是来自XX公司的销售顾问。了解到贵公司在数字化转型方面有需求...
            
            2. 价值主张表达
            我们的解决方案可以帮助您解决数据孤岛问题，预计可以提升30%的工作效率...
            
            3. 异议处理
            关于价格问题，我们可以从ROI角度来分析...
            """
        })
        
        sales_context = {
            "user_query": "需要一些开场白话术",
            "sales_stage": "prospecting",
            "industry": "软件开发"
        }
        
        talking_points = await sales_agent.generate_talking_points(sales_context)
        
        assert isinstance(talking_points, list)
        assert len(talking_points) > 0
        
        for point in talking_points:
            assert isinstance(point, TalkingPoint)
            assert point.content
            assert point.type in TalkingPointType
    
    @patch('src.agents.professional.sales_agent.get_db')
    @patch('src.agents.professional.sales_agent.rag_service')
    @patch('src.agents.professional.sales_agent.llm_service')
    async def test_assess_opportunity(self, mock_llm, mock_rag, mock_db, sales_agent, sample_opportunity):
        """测试机会评估功能"""
        # Mock数据库查询
        mock_db_session = AsyncMock()
        mock_db.return_value.__aenter__.return_value = mock_db_session
        
        mock_opportunity_service = Mock()
        mock_opportunity_service.get_opportunity = AsyncMock(return_value=sample_opportunity)
        
        # Mock RAG服务
        mock_rag.query = AsyncMock(return_value=Mock(
            answer="成功案例分析...",
            confidence=0.8
        ))
        
        # Mock LLM服务
        mock_llm.chat_completion = AsyncMock(return_value={
            "content": """
            成交概率分析：
            基于当前信息，成交概率约为65%
            
            风险等级评估：
            中等风险，主要风险在于竞争对手和预算审批
            
            关键成功因素：
            - 建立与决策者的良好关系
            - 展示明确的ROI价值
            - 提供完整的实施方案
            
            潜在障碍：
            - 预算审批流程复杂
            - 竞争对手价格优势
            
            推荐行动：
            - 安排高层会议
            - 准备详细ROI分析
            - 制定差异化竞争策略
            """
        })
        
        with patch('src.services.opportunity_service.OpportunityService', return_value=mock_opportunity_service):
            assessment = await sales_agent.assess_opportunity("opp_123")
        
        assert isinstance(assessment, OpportunityAssessment)
        assert assessment.opportunity_id == "opp_123"
        assert 0 <= assessment.win_probability <= 1
        assert assessment.risk_level in ["low", "medium", "high"]
        assert len(assessment.key_success_factors) > 0
    
    @patch('src.agents.professional.sales_agent.rag_service')
    @patch('src.agents.professional.sales_agent.llm_service')
    async def test_recommend_next_action(self, mock_llm, mock_rag, sales_agent):
        """测试行动建议功能"""
        # Mock RAG服务
        mock_rag.query = AsyncMock(return_value=Mock(
            answer="销售最佳实践...",
            confidence=0.8
        ))
        
        # Mock LLM服务
        mock_llm.chat_completion = AsyncMock(return_value={
            "content": """
            1. 高优先级 - 安排客户会议
            与关键决策者安排面对面会议，展示产品价值
            预期结果：获得明确购买意向
            执行时间：1周内
            所需资源：销售经理、产品专家
            成功指标：会议满意度、后续跟进意愿
            
            2. 中优先级 - 准备ROI分析
            制作详细的投资回报分析报告
            预期结果：量化产品价值
            执行时间：3-5天
            """
        })
        
        context = {
            "customer_id": "customer_123",
            "sales_stage": "proposal",
            "current_situation": "客户对产品感兴趣但担心投资回报"
        }
        
        recommendations = await sales_agent.recommend_next_action(context)
        
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        
        for rec in recommendations:
            assert isinstance(rec, ActionRecommendation)
            assert rec.priority in ["high", "medium", "low"]
            assert rec.description
            assert rec.expected_outcome
    
    async def test_mcp_tool_get_customer_info(self, sales_agent):
        """测试MCP工具 - 获取客户信息"""
        import uuid
        customer_uuid = str(uuid.uuid4())
        
        # Mock the customer object
        mock_customer = Mock()
        mock_customer.id = customer_uuid
        mock_customer.name = "张经理"
        mock_customer.company = "科技公司"
        mock_customer.industry = "软件"
        mock_customer.status = "active"
        mock_customer.contact = {"email": "test@example.com"}
        
        with patch('src.agents.professional.sales_agent.get_db') as mock_db:
            mock_db_session = AsyncMock()
            mock_db.return_value.__aenter__.return_value = mock_db_session
            
            with patch('src.services.customer_service.CustomerService') as mock_service_class:
                mock_service_instance = AsyncMock()
                mock_service_instance.get_customer = AsyncMock(return_value=mock_customer)
                mock_service_class.return_value = mock_service_instance
                
                result = await sales_agent._handle_get_customer_info(customer_uuid)
            
            assert result["success"] == True
            assert result["customer"]["id"] == customer_uuid
            assert result["customer"]["name"] == "张经理"
    
    async def test_mcp_tool_create_lead(self, sales_agent):
        """测试MCP工具 - 创建线索"""
        result = await sales_agent._handle_create_lead(
            name="李经理",
            company="新客户公司",
            email="li@example.com"
        )
        
        assert result["success"] == True
        assert "lead_id" in result
        assert result["message"] == "线索创建成功"
    
    async def test_execute_task_customer_analysis(self, sales_agent, sample_message):
        """测试执行客户分析任务"""
        analysis = {
            "task_type": "customer_analysis",
            "context": {"customer_id": "customer_123"}
        }
        
        with patch.object(sales_agent, '_execute_customer_analysis') as mock_execute:
            mock_execute.return_value = {
                "success": True,
                "analysis_type": "customer_analysis",
                "data": Mock(),
                "response_type": "structured"
            }
            
            result = await sales_agent.execute_task(sample_message, analysis)
            
            assert result["success"] == True
            assert result["analysis_type"] == "customer_analysis"
            mock_execute.assert_called_once()
    
    async def test_execute_task_error_handling(self, sales_agent, sample_message):
        """测试任务执行错误处理"""
        analysis = {
            "task_type": "customer_analysis",
            "context": {}
        }
        
        with patch.object(sales_agent, '_execute_customer_analysis') as mock_execute:
            mock_execute.side_effect = Exception("测试错误")
            
            result = await sales_agent.execute_task(sample_message, analysis)
            
            assert result["success"] == False
            assert "error" in result
            assert "fallback_response" in result
    
    async def test_generate_response_success(self, sales_agent):
        """测试成功响应生成"""
        task_result = {
            "success": True,
            "response_type": "structured",
            "data": CustomerAnalysis(
                customer_id="customer_123",
                profile_summary="测试客户画像",
                pain_points=["痛点1", "痛点2"],
                decision_makers=[],
                buying_signals=["信号1"],
                risk_factors=["风险1"],
                recommended_approach="推荐策略",
                confidence_score=0.8,
                analysis_date=datetime.now()
            )
        }
        
        response = await sales_agent.generate_response(task_result)
        
        assert response.confidence > 0.5
        assert "客户分析报告" in response.content
        assert len(response.suggestions) > 0
        assert len(response.next_actions) > 0
    
    async def test_generate_response_error(self, sales_agent):
        """测试错误响应生成"""
        task_result = {
            "success": False,
            "error": "测试错误",
            "fallback_response": "抱歉，处理失败"
        }
        
        response = await sales_agent.generate_response(task_result)
        
        assert response.confidence < 0.5
        assert "抱歉，处理失败" in response.content
        assert "error" in response.metadata
    
    async def test_extract_customer_id_from_message(self, sales_agent):
        """测试从消息中提取客户ID"""
        content = "请分析客户ID: customer_123 的情况"
        customer_id = sales_agent._extract_customer_id_from_message(content)
        assert customer_id == "customer_123"
        
        content_no_id = "请分析这个客户的情况"
        customer_id_none = sales_agent._extract_customer_id_from_message(content_no_id)
        assert customer_id_none is None
    
    async def test_extract_opportunity_id_from_message(self, sales_agent):
        """测试从消息中提取机会ID"""
        content = "机会编号：opp_456 的评估结果如何？"
        opp_id = sales_agent._extract_opportunity_id_from_message(content)
        assert opp_id == "opp_456"
    
    async def test_extract_section(self, sales_agent):
        """测试内容章节提取"""
        content = """
        客户画像总结：
        这是一个重要的客户
        
        主要痛点识别：
        痛点1
        痛点2
        """
        
        summary = sales_agent._extract_section(content, "客户画像总结")
        assert "重要的客户" in summary
        
        pain_points = sales_agent._extract_section(content, "主要痛点")
        assert "痛点1" in pain_points
    
    async def test_extract_list_items(self, sales_agent):
        """测试列表项提取"""
        content = """
        主要痛点：
        - 系统集成复杂
        - 数据孤岛严重
        • 成本控制困难
        1. 人员培训不足
        2. 技术更新缓慢
        """
        
        items = sales_agent._extract_list_items(content, "主要痛点")
        assert len(items) >= 3
        assert "系统集成复杂" in items
        assert "数据孤岛严重" in items
    
    async def test_extract_probability(self, sales_agent):
        """测试概率提取"""
        content = "成交概率：65%"
        prob = sales_agent._extract_probability(content)
        assert prob == 0.65
        
        content_decimal = "概率: 0.8"
        prob_decimal = sales_agent._extract_probability(content_decimal)
        assert prob_decimal == 0.8
    
    async def test_extract_risk_level(self, sales_agent):
        """测试风险等级提取"""
        content_high = "这是一个高风险项目"
        risk_high = sales_agent._extract_risk_level(content_high)
        assert risk_high == "high"
        
        content_medium = "风险适中，需要关注"
        risk_medium = sales_agent._extract_risk_level(content_medium)
        assert risk_medium == "medium"
        
        content_low = "风险较低，可以推进"
        risk_low = sales_agent._extract_risk_level(content_low)
        assert risk_low == "low"
    
    async def test_parse_talking_point(self, sales_agent):
        """测试话术点解析"""
        section = """
        开场白话术
        张经理您好，我是来自XX公司的销售顾问。
        了解到贵公司在数字化转型方面有需求，
        我们有一些成功案例想与您分享。
        """
        
        talking_point = sales_agent._parse_talking_point(section)
        
        assert talking_point is not None
        assert talking_point.type == TalkingPointType.OPENING
        assert "张经理您好" in talking_point.content
        assert talking_point.effectiveness_score > 0
    
    async def test_calculate_response_confidence(self, sales_agent):
        """测试响应置信度计算"""
        task_result_success = {"success": True}
        collaboration_result_success = {"success": True}
        
        confidence = sales_agent._calculate_response_confidence(
            task_result_success, 
            collaboration_result_success
        )
        
        assert 0.8 <= confidence <= 1.0
        
        task_result_fail = {"success": False}
        confidence_fail = sales_agent._calculate_response_confidence(
            task_result_fail, 
            None
        )
        
        assert confidence_fail < confidence
    
    async def test_generate_next_actions(self, sales_agent):
        """测试下一步行动生成"""
        task_result = {"response_type": "customer_analysis"}
        actions = sales_agent._generate_next_actions(task_result)
        
        assert isinstance(actions, list)
        assert len(actions) > 0
        assert "制定销售策略" in actions
    
    @pytest.mark.asyncio
    async def test_full_workflow_customer_analysis(self, sales_agent):
        """测试完整的客户分析工作流"""
        message = AgentMessage(
            type=MessageType.TASK,
            sender_id="user_123",
            content="请分析客户customer_123的情况",
            metadata={"customer_id": "customer_123"}
        )
        
        with patch.object(sales_agent, 'analyze_customer') as mock_analyze:
            mock_analyze.return_value = CustomerAnalysis(
                customer_id="customer_123",
                profile_summary="测试客户",
                pain_points=["痛点1"],
                decision_makers=[],
                buying_signals=["信号1"],
                risk_factors=["风险1"],
                recommended_approach="策略1",
                confidence_score=0.8,
                analysis_date=datetime.now()
            )
            
            # 执行完整流程
            analysis = await sales_agent.analyze_task(message)
            task_result = await sales_agent.execute_task(message, analysis)
            response = await sales_agent.generate_response(task_result)
            
            assert response.confidence > 0.5
            assert "客户分析报告" in response.content
            assert len(response.suggestions) > 0
    
    @pytest.mark.asyncio
    async def test_full_workflow_talking_points(self, sales_agent):
        """测试完整的话术生成工作流"""
        message = AgentMessage(
            type=MessageType.TASK,
            sender_id="user_123",
            content="给我一些销售开场白话术"
        )
        
        with patch.object(sales_agent, 'generate_talking_points') as mock_generate:
            mock_generate.return_value = [
                TalkingPoint(
                    type=TalkingPointType.OPENING,
                    content="您好，我是销售顾问...",
                    context="电话开场",
                    effectiveness_score=0.8,
                    usage_scenarios=["电话沟通"],
                    customization_notes="可调整"
                )
            ]
            
            # 执行完整流程
            analysis = await sales_agent.analyze_task(message)
            task_result = await sales_agent.execute_task(message, analysis)
            response = await sales_agent.generate_response(task_result)
            
            assert response.confidence > 0.5
            assert "销售话术建议" in response.content
            assert len(response.suggestions) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
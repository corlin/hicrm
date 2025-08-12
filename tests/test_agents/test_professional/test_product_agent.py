"""
产品Agent单元测试

测试ProductAgent的各项功能，包括产品匹配、技术方案生成、实施规划等。
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
from typing import Dict, Any, List

from src.agents.professional.product_agent import (
    ProductAgent, SolutionMatch, TechnicalProposal, ImplementationPlan,
    SolutionType, TechnicalComplexity, ImplementationPhase, ProductInfo
)
from src.agents.base import AgentMessage, AgentResponse, MessageType


class TestProductAgent:
    """产品Agent测试类"""
    
    @pytest.fixture
    def product_agent(self):
        """创建产品Agent实例"""
        return ProductAgent(
            agent_id="test_product_agent",
            name="测试产品专家"
        )
    
    @pytest.fixture
    def sample_message(self):
        """创建示例消息"""
        return AgentMessage(
            type=MessageType.TASK,
            sender_id="user_123",
            content="我需要一个CRM系统解决方案，要求支持客户管理、销售跟踪和报表分析",
            metadata={
                "customer_id": "customer_123",
                "budget_range": {"min": 50000, "max": 100000},
                "technical_complexity": "medium"
            }
        )
    
    @pytest.fixture
    def sample_customer_context(self):
        """创建示例客户上下文"""
        return {
            "customer_id": "customer_123",
            "requirements": ["客户管理", "销售跟踪", "报表分析"],
            "budget_range": {"min": 50000, "max": 100000},
            "technical_complexity": "medium"
        }
    
    def test_product_agent_initialization(self, product_agent):
        """测试产品Agent初始化"""
        assert product_agent.id == "test_product_agent"
        assert product_agent.name == "测试产品专家"
        assert product_agent.specialty == "产品方案与技术支持"
        assert len(product_agent.capabilities) == 5
        
        # 检查能力列表
        capability_names = [cap.name for cap in product_agent.capabilities]
        expected_capabilities = [
            "match_solution",
            "generate_technical_proposal", 
            "create_implementation_plan",
            "provide_technical_support",
            "product_database_access"
        ]
        
        for expected_cap in expected_capabilities:
            assert expected_cap in capability_names
    
    @pytest.mark.asyncio
    async def test_analyze_task_solution_matching(self, product_agent, sample_message):
        """测试方案匹配任务分析"""
        # 修改消息内容为方案匹配相关
        sample_message.content = "帮我匹配一个适合的CRM产品方案"
        
        analysis = await product_agent.analyze_task(sample_message)
        
        assert analysis["task_type"] == "solution_matching"
        assert analysis["needs_collaboration"] == False
        assert analysis["context"]["customer_id"] == "customer_123"
        assert analysis["context"]["technical_complexity"] == "medium"
    
    @pytest.mark.asyncio
    async def test_analyze_task_technical_proposal(self, product_agent):
        """测试技术方案任务分析"""
        message = AgentMessage(
            type=MessageType.TASK,
            sender_id="user_123",
            content="请生成一个详细的技术方案",
            metadata={"customer_id": "customer_456"}
        )
        
        analysis = await product_agent.analyze_task(message)
        
        assert analysis["task_type"] == "technical_proposal"
        assert analysis["context"]["customer_id"] == "customer_456"
    
    @pytest.mark.asyncio
    async def test_analyze_task_implementation_planning(self, product_agent):
        """测试实施规划任务分析"""
        message = AgentMessage(
            type=MessageType.TASK,
            sender_id="user_123",
            content="制定CRM系统的实施规划",
            metadata={}
        )
        
        analysis = await product_agent.analyze_task(message)
        
        assert analysis["task_type"] == "implementation_planning"
    
    @pytest.mark.asyncio
    async def test_analyze_task_with_collaboration_needed(self, product_agent):
        """测试需要协作的任务分析"""
        message = AgentMessage(
            type=MessageType.TASK,
            sender_id="user_123",
            content="需要产品方案，还要考虑销售策略和市场分析",
            metadata={}
        )
        
        analysis = await product_agent.analyze_task(message)
        
        assert analysis["needs_collaboration"] == True
        assert "sales_agent" in analysis["required_agents"]
        assert "market_agent" in analysis["required_agents"]
        assert analysis["collaboration_type"] == "sequential"
    
    def test_extract_requirements_from_message(self, product_agent):
        """测试从消息中提取需求"""
        content = "我需要客户管理功能，要求支持销售跟踪，希望有报表分析能力"
        
        requirements = product_agent._extract_requirements_from_message(content)
        
        assert len(requirements) > 0
        assert any("客户管理" in req for req in requirements)
    
    def test_extract_customer_id_from_message(self, product_agent):
        """测试从消息中提取客户ID"""
        content = "为客户ABC公司制定方案"
        
        customer_id = product_agent._extract_customer_id_from_message(content)
        
        assert customer_id == "ABC"
    
    def test_extract_timeline_from_message(self, product_agent):
        """测试从消息中提取时间线"""
        content = "需要在3个月内完成实施"
        
        timeline = product_agent._extract_timeline_from_message(content)
        
        assert timeline == "3个月"
    
    def test_extract_solution_type(self, product_agent):
        """测试提取解决方案类型"""
        content_standard = "标准方案就可以"
        content_customized = "需要定制化方案"
        content_enterprise = "企业级解决方案"
        
        assert product_agent._extract_solution_type(content_standard) == SolutionType.STANDARD
        assert product_agent._extract_solution_type(content_customized) == SolutionType.CUSTOMIZED
        assert product_agent._extract_solution_type(content_enterprise) == SolutionType.ENTERPRISE
    
    def test_extract_complexity(self, product_agent):
        """测试提取技术复杂度"""
        content_low = "简单的系统就行"
        content_medium = "中等复杂度"
        content_high = "高复杂度系统"
        content_very_high = "极高复杂度"
        
        assert product_agent._extract_complexity(content_low) == TechnicalComplexity.LOW
        assert product_agent._extract_complexity(content_medium) == TechnicalComplexity.MEDIUM
        assert product_agent._extract_complexity(content_high) == TechnicalComplexity.HIGH
        assert product_agent._extract_complexity(content_very_high) == TechnicalComplexity.VERY_HIGH
    
    def test_extract_timeline(self, product_agent):
        """测试提取时间线"""
        content = "预计需要6个月完成"
        
        timeline = product_agent._extract_timeline(content)
        
        assert timeline == "6个月"
    
    def test_extract_cost_estimate(self, product_agent):
        """测试提取成本估算"""
        content = "预算大概50万到100万之间"
        
        cost_estimate = product_agent._extract_cost_estimate(content)
        
        assert "万" in cost_estimate["estimated_range"]
        assert cost_estimate["currency"] == "CNY"
    
    def test_extract_list_items(self, product_agent):
        """测试提取列表项"""
        content = """
        主要收益：
        - 提高销售效率
        - 改善客户体验
        - 增强数据分析能力
        """
        
        benefits = product_agent._extract_list_items(content, "主要收益")
        
        assert len(benefits) == 3
        assert "提高销售效率" in benefits
        assert "改善客户体验" in benefits
        assert "增强数据分析能力" in benefits
    
    def test_calculate_match_score(self, product_agent):
        """测试计算匹配分数"""
        content = "这是一个详细的匹配分析内容，包含了大量的技术细节和业务分析。" * 20
        rag_confidence = 0.8
        
        score = product_agent._calculate_match_score(content, rag_confidence)
        
        assert 0.0 <= score <= 1.0
        assert isinstance(score, float)
    
    @pytest.mark.asyncio
    @patch('src.agents.professional.product_agent.rag_service')
    @patch('src.agents.professional.product_agent.llm_service')
    async def test_match_solution(self, mock_llm_service, mock_rag_service, product_agent, sample_customer_context):
        """测试产品方案匹配"""
        # Mock RAG服务响应
        mock_rag_result = Mock()
        mock_rag_result.answer = "推荐CRM产品A和产品B"
        mock_rag_result.confidence = 0.85
        mock_rag_result.sources = ["产品目录", "解决方案模板"]
        mock_rag_service.query = AsyncMock(return_value=mock_rag_result)
        
        # Mock LLM服务响应
        mock_llm_response = {
            "content": """
            推荐产品列表：
            产品：CRM系统标准版，功能完善，适合中小企业。
            
            解决方案类型：标准方案
            技术匹配度：高
            业务匹配度：高
            实施复杂度：中等
            预估时间：3-6个月
            预估成本：50-80万元
            
            主要收益：
            - 提高销售效率
            - 改善客户管理
            
            潜在风险：
            - 数据迁移风险
            - 用户培训需求
            """
        }
        mock_llm_service.chat_completion = AsyncMock(return_value=mock_llm_response)
        
        requirements = ["客户管理", "销售跟踪", "报表分析"]
        
        result = await product_agent.match_solution(requirements, sample_customer_context)
        
        assert isinstance(result, SolutionMatch)
        assert result.customer_id == "customer_123"
        assert result.requirements == requirements
        assert len(result.recommended_products) > 0
        assert result.solution_type in [SolutionType.STANDARD, SolutionType.CUSTOMIZED, SolutionType.HYBRID, SolutionType.ENTERPRISE]
        assert 0.0 <= result.match_score <= 1.0
        assert result.implementation_complexity in [TechnicalComplexity.LOW, TechnicalComplexity.MEDIUM, TechnicalComplexity.HIGH, TechnicalComplexity.VERY_HIGH]
        assert len(result.benefits) > 0
        assert len(result.risks) > 0
    
    @pytest.mark.asyncio
    @patch('src.agents.professional.product_agent.rag_service')
    @patch('src.agents.professional.product_agent.llm_service')
    @patch('src.agents.professional.product_agent.get_db')
    async def test_generate_technical_proposal(self, mock_get_db, mock_llm_service, mock_rag_service, product_agent):
        """测试生成技术方案"""
        # Mock数据库和客户服务
        mock_db = AsyncMock()
        mock_get_db.return_value.__aenter__.return_value = mock_db
        
        mock_customer = Mock()
        mock_customer.name = "张三"
        mock_customer.company = "ABC公司"
        mock_customer.industry = "制造业"
        mock_customer.size = "medium"
        
        with patch('src.agents.professional.product_agent.CustomerService') as mock_customer_service:
            mock_service_instance = AsyncMock()
            mock_service_instance.get_customer.return_value = mock_customer
            mock_customer_service.return_value = mock_service_instance
            
            # Mock RAG服务响应
            mock_rag_result = Mock()
            mock_rag_result.answer = "制造业CRM技术方案参考"
            mock_rag_result.confidence = 0.8
            mock_rag_service.query = AsyncMock(return_value=mock_rag_result)
            
            # Mock LLM服务响应
            mock_llm_response = {
                "content": """
                方案概述：为ABC公司提供定制化CRM解决方案
                
                技术架构设计：
                - 前端：React + TypeScript
                - 后端：Node.js + Express
                - 数据库：PostgreSQL
                
                实施阶段规划：
                1. 需求分析阶段（2周）
                2. 系统开发阶段（8周）
                3. 测试部署阶段（2周）
                
                成功标准：
                - 系统稳定运行
                - 用户满意度达到90%
                """
            }
            mock_llm_service.chat_completion = AsyncMock(return_value=mock_llm_response)
            
            solution_requirements = {
                "user_query": "需要CRM技术方案",
                "technical_complexity": "medium",
                "budget_range": {"min": 50000, "max": 100000}
            }
            
            result = await product_agent.generate_technical_proposal("customer_123", solution_requirements)
            
            assert isinstance(result, TechnicalProposal)
            assert result.customer_id == "customer_123"
            assert result.proposal_id.startswith("proposal_")
            assert "ABC公司" in result.solution_overview
            assert len(result.implementation_phases) > 0
            assert len(result.success_criteria) > 0
            assert result.validity_period == 30
    
    @pytest.mark.asyncio
    @patch('src.agents.professional.product_agent.rag_service')
    @patch('src.agents.professional.product_agent.llm_service')
    async def test_create_implementation_plan(self, mock_llm_service, mock_rag_service, product_agent):
        """测试创建实施规划"""
        # Mock RAG服务响应
        mock_rag_result = Mock()
        mock_rag_result.answer = "中等复杂度项目实施最佳实践"
        mock_rag_result.confidence = 0.8
        mock_rag_service.query = AsyncMock(return_value=mock_rag_result)
        
        # Mock LLM服务响应
        mock_llm_response = {
            "content": """
            项目阶段划分：
            1. 项目启动阶段
            2. 需求分析阶段
            3. 系统开发阶段
            4. 测试部署阶段
            
            关键里程碑：
            - 项目启动
            - 需求确认
            - 开发完成
            - 系统上线
            
            成功指标：
            - 按时交付
            - 质量达标
            - 用户满意
            """
        }
        mock_llm_service.chat_completion = AsyncMock(return_value=mock_llm_response)
        
        project_scope = {
            "description": "CRM系统实施项目",
            "customer_id": "customer_123",
            "technical_complexity": "medium"
        }
        
        result = await product_agent.create_implementation_plan(project_scope)
        
        assert isinstance(result, ImplementationPlan)
        assert result.customer_id == "customer_123"
        assert result.plan_id.startswith("plan_")
        assert "CRM" in result.project_name
        assert len(result.phases) > 0
        assert len(result.milestones) > 0
        assert len(result.success_metrics) > 0
    
    @pytest.mark.asyncio
    @patch('src.agents.professional.product_agent.rag_service')
    @patch('src.agents.professional.product_agent.llm_service')
    async def test_provide_technical_support(self, mock_llm_service, mock_rag_service, product_agent):
        """测试提供技术支持"""
        # Mock RAG服务响应
        mock_rag_result = Mock()
        mock_rag_result.answer = "技术文档参考"
        mock_rag_result.confidence = 0.8
        mock_rag_result.sources = ["技术文档", "故障排除指南"]
        mock_rag_service.query = AsyncMock(return_value=mock_rag_result)
        
        # Mock LLM服务响应
        mock_llm_response = {
            "content": """
            问题分析：数据库连接问题
            解决方案：检查数据库配置和网络连接
            实施步骤：
            1. 检查数据库服务状态
            2. 验证连接参数
            3. 测试网络连通性
            """
        }
        mock_llm_service.chat_completion = AsyncMock(return_value=mock_llm_response)
        
        technical_question = "数据库连接失败怎么办？"
        context = {"urgency": "high"}
        
        result = await product_agent.provide_technical_support(technical_question, context)
        
        assert result["question"] == technical_question
        assert "数据库" in result["answer"]
        assert result["urgency"] == "high"
        assert 0.0 <= result["confidence"] <= 1.0
        assert len(result["sources"]) > 0
    
    @pytest.mark.asyncio
    async def test_execute_task_solution_matching(self, product_agent, sample_message):
        """测试执行方案匹配任务"""
        analysis = {
            "task_type": "solution_matching",
            "context": {
                "customer_id": "customer_123",
                "budget_range": {"min": 50000, "max": 100000}
            }
        }
        
        with patch.object(product_agent, 'match_solution') as mock_match_solution:
            mock_solution_match = Mock(spec=SolutionMatch)
            mock_solution_match.customer_id = "customer_123"
            mock_solution_match.match_score = 0.85
            mock_match_solution.return_value = mock_solution_match
            
            result = await product_agent.execute_task(sample_message, analysis)
            
            assert result["success"] == True
            assert result["analysis_type"] == "solution_matching"
            assert result["response_type"] == "solution_match"
            mock_match_solution.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_task_technical_proposal(self, product_agent):
        """测试执行技术方案任务"""
        message = AgentMessage(
            type=MessageType.TASK,
            sender_id="user_123",
            content="生成技术方案",
            metadata={}
        )
        
        analysis = {
            "task_type": "technical_proposal",
            "context": {"customer_id": "customer_123"}
        }
        
        with patch.object(product_agent, 'generate_technical_proposal') as mock_generate_proposal:
            mock_proposal = Mock(spec=TechnicalProposal)
            mock_proposal.customer_id = "customer_123"
            mock_generate_proposal.return_value = mock_proposal
            
            result = await product_agent.execute_task(message, analysis)
            
            assert result["success"] == True
            assert result["analysis_type"] == "technical_proposal"
            assert result["response_type"] == "technical_proposal"
            mock_generate_proposal.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_task_implementation_planning(self, product_agent):
        """测试执行实施规划任务"""
        message = AgentMessage(
            type=MessageType.TASK,
            sender_id="user_123",
            content="制定实施规划",
            metadata={}
        )
        
        analysis = {
            "task_type": "implementation_planning",
            "context": {}
        }
        
        with patch.object(product_agent, 'create_implementation_plan') as mock_create_plan:
            mock_plan = Mock(spec=ImplementationPlan)
            mock_plan.customer_id = "customer_123"
            mock_create_plan.return_value = mock_plan
            
            result = await product_agent.execute_task(message, analysis)
            
            assert result["success"] == True
            assert result["analysis_type"] == "implementation_planning"
            assert result["response_type"] == "implementation_plan"
            mock_create_plan.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_task_technical_support(self, product_agent):
        """测试执行技术支持任务"""
        message = AgentMessage(
            type=MessageType.TASK,
            sender_id="user_123",
            content="技术问题咨询",
            metadata={}
        )
        
        analysis = {
            "task_type": "technical_support",
            "context": {}
        }
        
        with patch.object(product_agent, 'provide_technical_support') as mock_provide_support:
            mock_support_response = {
                "question": "技术问题咨询",
                "answer": "技术解答",
                "confidence": 0.8
            }
            mock_provide_support.return_value = mock_support_response
            
            result = await product_agent.execute_task(message, analysis)
            
            assert result["success"] == True
            assert result["analysis_type"] == "technical_support"
            assert result["response_type"] == "technical_support"
            mock_provide_support.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_task_error_handling(self, product_agent, sample_message):
        """测试任务执行错误处理"""
        analysis = {
            "task_type": "solution_matching",
            "context": {}
        }
        
        with patch.object(product_agent, 'match_solution', side_effect=Exception("测试错误")):
            result = await product_agent.execute_task(sample_message, analysis)
            
            assert result["success"] == False
            assert "error" in result
            assert "fallback_response" in result
    
    @pytest.mark.asyncio
    async def test_generate_response_success(self, product_agent):
        """测试成功生成响应"""
        task_result = {
            "success": True,
            "response_type": "solution_match",
            "data": Mock(spec=SolutionMatch)
        }
        
        with patch.object(product_agent, '_format_solution_match_response') as mock_format:
            mock_format.return_value = ("测试响应内容", ["建议1", "建议2"])
            
            response = await product_agent.generate_response(task_result)
            
            assert isinstance(response, AgentResponse)
            assert response.content == "测试响应内容"
            assert len(response.suggestions) == 2
            assert response.confidence > 0
    
    @pytest.mark.asyncio
    async def test_generate_response_failure(self, product_agent):
        """测试失败响应生成"""
        task_result = {
            "success": False,
            "error": "测试错误",
            "fallback_response": "抱歉，处理失败"
        }
        
        response = await product_agent.generate_response(task_result)
        
        assert isinstance(response, AgentResponse)
        assert response.content == "抱歉，处理失败"
        assert response.confidence == 0.1
        assert "error" in response.metadata
    
    @pytest.mark.asyncio
    async def test_generate_response_with_collaboration(self, product_agent):
        """测试带协作结果的响应生成"""
        task_result = {
            "success": True,
            "response_type": "solution_match",
            "data": Mock(spec=SolutionMatch)
        }
        
        collaboration_result = {
            "success": True,
            "collaboration_results": [
                {"agent_id": "sales_agent", "result": "销售建议"}
            ]
        }
        
        with patch.object(product_agent, '_format_solution_match_response') as mock_format:
            mock_format.return_value = ("基础响应", ["建议1"])
            
            with patch.object(product_agent, '_integrate_collaboration_result') as mock_integrate:
                mock_integrate.return_value = "协作建议"
                
                response = await product_agent.generate_response(task_result, collaboration_result)
                
                assert isinstance(response, AgentResponse)
                assert "协作建议" in response.content
    
    @pytest.mark.asyncio
    async def test_format_solution_match_response(self, product_agent):
        """测试格式化方案匹配响应"""
        mock_product = ProductInfo(
            id="product_1",
            name="CRM标准版",
            category="CRM系统",
            description="适合中小企业的CRM解决方案",
            features=[],
            technical_specs={},
            pricing={},
            compatibility=[],
            target_industries=[],
            implementation_time="3-6个月"
        )
        
        solution_match = SolutionMatch(
            customer_id="customer_123",
            requirements=["客户管理", "销售跟踪"],
            recommended_products=[mock_product],
            solution_type=SolutionType.STANDARD,
            match_score=0.85,
            technical_fit={},
            business_fit={},
            implementation_complexity=TechnicalComplexity.MEDIUM,
            estimated_timeline="3-6个月",
            estimated_cost={"estimated_range": "50-80万元"},
            risks=["数据迁移风险"],
            benefits=["提高效率", "改善体验"],
            alternatives=[],
            match_date=datetime.now()
        )
        
        content, suggestions = await product_agent._format_solution_match_response(solution_match)
        
        assert "产品方案匹配结果" in content
        assert "CRM标准版" in content
        assert "85.0%" in content
        assert "3-6个月" in content
        assert len(suggestions) > 0
    
    @pytest.mark.asyncio
    async def test_format_technical_proposal_response(self, product_agent):
        """测试格式化技术方案响应"""
        proposal = TechnicalProposal(
            proposal_id="proposal_123",
            customer_id="customer_123",
            solution_overview="CRM技术方案概述",
            technical_architecture={},
            implementation_phases=[
                {"phase": "规划阶段", "duration": "2周"},
                {"phase": "开发阶段", "duration": "8周"}
            ],
            resource_requirements={},
            timeline={},
            deliverables=[
                {"name": "需求文档", "description": "详细需求规格"}
            ],
            success_criteria=["系统稳定运行", "用户满意度90%"],
            risk_mitigation=[],
            support_model={"support_type": "7x24小时支持"},
            proposal_date=datetime.now(),
            validity_period=30
        )
        
        content, suggestions = await product_agent._format_technical_proposal_response(proposal)
        
        assert "技术方案建议" in content
        assert "CRM技术方案概述" in content
        assert "规划阶段" in content
        assert "需求文档" in content
        assert "30天" in content
        assert len(suggestions) > 0
    
    @pytest.mark.asyncio
    async def test_format_implementation_plan_response(self, product_agent):
        """测试格式化实施计划响应"""
        plan = ImplementationPlan(
            plan_id="plan_123",
            project_name="CRM实施项目",
            customer_id="customer_123",
            solution_components=[],
            phases=[
                {"phase_name": "项目启动", "duration": "1周"}
            ],
            milestones=[
                {"milestone_name": "项目启动", "date": "第1周"}
            ],
            resource_allocation={
                "project_manager": {"allocation": "100%", "duration": "全程"}
            },
            timeline={},
            dependencies=[],
            risk_assessment=[
                {"risk_name": "技术风险", "mitigation_strategy": "技术预研"}
            ],
            quality_assurance={},
            change_management={},
            success_metrics=["按时交付", "质量达标"],
            plan_date=datetime.now()
        )
        
        content, suggestions = await product_agent._format_implementation_plan_response(plan)
        
        assert "项目实施规划" in content
        assert "CRM实施项目" in content
        assert "项目启动" in content
        assert "按时交付" in content
        assert len(suggestions) > 0
    
    def test_calculate_response_confidence(self, product_agent):
        """测试计算响应置信度"""
        # 测试成功任务结果
        task_result_success = {
            "success": True,
            "data": {"confidence": 0.9}
        }
        
        confidence = product_agent._calculate_response_confidence(task_result_success)
        assert 0.8 <= confidence <= 1.0
        
        # 测试失败任务结果
        task_result_failure = {
            "success": False
        }
        
        confidence = product_agent._calculate_response_confidence(task_result_failure)
        assert confidence == 0.3
        
        # 测试带协作结果
        collaboration_result = {"success": True}
        confidence = product_agent._calculate_response_confidence(task_result_success, collaboration_result)
        assert confidence >= 0.8
    
    def test_generate_next_actions(self, product_agent):
        """测试生成下一步行动建议"""
        # 测试方案匹配的下一步行动
        task_result = {"response_type": "solution_match"}
        actions = product_agent._generate_next_actions(task_result)
        
        assert len(actions) > 0
        assert any("技术方案" in action for action in actions)
        
        # 测试技术方案的下一步行动
        task_result = {"response_type": "technical_proposal"}
        actions = product_agent._generate_next_actions(task_result)
        
        assert len(actions) > 0
        assert any("实施计划" in action for action in actions)
    
    @pytest.mark.asyncio
    async def test_mcp_get_product_info(self, product_agent):
        """测试MCP获取产品信息工具"""
        with patch('src.agents.professional.product_agent.rag_service') as mock_rag_service:
            mock_rag_result = Mock()
            mock_rag_result.answer = "产品详细信息"
            mock_rag_result.confidence = 0.8
            mock_rag_result.sources = ["产品目录"]
            mock_rag_service.query = AsyncMock(return_value=mock_rag_result)
            
            result = await product_agent._handle_get_product_info("product_123")
            
            assert result["success"] == True
            assert result["product_id"] == "product_123"
            assert "产品详细信息" in result["product_info"]
    
    @pytest.mark.asyncio
    async def test_mcp_search_solutions(self, product_agent):
        """测试MCP搜索解决方案工具"""
        with patch('src.agents.professional.product_agent.rag_service') as mock_rag_service:
            mock_rag_result = Mock()
            mock_rag_result.answer = "搜索到的解决方案"
            mock_rag_result.confidence = 0.8
            mock_rag_service.query = AsyncMock(return_value=mock_rag_result)
            
            result = await product_agent._handle_search_solutions(
                query="CRM解决方案",
                filters={"industry": "制造业"}
            )
            
            assert result["success"] == True
            assert result["query"] == "CRM解决方案"
            assert "搜索到的解决方案" in result["solutions"]
    
    @pytest.mark.asyncio
    async def test_mcp_generate_quote(self, product_agent):
        """测试MCP生成报价工具"""
        result = await product_agent._handle_generate_quote(
            customer_id="customer_123",
            products=["product_1", "product_2"]
        )
        
        assert result["success"] == True
        assert result["quote_id"].startswith("quote_")
        assert len(result["next_steps"]) > 0
    
    @pytest.mark.asyncio
    async def test_mcp_create_project_plan(self, product_agent):
        """测试MCP创建项目计划工具"""
        project_scope = {
            "description": "CRM实施项目",
            "customer_id": "customer_123"
        }
        
        result = await product_agent._handle_create_project_plan(project_scope=project_scope)
        
        assert result["success"] == True
        assert result["plan_id"].startswith("plan_")
        assert len(result["next_steps"]) > 0
    
    @pytest.mark.asyncio
    async def test_mcp_access_technical_docs(self, product_agent):
        """测试MCP访问技术文档工具"""
        with patch('src.agents.professional.product_agent.rag_service') as mock_rag_service:
            mock_rag_result = Mock()
            mock_rag_result.answer = "技术文档内容"
            mock_rag_result.confidence = 0.8
            mock_rag_result.sources = ["技术文档库"]
            mock_rag_service.query = AsyncMock(return_value=mock_rag_result)
            
            result = await product_agent._handle_access_technical_docs(query="API文档")
            
            assert result["success"] == True
            assert result["query"] == "API文档"
            assert "技术文档内容" in result["documents"]
    
    @pytest.mark.asyncio
    async def test_process_message_integration(self, product_agent, sample_message):
        """测试消息处理集成"""
        with patch.object(product_agent, 'analyze_task') as mock_analyze:
            mock_analyze.return_value = {
                "task_type": "solution_matching",
                "needs_collaboration": False,
                "context": {"customer_id": "customer_123"}
            }
            
            with patch.object(product_agent, 'execute_task') as mock_execute:
                mock_execute.return_value = {
                    "success": True,
                    "response_type": "solution_match",
                    "data": Mock(spec=SolutionMatch)
                }
                
                with patch.object(product_agent, 'generate_response') as mock_generate:
                    mock_response = AgentResponse(
                        content="测试响应",
                        confidence=0.8,
                        suggestions=["建议1", "建议2"]
                    )
                    mock_generate.return_value = mock_response
                    
                    # 模拟工作流执行
                    with patch.object(product_agent, 'workflow') as mock_workflow:
                        mock_workflow.ainvoke = AsyncMock(return_value={"response": mock_response})
                        
                        response = await product_agent.process_message(sample_message)
                        
                        assert isinstance(response, AgentResponse)
                        assert response.content == "测试响应"
                        assert response.confidence == 0.8
                        assert len(response.suggestions) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
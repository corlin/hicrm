"""
CRM专家Agent测试

测试CRM专家Agent的各项功能，包括流程指导、知识整合、质量控制等
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

from src.agents.professional.crm_expert_agent import (
    CRMExpertAgent,
    ProcessType,
    KnowledgeCategory,
    QualityMetric,
    ProcessGuidance,
    KnowledgeIntegration,
    QualityAssessment,
    SystemIntegration
)
from src.agents.base import AgentMessage, MessageType, AgentResponse


class TestCRMExpertAgent:
    """CRM专家Agent测试类"""
    
    @pytest.fixture
    def agent(self):
        """创建CRM专家Agent实例"""
        return CRMExpertAgent()
    
    @pytest.fixture
    def sample_message(self):
        """创建示例消息"""
        return AgentMessage(
            type=MessageType.TASK,
            sender_id="user_123",
            content="请提供销售流程的最佳实践指导"
        )
    
    def test_agent_initialization(self, agent):
        """测试Agent初始化"""
        assert agent.id == "crm_expert_agent"
        assert agent.name == "CRM专家"
        assert agent.specialty == "CRM专业指导和优化"
        assert len(agent.capabilities) == 5
        
        # 检查能力列表
        capability_names = [cap.name for cap in agent.capabilities]
        expected_capabilities = [
            "process_guidance",
            "knowledge_integration", 
            "quality_control",
            "system_integration",
            "compliance_check"
        ]
        for expected in expected_capabilities:
            assert expected in capability_names
    
    @pytest.mark.asyncio
    async def test_analyze_task_process_guidance(self, agent):
        """测试流程指导任务分析"""
        message = AgentMessage(
            type=MessageType.TASK,
            sender_id="user_123",
            content="请帮我设计一个标准的销售流程"
        )
        
        analysis = await agent.analyze_task(message)
        
        assert analysis["task_type"] == "process_guidance"
        assert analysis["needs_collaboration"] == False
        assert "context" in analysis
    
    @pytest.mark.asyncio
    async def test_analyze_task_knowledge_integration(self, agent):
        """测试知识整合任务分析"""
        message = AgentMessage(
            type=MessageType.TASK,
            sender_id="user_123",
            content="请整合关于客户关系管理的最佳实践知识"
        )
        
        analysis = await agent.analyze_task(message)
        
        assert analysis["task_type"] == "knowledge_integration"
        assert analysis["needs_collaboration"] == False
    
    @pytest.mark.asyncio
    async def test_analyze_task_quality_control(self, agent):
        """测试质量控制任务分析"""
        message = AgentMessage(
            type=MessageType.TASK,
            sender_id="user_123",
            content="请评估我们CRM系统的数据质量"
        )
        
        analysis = await agent.analyze_task(message)
        
        assert analysis["task_type"] == "quality_control"
        assert analysis["needs_collaboration"] == False
    
    @pytest.mark.asyncio
    async def test_analyze_task_with_collaboration(self, agent):
        """测试需要协作的任务分析"""
        message = AgentMessage(
            type=MessageType.TASK,
            sender_id="user_123",
            content="请帮我优化销售流程，需要考虑客户成功管理"
        )
        
        analysis = await agent.analyze_task(message)
        
        assert analysis["task_type"] == "process_guidance"
        assert analysis["needs_collaboration"] == True
        assert "customer_success_agent" in analysis["required_agents"]
    
    @pytest.mark.asyncio
    @patch('src.services.rag_service.rag_service.query')
    @patch('src.services.llm_service.llm_service.chat_completion')
    async def test_provide_process_guidance(self, mock_llm, mock_rag, agent):
        """测试提供流程指导"""
        # Mock RAG服务响应
        mock_rag.return_value = Mock(
            answer="销售流程最佳实践包括客户发现、需求分析、方案提议等步骤",
            confidence=0.85
        )
        
        # Mock LLM服务响应
        mock_llm.return_value = {
            "content": """
            ## 销售流程指导
            
            ### 流程概述
            标准销售流程包括客户发现、需求分析、方案提议、商务谈判、成交关单等关键步骤。
            
            ### 执行步骤
            1. **客户发现**
               识别潜在客户和商机
            
            2. **需求分析**
               深入了解客户需求和痛点
            
            ### 最佳实践
            - 建立标准化的销售流程
            - 定期培训销售团队
            
            ### 常见问题
            - 流程执行不一致
            - 缺乏有效的跟进机制
            
            ### 成功指标
            - 转化率提升
            - 销售周期缩短
            """
        }
        
        guidance = await agent.provide_process_guidance(
            ProcessType.SALES_PROCESS.value,
            "制造业",
            "medium"
        )
        
        assert isinstance(guidance, ProcessGuidance)
        assert guidance.process_type == ProcessType.SALES_PROCESS
        assert guidance.process_name == "销售流程指导"
        assert len(guidance.steps) >= 2
        assert len(guidance.best_practices) >= 1
        assert len(guidance.common_pitfalls) >= 1
        
        # 验证调用
        mock_rag.assert_called_once()
        mock_llm.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('src.services.rag_service.rag_service.query')
    @patch('src.services.llm_service.llm_service.chat_completion')
    async def test_integrate_knowledge(self, mock_llm, mock_rag, agent):
        """测试知识整合"""
        # Mock多个RAG服务调用
        mock_rag.return_value = Mock(
            answer="CRM最佳实践包括客户细分、个性化服务、数据驱动决策等",
            confidence=0.8
        )
        
        # Mock LLM服务响应
        mock_llm.return_value = {
            "content": """
            ## CRM最佳实践知识整合
            
            基于多个知识源的整合分析，CRM最佳实践包括以下几个核心方面：
            
            1. 客户细分和画像
            2. 个性化服务策略
            3. 数据驱动的决策支持
            
            ### 建议
            - 建立完善的客户数据管理体系
            - 实施个性化营销策略
            
            ### 相关主题
            - 客户生命周期管理
            - 数据分析和洞察
            """
        }
        
        integration = await agent.integrate_knowledge(
            "CRM最佳实践",
            KnowledgeCategory.BEST_PRACTICES,
            "comprehensive"
        )
        
        assert isinstance(integration, KnowledgeIntegration)
        assert integration.topic == "CRM最佳实践"
        assert integration.category == KnowledgeCategory.BEST_PRACTICES
        assert integration.confidence_score > 0
        assert len(integration.sources) > 0
        assert len(integration.recommendations) >= 1
        
        # 验证多次RAG调用
        assert mock_rag.call_count >= 1
        mock_llm.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('src.services.rag_service.rag_service.query')
    @patch('src.services.llm_service.llm_service.chat_completion')
    async def test_assess_quality(self, mock_llm, mock_rag, agent):
        """测试质量评估"""
        # Mock RAG服务响应
        mock_rag.return_value = Mock(
            answer="CRM系统质量评估应包括数据完整性、流程合规性等维度",
            confidence=0.9
        )
        
        # Mock LLM服务响应
        mock_llm.return_value = {
            "content": """
            ## CRM系统质量评估
            
            ### 总体质量评分：82.5/100
            
            ### 各维度评分
            - **数据完整性**: 85.0/100
            - **流程合规性**: 78.0/100
            - **用户采用率**: 72.0/100
            - **系统利用率**: 88.0/100
            
            ### 主要优势
            - 数据质量较高
            - 系统稳定性好
            
            ### 存在问题
            - 用户培训不足
            - 流程标准化程度低
            
            ### 改进建议
            - 加强用户培训
            - 完善流程标准化
            
            ### 优先行动
            - 制定培训计划
            - 建立质量监控机制
            
            ### 合规状态：基本合规
            """
        }
        
        assessment = await agent.assess_quality(
            "system_quality",
            ["data_completeness", "process_compliance"],
            "last_quarter"
        )
        
        assert isinstance(assessment, QualityAssessment)
        assert assessment.assessment_type == "system_quality"
        assert assessment.overall_score == 82.5
        assert len(assessment.metric_scores) >= 4
        assert len(assessment.strengths) >= 1
        assert len(assessment.weaknesses) >= 1
        assert len(assessment.improvement_recommendations) >= 1
        assert assessment.compliance_status == "基本合规"
        
        # 验证调用
        mock_rag.assert_called_once()
        mock_llm.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('src.services.rag_service.rag_service.query')
    @patch('src.services.llm_service.llm_service.chat_completion')
    async def test_configure_system_integration(self, mock_llm, mock_rag, agent):
        """测试系统集成配置"""
        # Mock RAG服务响应
        mock_rag.return_value = Mock(
            answer="Salesforce到HiCRM的集成需要配置API认证、数据映射等",
            confidence=0.85
        )
        
        # Mock LLM服务响应
        mock_llm.return_value = {
            "content": """
            ## 系统集成配置方案
            
            ### 数据映射关系
            - customer_id → 客户ID
            - customer_name → 客户名称
            - contact_email → 联系邮箱
            
            ### 同步频率设置
            建议设置为每天同步一次
            
            ### 验证规则
            - 必填字段检查
            - 数据格式验证
            
            ### 错误处理
            建立完善的错误日志和重试机制
            
            ### 监控和告警设置
            - 健康检查间隔：5分钟
            - 错误阈值：5%
            """
        }
        
        integration_config = await agent.configure_system_integration(
            "data_sync",
            "Salesforce",
            "HiCRM"
        )
        
        assert isinstance(integration_config, SystemIntegration)
        assert integration_config.integration_type == "data_sync"
        assert integration_config.source_system == "Salesforce"
        assert integration_config.target_system == "HiCRM"
        assert len(integration_config.data_mapping) >= 3
        assert integration_config.sync_frequency == "每天"
        assert len(integration_config.validation_rules) >= 1
        
        # 验证调用
        mock_rag.assert_called_once()
        mock_llm.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('src.services.rag_service.rag_service.query')
    @patch('src.services.llm_service.llm_service.chat_completion')
    async def test_check_compliance(self, mock_llm, mock_rag, agent):
        """测试合规检查"""
        # Mock RAG服务响应
        mock_rag.return_value = Mock(
            answer="GDPR合规要求包括数据保护、用户同意、数据删除权等",
            confidence=0.9
        )
        
        # Mock LLM服务响应
        mock_llm.return_value = {
            "content": """
            ## GDPR合规性检查结果
            
            ### 合规性评估结果：基本合规
            
            ### 合规项目
            - 数据加密存储
            - 用户同意机制
            
            ### 不合规项目
            - 缺少数据删除功能
            - 隐私政策不完整
            
            ### 风险等级：中风险
            
            ### 整改建议
            - 实施数据删除功能
            - 完善隐私政策
            
            ### 实施计划
            制定分阶段整改计划，优先处理高风险项目
            """
        }
        
        compliance_result = await agent.check_compliance("GDPR", "all")
        
        assert compliance_result["compliance_standard"] == "GDPR"
        assert compliance_result["scope"] == "all"
        assert compliance_result["overall_status"] == "基本合规"
        assert len(compliance_result["compliant_items"]) >= 1
        assert len(compliance_result["non_compliant_items"]) >= 1
        assert compliance_result["risk_level"] == "中风险"
        assert len(compliance_result["recommendations"]) >= 1
        
        # 验证调用
        mock_rag.assert_called_once()
        mock_llm.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('src.agents.professional.crm_expert_agent.CRMExpertAgent.provide_process_guidance')
    async def test_execute_process_guidance_task(self, mock_guidance, agent):
        """测试执行流程指导任务"""
        # Mock流程指导结果
        mock_guidance.return_value = ProcessGuidance(
            process_type=ProcessType.SALES_PROCESS,
            process_name="销售流程",
            description="标准销售流程",
            steps=[{"step": 1, "name": "客户发现", "description": "识别潜在客户"}],
            best_practices=["建立标准流程"],
            common_pitfalls=["流程不一致"],
            success_metrics=["转化率提升"],
            templates=["销售流程模板"],
            related_processes=["客户管理流程"],
            compliance_requirements=["数据保护要求"]
        )
        
        message = AgentMessage(
            type=MessageType.TASK,
            sender_id="user_123",
            content="请提供销售流程指导"
        )
        
        analysis = {"task_type": "process_guidance", "context": {}}
        result = await agent._execute_process_guidance(message, analysis["context"])
        
        assert result["success"] == True
        assert result["analysis_type"] == "process_guidance"
        assert result["response_type"] == "process_guidance"
        assert "data" in result
        
        mock_guidance.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_response_success(self, agent):
        """测试成功响应生成"""
        task_result = {
            "success": True,
            "response_type": "process_guidance",
            "data": ProcessGuidance(
                process_type=ProcessType.SALES_PROCESS,
                process_name="销售流程",
                description="标准销售流程",
                steps=[{"step": 1, "name": "客户发现", "description": "识别潜在客户"}],
                best_practices=["建立标准流程"],
                common_pitfalls=["流程不一致"],
                success_metrics=["转化率提升"],
                templates=["销售流程模板"],
                related_processes=["客户管理流程"],
                compliance_requirements=["数据保护要求"]
            )
        }
        
        response = await agent.generate_response(task_result)
        
        assert isinstance(response, AgentResponse)
        assert response.confidence > 0.5
        assert "销售流程指导" in response.content
        assert len(response.suggestions) > 0
        assert len(response.next_actions) > 0
    
    @pytest.mark.asyncio
    async def test_generate_response_error(self, agent):
        """测试错误响应生成"""
        task_result = {
            "success": False,
            "error": "测试错误",
            "fallback_response": "处理请求时出现错误"
        }
        
        response = await agent.generate_response(task_result)
        
        assert isinstance(response, AgentResponse)
        assert response.confidence <= 0.1
        assert "处理请求时出现错误" in response.content
        assert "测试错误" in response.metadata["error"]
    
    @pytest.mark.asyncio
    async def test_mcp_tool_get_process_template(self, agent):
        """测试MCP工具：获取流程模板"""
        result = await agent._handle_get_process_template("sales_process")
        
        assert result["success"] == True
        assert "template" in result
        assert result["template"]["process_type"] == "sales_process"
        assert len(result["template"]["steps"]) == 4
    
    @pytest.mark.asyncio
    async def test_mcp_tool_validate_data_quality(self, agent):
        """测试MCP工具：数据质量验证"""
        result = await agent._handle_validate_data_quality("customer_data")
        
        assert result["success"] == True
        assert "validation_result" in result
        assert result["validation_result"]["scope"] == "customer_data"
        assert "overall_score" in result["validation_result"]
    
    @pytest.mark.asyncio
    async def test_mcp_tool_check_compliance(self, agent):
        """测试MCP工具：合规检查"""
        with patch.object(agent, 'check_compliance') as mock_check:
            mock_check.return_value = {
                "compliance_standard": "GDPR",
                "overall_status": "compliant",
                "compliant_items": ["数据加密"],
                "non_compliant_items": [],
                "risk_level": "低风险",
                "recommendations": [],
                "check_date": datetime.now()
            }
            
            result = await agent._handle_check_compliance("GDPR", "data")
            
            assert result["success"] == True
            assert "compliance_result" in result
            mock_check.assert_called_once_with("GDPR", "data")
    
    def test_determine_process_type(self, agent):
        """测试流程类型确定"""
        test_cases = [
            ("销售流程优化", ProcessType.SALES_PROCESS.value),
            ("线索管理流程", ProcessType.LEAD_MANAGEMENT.value),
            ("客户入职流程", ProcessType.CUSTOMER_ONBOARDING.value),
            ("机会管理流程", ProcessType.OPPORTUNITY_MANAGEMENT.value),
            ("数据质量管理", ProcessType.DATA_QUALITY.value)
        ]
        
        for content, expected in test_cases:
            result = agent._determine_process_type(content)
            assert result == expected
    
    def test_determine_knowledge_category(self, agent):
        """测试知识分类确定"""
        test_cases = [
            ("最佳实践指导", KnowledgeCategory.BEST_PRACTICES),
            ("行业标准规范", KnowledgeCategory.INDUSTRY_STANDARDS),
            ("方法论研究", KnowledgeCategory.METHODOLOGIES),
            ("成功案例分析", KnowledgeCategory.CASE_STUDIES),
            ("模板下载", KnowledgeCategory.TEMPLATES),
            ("检查清单", KnowledgeCategory.CHECKLISTS)
        ]
        
        for content, expected in test_cases:
            result = agent._determine_knowledge_category(content)
            assert result == expected
    
    def test_extract_topic_from_message(self, agent):
        """测试主题提取"""
        test_cases = [
            ("关于客户管理的最佳实践", "客户管理"),
            ("有关销售流程的知识", "销售流程"),
            ("CRM系统知识整合", "CRM系统"),
            ("数据质量最佳实践", "数据质量")
        ]
        
        for content, expected in test_cases:
            result = agent._extract_topic_from_message(content)
            assert expected in result
    
    def test_extract_compliance_standard(self, agent):
        """测试合规标准提取"""
        test_cases = [
            ("GDPR合规检查", "GDPR"),
            ("ISO27001认证", "ISO27001"),
            ("SOX法案合规", "SOX"),
            ("PCI-DSS标准", "PCI-DSS"),
            ("一般合规要求", "general_compliance")
        ]
        
        for content, expected in test_cases:
            result = agent._extract_compliance_standard(content)
            assert result == expected
    
    @pytest.mark.asyncio
    async def test_full_workflow_process_guidance(self, agent, sample_message):
        """测试完整的流程指导工作流"""
        with patch('src.services.rag_service.rag_service.query') as mock_rag, \
             patch('src.services.llm_service.llm_service.chat_completion') as mock_llm:
            
            # Mock服务响应
            mock_rag.return_value = Mock(answer="流程指导内容", confidence=0.8)
            mock_llm.return_value = {"content": "详细的流程指导内容"}
            
            # 执行完整工作流
            analysis = await agent.analyze_task(sample_message)
            task_result = await agent.execute_task(sample_message, analysis)
            response = await agent.generate_response(task_result)
            
            # 验证结果
            assert analysis["task_type"] == "process_guidance"
            assert task_result["success"] == True
            assert isinstance(response, AgentResponse)
            assert response.confidence > 0.5
    
    def test_error_handling(self, agent):
        """测试错误处理"""
        # 测试无效的流程类型
        result = agent._determine_process_type("无效的流程类型")
        assert result == ProcessType.SALES_PROCESS.value  # 默认值
        
        # 测试无效的知识分类
        result = agent._determine_knowledge_category("无效的分类")
        assert result == KnowledgeCategory.BEST_PRACTICES  # 默认值
        
        # 测试空内容的主题提取
        result = agent._extract_topic_from_message("")
        assert len(result) > 0  # 应该返回默认值
"""
系统管理Agent测试

测试系统管理Agent的各项功能，包括系统监控、安全管理、集成管理等
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

from src.agents.professional.system_management_agent import (
    SystemManagementAgent,
    SystemStatus,
    SecurityLevel,
    IntegrationStatus,
    MonitoringType,
    SystemHealthReport,
    SecurityAssessment,
    IntegrationConfig,
    PerformanceMetrics
)
from src.agents.base import AgentMessage, MessageType, AgentResponse


class TestSystemManagementAgent:
    """系统管理Agent测试类"""
    
    @pytest.fixture
    def agent(self):
        """创建系统管理Agent实例"""
        return SystemManagementAgent()
    
    @pytest.fixture
    def sample_message(self):
        """创建示例消息"""
        return AgentMessage(
            type=MessageType.TASK,
            sender_id="user_123",
            content="请检查系统健康状态"
        )
    
    def test_agent_initialization(self, agent):
        """测试Agent初始化"""
        assert agent.id == "system_management_agent"
        assert agent.name == "系统管理专家"
        assert agent.specialty == "系统运维管理"
        assert len(agent.capabilities) == 5
        
        # 检查能力列表
        capability_names = [cap.name for cap in agent.capabilities]
        expected_capabilities = [
            "system_monitoring",
            "security_management",
            "integration_management",
            "performance_optimization",
            "infrastructure_management"
        ]
        for expected in expected_capabilities:
            assert expected in capability_names
    
    @pytest.mark.asyncio
    async def test_analyze_task_system_monitoring(self, agent):
        """测试系统监控任务分析"""
        message = AgentMessage(
            type=MessageType.TASK,
            sender_id="user_123",
            content="请监控系统性能状态"
        )
        
        analysis = await agent.analyze_task(message)
        
        assert analysis["task_type"] == "system_monitoring"
        assert analysis["needs_collaboration"] == False
        assert "context" in analysis
    
    @pytest.mark.asyncio
    async def test_analyze_task_security_management(self, agent):
        """测试安全管理任务分析"""
        message = AgentMessage(
            type=MessageType.TASK,
            sender_id="user_123",
            content="请进行系统安全扫描"
        )
        
        analysis = await agent.analyze_task(message)
        
        assert analysis["task_type"] == "security_management"
        assert analysis["needs_collaboration"] == False
    
    @pytest.mark.asyncio
    async def test_analyze_task_integration_management(self, agent):
        """测试集成管理任务分析"""
        message = AgentMessage(
            type=MessageType.TASK,
            sender_id="user_123",
            content="请配置系统集成接口"
        )
        
        analysis = await agent.analyze_task(message)
        
        assert analysis["task_type"] == "integration_management"
        assert analysis["needs_collaboration"] == False
    
    @pytest.mark.asyncio
    async def test_analyze_task_with_collaboration(self, agent):
        """测试需要协作的任务分析"""
        message = AgentMessage(
            type=MessageType.TASK,
            sender_id="user_123",
            content="请优化CRM系统性能，需要考虑业务影响"
        )
        
        analysis = await agent.analyze_task(message)
        
        assert analysis["task_type"] == "performance_optimization"
        assert analysis["needs_collaboration"] == True
        assert "crm_expert_agent" in analysis["required_agents"]
    
    @pytest.mark.asyncio
    @patch('src.services.rag_service.rag_service.query')
    @patch('src.services.llm_service.llm_service.chat_completion')
    async def test_monitor_system_health(self, mock_llm, mock_rag, agent):
        """测试系统健康监控"""
        # Mock RAG服务响应
        mock_rag.return_value = Mock(
            answer="系统性能监控应关注CPU、内存、磁盘、网络等关键指标",
            confidence=0.85
        )
        
        # Mock LLM服务响应
        mock_llm.return_value = {
            "content": """
            ## 系统健康分析
            
            ### 整体系统状态评估
            系统整体运行正常，性能指标在合理范围内。
            
            ### 各组件健康状况
            - Web服务器：健康
            - 数据库：正常
            - 缓存系统：良好
            
            ### 性能指标分析
            CPU使用率65.2%，内存使用率78.5%，均在正常范围。
            
            ### 异常和告警识别
            - CPU使用率较高，需要关注
            
            ### 潜在风险评估
            - 内存使用率持续上升
            
            ### 优化建议
            - 优化数据库查询
            - 增加缓存策略
            """
        }
        
        health_report = await agent.monitor_system_health("performance", "last_24_hours")
        
        assert isinstance(health_report, SystemHealthReport)
        assert health_report.overall_status in [status for status in SystemStatus]
        assert health_report.uptime > 0
        assert len(health_report.performance_metrics) > 0
        assert len(health_report.recommendations) >= 1
        assert health_report.report_time is not None
        
        # 验证调用
        mock_rag.assert_called_once()
        mock_llm.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('src.services.rag_service.rag_service.query')
    @patch('src.services.llm_service.llm_service.chat_completion')
    async def test_assess_security(self, mock_llm, mock_rag, agent):
        """测试安全评估"""
        # Mock RAG服务响应
        mock_rag.return_value = Mock(
            answer="系统漏洞安全评估应包括配置检查、软件更新、访问控制等",
            confidence=0.9
        )
        
        # Mock LLM服务响应
        mock_llm.return_value = {
            "content": """
            ## 系统安全评估
            
            ### 漏洞风险分析
            发现2个中等风险漏洞，1个低风险漏洞。
            
            ### 威胁检测结果
            未发现活跃威胁指标。
            
            ### 合规性检查
            GDPR合规状态良好，ISO27001部分合规。
            
            ### 安全配置评估
            SSL配置需要更新，防火墙规则完善。
            
            ### 访问控制审查
            用户权限管理规范，需要定期审查。
            
            ### 安全改进建议
            - 更新SSL证书
            - 升级依赖包版本
            - 加强访问日志监控
            
            ### 威胁指标
            - 异常登录尝试
            - 可疑网络流量
            """
        }
        
        security_assessment = await agent.assess_security("vulnerability", "system")
        
        assert isinstance(security_assessment, SecurityAssessment)
        assert security_assessment.security_level in [level for level in SecurityLevel]
        assert security_assessment.security_score > 0
        assert len(security_assessment.vulnerabilities) >= 0
        assert len(security_assessment.compliance_status) > 0
        assert len(security_assessment.security_recommendations) >= 1
        assert security_assessment.last_scan is not None
        assert security_assessment.next_scan is not None
        
        # 验证调用
        mock_rag.assert_called_once()
        mock_llm.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('src.services.rag_service.rag_service.query')
    @patch('src.services.llm_service.llm_service.chat_completion')
    async def test_manage_integration(self, mock_llm, mock_rag, agent):
        """测试集成管理"""
        # Mock RAG服务响应
        mock_rag.return_value = Mock(
            answer="系统集成更新操作需要考虑配置变更、测试验证、回滚计划等",
            confidence=0.85
        )
        
        # Mock LLM服务响应
        mock_llm.return_value = {
            "content": """
            ## 集成管理方案
            
            ### 操作执行步骤
            1. 备份当前配置
            2. 应用新配置
            3. 执行测试验证
            4. 监控集成状态
            
            ### 配置变更建议
            - 更新API端点
            - 调整同步频率
            
            ### 风险评估
            - 配置错误可能导致数据同步失败
            - 需要准备回滚方案
            
            ### 测试验证方案
            执行端到端测试，验证数据同步正确性
            
            ### 回滚计划
            如果出现问题，立即恢复备份配置
            
            ### 监控设置
            - 健康检查间隔：5分钟
            - 错误阈值：5%
            """
        }
        
        integration_result = await agent.manage_integration("test_integration", "update")
        
        assert integration_result["integration_id"] == "test_integration"
        assert integration_result["operation"] == "update"
        assert integration_result["status"] in ["completed", "in_progress", "failed"]
        assert len(integration_result["execution_steps"]) >= 1
        assert len(integration_result["risks"]) >= 1
        assert integration_result["operation_time"] is not None
        
        # 验证调用
        mock_rag.assert_called_once()
        mock_llm.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('src.services.rag_service.rag_service.query')
    @patch('src.services.llm_service.llm_service.chat_completion')
    async def test_optimize_performance(self, mock_llm, mock_rag, agent):
        """测试性能优化"""
        # Mock RAG服务响应
        mock_rag.return_value = Mock(
            answer="数据库性能优化包括索引优化、查询优化、连接池调优等",
            confidence=0.8
        )
        
        # Mock LLM服务响应
        mock_llm.return_value = {
            "content": """
            ## 数据库性能优化方案
            
            ### 性能瓶颈分析
            - 慢查询较多
            - 索引使用不充分
            - 连接池配置不当
            
            ### 优化策略建议
            - 优化慢查询SQL
            - 添加必要索引
            - 调整连接池参数
            
            ### 具体实施步骤
            1. 分析慢查询日志
            2. 创建优化索引
            3. 调整数据库配置
            4. 监控性能改进
            
            ### 预期效果评估
            - 查询响应时间减少30%
            - 数据库CPU使用率降低20%
            
            ### 风险控制措施
            - 在测试环境先验证
            - 准备回滚方案
            
            ### 监控验证方案
            持续监控关键性能指标，确保优化效果
            """
        }
        
        optimization_result = await agent.optimize_performance("database", "improve_response_time")
        
        assert optimization_result["component"] == "database"
        assert optimization_result["optimization_goal"] == "improve_response_time"
        assert "current_performance" in optimization_result
        assert len(optimization_result["bottlenecks"]) >= 1
        assert len(optimization_result["optimization_strategies"]) >= 1
        assert len(optimization_result["implementation_steps"]) >= 1
        assert optimization_result["optimization_time"] is not None
        
        # 验证调用
        mock_rag.assert_called_once()
        mock_llm.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('src.services.rag_service.rag_service.query')
    @patch('src.services.llm_service.llm_service.chat_completion')
    async def test_manage_infrastructure(self, mock_llm, mock_rag, agent):
        """测试基础设施管理"""
        # Mock RAG服务响应
        mock_rag.return_value = Mock(
            answer="服务器配置操作需要考虑资源规划、安全配置、监控设置等",
            confidence=0.85
        )
        
        # Mock LLM服务响应
        mock_llm.return_value = {
            "content": """
            ## 服务器配置管理方案
            
            ### 操作前准备工作
            - 评估资源需求
            - 制定配置方案
            - 准备备份策略
            
            ### 具体执行步骤
            1. 创建服务器实例
            2. 安装必要软件
            3. 配置安全设置
            4. 部署应用程序
            
            ### 配置参数建议
            - CPU: 8核心
            - 内存: 32GB
            - 存储: 500GB SSD
            
            ### 安全注意事项
            - 配置防火墙规则
            - 启用SSL加密
            - 设置访问控制
            
            ### 验证测试方案
            执行功能测试和性能测试
            
            ### 应急处理预案
            如果配置失败，立即回滚到之前状态
            """
        }
        
        infrastructure_result = await agent.manage_infrastructure("server", "configure")
        
        assert infrastructure_result["resource_type"] == "server"
        assert infrastructure_result["operation"] == "configure"
        assert infrastructure_result["status"] in ["completed", "in_progress", "failed"]
        assert len(infrastructure_result["preparation_steps"]) >= 1
        assert len(infrastructure_result["execution_steps"]) >= 1
        assert len(infrastructure_result["security_notes"]) >= 1
        assert infrastructure_result["operation_time"] is not None
        
        # 验证调用
        mock_rag.assert_called_once()
        mock_llm.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_response_success(self, agent):
        """测试成功响应生成"""
        task_result = {
            "success": True,
            "response_type": "system_health_report",
            "data": SystemHealthReport(
                overall_status=SystemStatus.HEALTHY,
                components={"web_server": {"status": "healthy"}},
                performance_metrics={"cpu_usage": 65.2, "memory_usage": 78.5},
                alerts=[],
                recommendations=["优化数据库查询"],
                uptime=99.95,
                last_incident=None,
                report_time=datetime.now()
            )
        }
        
        response = await agent.generate_response(task_result)
        
        assert isinstance(response, AgentResponse)
        assert response.confidence > 0.5
        assert "系统健康报告" in response.content
        assert "🟢" in response.content  # 健康状态emoji
        assert len(response.suggestions) > 0
        assert len(response.next_actions) > 0
    
    @pytest.mark.asyncio
    async def test_generate_response_error(self, agent):
        """测试错误响应生成"""
        task_result = {
            "success": False,
            "error": "系统监控失败",
            "fallback_response": "无法获取系统状态"
        }
        
        response = await agent.generate_response(task_result)
        
        assert isinstance(response, AgentResponse)
        assert response.confidence <= 0.1
        assert "无法获取系统状态" in response.content
        assert "系统监控失败" in response.metadata["error"]
    
    @pytest.mark.asyncio
    async def test_mcp_tool_check_system_health(self, agent):
        """测试MCP工具：系统健康检查"""
        with patch.object(agent, 'monitor_system_health') as mock_monitor:
            mock_monitor.return_value = SystemHealthReport(
                overall_status=SystemStatus.HEALTHY,
                components={},
                performance_metrics={},
                alerts=[],
                recommendations=[],
                uptime=99.9,
                last_incident=None,
                report_time=datetime.now()
            )
            
            result = await agent._handle_check_system_health(
                monitoring_type="performance",
                time_range="last_24_hours"
            )
            
            assert result["success"] == True
            assert "health_report" in result
            assert result["health_report"]["overall_status"] == "healthy"
            mock_monitor.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_mcp_tool_get_performance_metrics(self, agent):
        """测试MCP工具：获取性能指标"""
        result = await agent._handle_get_performance_metrics(
            component="database",
            time_range="last_hour"
        )
        
        assert result["success"] == True
        assert "metrics" in result
        assert "timestamp" in result
    
    @pytest.mark.asyncio
    async def test_mcp_tool_manage_security_scan(self, agent):
        """测试MCP工具：安全扫描管理"""
        # 测试启动扫描
        result = await agent._handle_manage_security_scan(
            operation="start",
            scan_type="vulnerability"
        )
        
        assert result["success"] == True
        assert "scan_id" in result
        assert result["status"] == "started"
        
        # 测试查询状态
        result = await agent._handle_manage_security_scan(
            operation="status"
        )
        
        assert result["success"] == True
        assert result["status"] == "completed"
    
    @pytest.mark.asyncio
    async def test_mcp_tool_manage_backup(self, agent):
        """测试MCP工具：备份管理"""
        # 测试启动备份
        result = await agent._handle_manage_backup(
            operation="start",
            backup_type="full"
        )
        
        assert result["success"] == True
        assert "backup_id" in result
        assert result["status"] == "started"
        
        # 测试查询备份状态
        result = await agent._handle_manage_backup(
            operation="status"
        )
        
        assert result["success"] == True
        assert "last_backup" in result
        assert "backup_size" in result
    
    def test_determine_monitoring_type(self, agent):
        """测试监控类型确定"""
        test_cases = [
            ("系统性能监控", MonitoringType.PERFORMANCE.value),
            ("服务可用性检查", MonitoringType.AVAILABILITY.value),
            ("安全状态监控", MonitoringType.SECURITY.value),
            ("集成接口监控", MonitoringType.INTEGRATION.value),
            ("CPU内存资源监控", MonitoringType.RESOURCE.value)
        ]
        
        for content, expected in test_cases:
            result = agent._determine_monitoring_type(content)
            assert result == expected
    
    def test_determine_assessment_type(self, agent):
        """测试评估类型确定"""
        test_cases = [
            ("漏洞扫描评估", "vulnerability"),
            ("合规性检查", "compliance"),
            ("威胁检测分析", "threat"),
            ("一般安全评估", "vulnerability")  # 默认值
        ]
        
        for content, expected in test_cases:
            result = agent._determine_assessment_type(content)
            assert result == expected
    
    def test_determine_security_scope(self, agent):
        """测试安全范围确定"""
        test_cases = [
            ("网络安全检查", "network"),
            ("应用程序安全", "application"),
            ("数据安全评估", "data"),
            ("系统整体安全", "system")  # 默认值
        ]
        
        for content, expected in test_cases:
            result = agent._determine_security_scope(content)
            assert result == expected
    
    def test_determine_component(self, agent):
        """测试组件确定"""
        test_cases = [
            ("数据库性能优化", "database"),
            ("API接口优化", "api"),
            ("前端页面优化", "frontend"),
            ("基础设施优化", "infrastructure"),
            ("系统整体优化", "system")  # 默认值
        ]
        
        for content, expected in test_cases:
            result = agent._determine_component(content)
            assert result == expected
    
    def test_determine_resource_type(self, agent):
        """测试资源类型确定"""
        test_cases = [
            ("服务器配置", "server"),
            ("数据库管理", "database"),
            ("存储扩容", "storage"),
            ("网络配置", "network"),
            ("基础资源", "server")  # 默认值
        ]
        
        for content, expected in test_cases:
            result = agent._determine_resource_type(content)
            assert result == expected
    
    def test_determine_system_status(self, agent):
        """测试系统状态确定"""
        # 测试健康状态
        monitoring_data = {
            "performance_metrics": {
                "cpu_usage": 60.0,
                "memory_usage": 70.0,
                "error_rate": 1.0
            },
            "alerts": []
        }
        analysis_content = "系统运行正常"
        
        status = agent._determine_system_status(monitoring_data, analysis_content)
        assert status == SystemStatus.HEALTHY
        
        # 测试警告状态
        monitoring_data["performance_metrics"]["cpu_usage"] = 85.0
        monitoring_data["alerts"] = [{"level": "warning", "message": "CPU使用率高"}]
        
        status = agent._determine_system_status(monitoring_data, analysis_content)
        assert status == SystemStatus.WARNING
        
        # 测试严重状态
        monitoring_data["performance_metrics"]["cpu_usage"] = 95.0
        monitoring_data["alerts"] = [{"level": "critical", "message": "系统过载"}]
        
        status = agent._determine_system_status(monitoring_data, analysis_content)
        assert status == SystemStatus.CRITICAL
    
    def test_determine_security_level(self, agent):
        """测试安全级别确定"""
        # 测试低风险
        security_data = {
            "vulnerabilities": [{"severity": "low"}],
            "security_score": 90.0
        }
        
        level = agent._determine_security_level(security_data)
        assert level == SecurityLevel.LOW
        
        # 测试高风险
        security_data = {
            "vulnerabilities": [{"severity": "high"}],
            "security_score": 60.0
        }
        
        level = agent._determine_security_level(security_data)
        assert level == SecurityLevel.HIGH
        
        # 测试严重风险
        security_data = {
            "vulnerabilities": [{"severity": "critical"}],
            "security_score": 40.0
        }
        
        level = agent._determine_security_level(security_data)
        assert level == SecurityLevel.CRITICAL
    
    @pytest.mark.asyncio
    async def test_full_workflow_system_monitoring(self, agent, sample_message):
        """测试完整的系统监控工作流"""
        with patch('src.services.rag_service.rag_service.query') as mock_rag, \
             patch('src.services.llm_service.llm_service.chat_completion') as mock_llm:
            
            # Mock服务响应
            mock_rag.return_value = Mock(answer="系统监控指导", confidence=0.8)
            mock_llm.return_value = {"content": "详细的系统健康分析"}
            
            # 执行完整工作流
            analysis = await agent.analyze_task(sample_message)
            task_result = await agent.execute_task(sample_message, analysis)
            response = await agent.generate_response(task_result)
            
            # 验证结果
            assert analysis["task_type"] == "system_monitoring"
            assert task_result["success"] == True
            assert isinstance(response, AgentResponse)
            assert response.confidence > 0.5
    
    def test_error_handling(self, agent):
        """测试错误处理"""
        # 测试无效的监控类型
        result = agent._determine_monitoring_type("无效的监控类型")
        assert result == MonitoringType.PERFORMANCE.value  # 默认值
        
        # 测试无效的评估类型
        result = agent._determine_assessment_type("无效的评估类型")
        assert result == "vulnerability"  # 默认值
        
        # 测试无效的组件类型
        result = agent._determine_component("无效的组件")
        assert result == "system"  # 默认值
    
    @pytest.mark.asyncio
    async def test_get_monitoring_data(self, agent):
        """测试获取监控数据"""
        data = await agent._get_monitoring_data("performance", "last_24_hours")
        
        assert data["monitoring_type"] == "performance"
        assert data["time_range"] == "last_24_hours"
        assert "performance_metrics" in data
        assert "alerts" in data
        assert "uptime" in data
    
    @pytest.mark.asyncio
    async def test_get_security_data(self, agent):
        """测试获取安全数据"""
        data = await agent._get_security_data("vulnerability", "system")
        
        assert data["assessment_type"] == "vulnerability"
        assert data["scope"] == "system"
        assert "security_score" in data
        assert "vulnerabilities" in data
        assert "compliance_status" in data
    
    @pytest.mark.asyncio
    async def test_get_performance_data(self, agent):
        """测试获取性能数据"""
        data = await agent._get_performance_data("database")
        
        assert data["component"] == "database"
        assert "cpu_usage" in data
        assert "memory_usage" in data
        assert "response_times" in data
        assert "throughput" in data
        assert "error_rates" in data
"""
系统管理Agent - 专业化系统运维管理Agent

提供系统监控、安全管理、集成配置等系统管理功能
支持Function Calling和MCP协议集成
"""

import json
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from src.agents.base import BaseAgent, AgentMessage, AgentResponse, AgentCapability
from src.services.llm_service import llm_service
from src.services.rag_service import rag_service, RAGMode
from src.core.database import get_db

logger = logging.getLogger(__name__)


class SystemStatus(str, Enum):
    """系统状态枚举"""
    HEALTHY = "healthy"  # 健康
    WARNING = "warning"  # 警告
    CRITICAL = "critical"  # 严重
    DOWN = "down"  # 宕机


class SecurityLevel(str, Enum):
    """安全级别枚举"""
    LOW = "low"  # 低
    MEDIUM = "medium"  # 中
    HIGH = "high"  # 高
    CRITICAL = "critical"  # 严重


class IntegrationStatus(str, Enum):
    """集成状态枚举"""
    ACTIVE = "active"  # 活跃
    INACTIVE = "inactive"  # 非活跃
    ERROR = "error"  # 错误
    MAINTENANCE = "maintenance"  # 维护中


class MonitoringType(str, Enum):
    """监控类型枚举"""
    PERFORMANCE = "performance"  # 性能监控
    AVAILABILITY = "availability"  # 可用性监控
    SECURITY = "security"  # 安全监控
    INTEGRATION = "integration"  # 集成监控
    RESOURCE = "resource"  # 资源监控


@dataclass
class SystemHealthReport:
    """系统健康报告"""
    overall_status: SystemStatus
    components: Dict[str, Dict[str, Any]]
    performance_metrics: Dict[str, float]
    alerts: List[Dict[str, Any]]
    recommendations: List[str]
    uptime: float
    last_incident: Optional[datetime]
    report_time: datetime


@dataclass
class SecurityAssessment:
    """安全评估结果"""
    security_level: SecurityLevel
    vulnerabilities: List[Dict[str, Any]]
    security_score: float
    compliance_status: Dict[str, str]
    threat_indicators: List[str]
    security_recommendations: List[str]
    last_scan: datetime
    next_scan: datetime


@dataclass
class IntegrationConfig:
    """集成配置"""
    integration_id: str
    name: str
    type: str
    status: IntegrationStatus
    endpoint: str
    authentication: Dict[str, Any]
    data_mapping: Dict[str, str]
    sync_schedule: str
    error_handling: Dict[str, Any]
    monitoring: Dict[str, Any]
    last_sync: Optional[datetime]
    next_sync: Optional[datetime]


@dataclass
class PerformanceMetrics:
    """性能指标"""
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_io: float
    database_performance: Dict[str, float]
    response_times: Dict[str, float]
    throughput: Dict[str, float]
    error_rates: Dict[str, float]
    timestamp: datetime


@dataclass
class BackupStatus:
    """备份状态"""
    backup_type: str
    last_backup: datetime
    backup_size: float
    backup_location: str
    retention_period: str
    verification_status: str
    next_backup: datetime
    recovery_time_objective: str


class SystemManagementAgent(BaseAgent):
    """
    系统管理Agent
    
    专注于系统运维管理的各个环节：
    - 系统健康监控和告警
    - 安全管理和威胁检测
    - 集成配置和管理
    - 性能优化和调优
    - 备份和恢复管理
    - 基础设施管理工具集成
    """
    
    def __init__(
        self,
        agent_id: str = "system_management_agent",
        name: str = "系统管理专家",
        state_manager=None,
        communicator=None
    ):
        # 定义系统管理Agent的专业能力
        capabilities = [
            AgentCapability(
                name="system_monitoring",
                description="监控系统健康状态和性能指标",
                parameters={
                    "monitoring_type": {"type": "string", "enum": list(MonitoringType)},
                    "time_range": {"type": "string", "default": "last_24_hours"},
                    "include_alerts": {"type": "boolean", "default": True}
                }
            ),
            AgentCapability(
                name="security_management",
                description="管理系统安全和威胁检测",
                parameters={
                    "assessment_type": {"type": "string", "enum": ["vulnerability", "compliance", "threat"]},
                    "scope": {"type": "string", "enum": ["system", "network", "application", "data"]},
                    "severity_filter": {"type": "string", "enum": ["all", "high", "critical"]}
                }
            ),
            AgentCapability(
                name="integration_management",
                description="管理系统集成和接口配置",
                parameters={
                    "integration_id": {"type": "string"},
                    "operation": {"type": "string", "enum": ["create", "update", "delete", "status", "sync"]},
                    "config_data": {"type": "object"}
                }
            ),
            AgentCapability(
                name="performance_optimization",
                description="系统性能分析和优化建议",
                parameters={
                    "component": {"type": "string", "enum": ["database", "api", "frontend", "infrastructure"]},
                    "metric_type": {"type": "string", "enum": ["response_time", "throughput", "resource_usage"]},
                    "optimization_goal": {"type": "string"}
                }
            ),
            AgentCapability(
                name="infrastructure_management",
                description="基础设施管理和配置",
                parameters={
                    "resource_type": {"type": "string", "enum": ["server", "database", "storage", "network"]},
                    "operation": {"type": "string", "enum": ["provision", "configure", "scale", "monitor"]},
                    "specifications": {"type": "object"}
                }
            )
        ]
        
        super().__init__(
            agent_id=agent_id,
            name=name,
            specialty="系统运维管理",
            capabilities=capabilities,
            state_manager=state_manager,
            communicator=communicator
        )
        
        # 系统管理知识库集合名称
        self.knowledge_collections = {
            "system_administration": "system_admin_guides",
            "security_practices": "security_best_practices",
            "infrastructure_management": "infrastructure_management",
            "monitoring_guides": "monitoring_and_alerting",
            "troubleshooting": "system_troubleshooting",
            "automation_scripts": "automation_and_scripts"
        }
        
        # MCP工具配置
        self.mcp_tools = {
            "check_system_health": self._handle_check_system_health,
            "get_performance_metrics": self._handle_get_performance_metrics,
            "manage_security_scan": self._handle_manage_security_scan,
            "configure_integration": self._handle_configure_integration,
            "manage_backup": self._handle_manage_backup,
            "execute_maintenance": self._handle_execute_maintenance,
            "infrastructure_provision": self._handle_infrastructure_provision,
            "deploy_configuration": self._handle_deploy_configuration
        }
        
        logger.info(f"系统管理Agent {self.name} 初始化完成")
    
    async def analyze_task(self, message: AgentMessage) -> Dict[str, Any]:
        """
        分析系统管理相关任务
        """
        try:
            content = message.content.lower()
            metadata = message.metadata or {}
            
            # 识别任务类型
            task_type = "general"
            needs_collaboration = False
            required_agents = []
            
            # 系统监控相关
            if any(keyword in content for keyword in ["监控", "健康", "状态", "性能", "告警"]):
                task_type = "system_monitoring"
                
            # 安全管理相关
            elif any(keyword in content for keyword in ["安全", "漏洞", "威胁", "防护", "合规"]):
                task_type = "security_management"
                
            # 集成管理相关
            elif any(keyword in content for keyword in ["集成", "接口", "同步", "连接", "配置"]):
                task_type = "integration_management"
                
            # 性能优化相关
            elif any(keyword in content for keyword in ["优化", "性能", "调优", "响应时间", "吞吐量"]):
                task_type = "performance_optimization"
                
            # 基础设施管理相关
            elif any(keyword in content for keyword in ["基础设施", "服务器", "数据库", "存储", "网络", "部署"]):
                task_type = "infrastructure_management"
            
            # 判断是否需要协作
            if any(keyword in content for keyword in ["crm", "业务", "流程"]):
                needs_collaboration = True
                required_agents.append("crm_expert_agent")
                
            if any(keyword in content for keyword in ["客户", "用户体验"]):
                needs_collaboration = True
                required_agents.append("customer_success_agent")
                
            if any(keyword in content for keyword in ["数据", "分析", "报告"]):
                needs_collaboration = True
                required_agents.append("management_strategy_agent")
            
            return {
                "task_type": task_type,
                "needs_collaboration": needs_collaboration,
                "required_agents": required_agents,
                "collaboration_type": "sequential" if needs_collaboration else None,
                "priority": metadata.get("priority", "medium"),
                "context": {
                    "user_role": metadata.get("user_role", "system_admin"),
                    "system_component": metadata.get("system_component"),
                    "urgency": metadata.get("urgency", "normal"),
                    "environment": metadata.get("environment", "production")
                }
            }
            
        except Exception as e:
            logger.error(f"系统管理任务分析失败: {e}")
            return {
                "task_type": "general",
                "needs_collaboration": False,
                "error": str(e)
            }
    
    async def execute_task(self, message: AgentMessage, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行系统管理任务
        """
        task_type = analysis.get("task_type", "general")
        context = analysis.get("context", {})
        
        try:
            if task_type == "system_monitoring":
                return await self._execute_system_monitoring(message, context)
            elif task_type == "security_management":
                return await self._execute_security_management(message, context)
            elif task_type == "integration_management":
                return await self._execute_integration_management(message, context)
            elif task_type == "performance_optimization":
                return await self._execute_performance_optimization(message, context)
            elif task_type == "infrastructure_management":
                return await self._execute_infrastructure_management(message, context)
            else:
                return await self._execute_general_system_query(message, context)
                
        except Exception as e:
            logger.error(f"系统管理任务执行失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "fallback_response": "抱歉，处理您的系统管理请求时遇到了问题，请稍后重试。"
            }
    
    async def _execute_system_monitoring(self, message: AgentMessage, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行系统监控任务"""
        try:
            monitoring_type = self._determine_monitoring_type(message.content)
            time_range = context.get("time_range", "last_24_hours")
            
            health_report = await self.monitor_system_health(monitoring_type, time_range)
            
            return {
                "success": True,
                "analysis_type": "system_monitoring",
                "data": health_report,
                "response_type": "system_health_report"
            }
                
        except Exception as e:
            logger.error(f"系统监控执行失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _execute_security_management(self, message: AgentMessage, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行安全管理任务"""
        try:
            assessment_type = self._determine_assessment_type(message.content)
            scope = self._determine_security_scope(message.content)
            
            security_assessment = await self.assess_security(assessment_type, scope)
            
            return {
                "success": True,
                "analysis_type": "security_management",
                "data": security_assessment,
                "response_type": "security_assessment"
            }
            
        except Exception as e:
            logger.error(f"安全管理执行失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _execute_integration_management(self, message: AgentMessage, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行集成管理任务"""
        try:
            integration_id = self._extract_integration_id(message.content)
            operation = self._determine_integration_operation(message.content)
            
            integration_result = await self.manage_integration(integration_id, operation)
            
            return {
                "success": True,
                "analysis_type": "integration_management",
                "data": integration_result,
                "response_type": "integration_result"
            }
            
        except Exception as e:
            logger.error(f"集成管理执行失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _execute_performance_optimization(self, message: AgentMessage, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行性能优化任务"""
        try:
            component = self._determine_component(message.content)
            optimization_goal = self._extract_optimization_goal(message.content)
            
            optimization_result = await self.optimize_performance(component, optimization_goal)
            
            return {
                "success": True,
                "analysis_type": "performance_optimization",
                "data": optimization_result,
                "response_type": "optimization_result"
            }
            
        except Exception as e:
            logger.error(f"性能优化执行失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _execute_infrastructure_management(self, message: AgentMessage, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行基础设施管理任务"""
        try:
            resource_type = self._determine_resource_type(message.content)
            operation = self._determine_infrastructure_operation(message.content)
            
            infrastructure_result = await self.manage_infrastructure(resource_type, operation)
            
            return {
                "success": True,
                "analysis_type": "infrastructure_management",
                "data": infrastructure_result,
                "response_type": "infrastructure_result"
            }
            
        except Exception as e:
            logger.error(f"基础设施管理执行失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _execute_general_system_query(self, message: AgentMessage, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行一般系统查询"""
        try:
            # 使用RAG检索相关系统管理知识
            rag_result = await rag_service.query(
                question=message.content,
                mode=RAGMode.HYBRID,
                collection_name=self.knowledge_collections["system_administration"]
            )
            
            return {
                "success": True,
                "analysis_type": "general_query",
                "data": {
                    "answer": rag_result.answer,
                    "sources": rag_result.sources,
                    "confidence": rag_result.confidence
                },
                "response_type": "knowledge_based"
            }
            
        except Exception as e:
            logger.error(f"一般系统查询执行失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def generate_response(
        self, 
        task_result: Optional[Dict[str, Any]] = None,
        collaboration_result: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        """
        生成系统管理Agent响应
        """
        try:
            if not task_result or not task_result.get("success", False):
                error_msg = task_result.get("error", "未知错误") if task_result else "任务执行失败"
                fallback = task_result.get("fallback_response", "抱歉，我无法处理您的系统管理请求。")
                
                return AgentResponse(
                    content=fallback,
                    confidence=0.1,
                    suggestions=["请检查输入信息", "稍后重试", "联系技术支持"],
                    metadata={"error": error_msg}
                )
            
            response_type = task_result.get("response_type", "general")
            data = task_result.get("data", {})
            
            # 根据响应类型生成不同格式的回复
            if response_type == "system_health_report":
                content, suggestions = await self._format_system_health_response(data)
            elif response_type == "security_assessment":
                content, suggestions = await self._format_security_assessment_response(data)
            elif response_type == "integration_result":
                content, suggestions = await self._format_integration_result_response(data)
            elif response_type == "optimization_result":
                content, suggestions = await self._format_optimization_result_response(data)
            elif response_type == "infrastructure_result":
                content, suggestions = await self._format_infrastructure_result_response(data)
            elif response_type == "knowledge_based":
                content, suggestions = await self._format_knowledge_based_response(data)
            else:
                content, suggestions = await self._format_general_response(data)
            
            # 整合协作结果
            if collaboration_result and collaboration_result.get("success"):
                content += "\n\n" + await self._integrate_collaboration_result(collaboration_result)
            
            # 计算置信度
            confidence = self._calculate_response_confidence(task_result, collaboration_result)
            
            return AgentResponse(
                content=content,
                confidence=confidence,
                suggestions=suggestions,
                next_actions=self._generate_next_actions(task_result),
                metadata={
                    "response_type": response_type,
                    "agent_specialty": self.specialty,
                    "timestamp": datetime.now().isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"生成系统管理Agent响应失败: {e}")
            return AgentResponse(
                content="抱歉，生成响应时遇到了问题。",
                confidence=0.0,
                suggestions=["请重新提问", "检查网络连接"],
                metadata={"error": str(e)}
            )
    
    # 核心业务方法实现
    
    async def monitor_system_health(
        self, 
        monitoring_type: str = "performance", 
        time_range: str = "last_24_hours"
    ) -> SystemHealthReport:
        """
        监控系统健康状态
        """
        try:
            # 获取系统监控数据
            monitoring_data = await self._get_monitoring_data(monitoring_type, time_range)
            
            # 构建系统健康分析提示
            health_prompt = f"""
            作为系统管理专家，请分析以下系统监控数据：
            
            监控类型：{monitoring_type}
            时间范围：{time_range}
            监控数据：{json.dumps(monitoring_data, ensure_ascii=False, indent=2)}
            
            请从以下维度分析系统健康状态：
            1. 整体系统状态评估
            2. 各组件健康状况
            3. 性能指标分析
            4. 异常和告警识别
            5. 潜在风险评估
            6. 优化建议
            
            请提供详细的健康报告和改进建议。
            """
            
            # 检索监控最佳实践
            rag_result = await rag_service.query(
                question=f"系统{monitoring_type}监控分析和健康评估方法",
                collection_name=self.knowledge_collections["monitoring_guides"]
            )
            
            enhanced_prompt = f"{health_prompt}\n\n监控指南：\n{rag_result.answer}"
            
            # 使用LLM生成健康分析
            llm_response = await llm_service.chat_completion(
                messages=[{"role": "user", "content": enhanced_prompt}],
                temperature=0.2,
                max_tokens=2000
            )
            
            content = llm_response.get("content", "")
            
            # 确定整体状态
            overall_status = self._determine_system_status(monitoring_data, content)
            
            return SystemHealthReport(
                overall_status=overall_status,
                components=self._extract_component_status(monitoring_data),
                performance_metrics=monitoring_data.get("performance_metrics", {}),
                alerts=monitoring_data.get("alerts", []),
                recommendations=self._extract_list_items(content, "建议"),
                uptime=monitoring_data.get("uptime", 99.9),
                last_incident=self._get_last_incident_time(),
                report_time=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"系统健康监控失败: {e}")
            raise
    
    async def assess_security(self, assessment_type: str = "vulnerability", scope: str = "system") -> SecurityAssessment:
        """
        评估系统安全
        """
        try:
            # 获取安全数据
            security_data = await self._get_security_data(assessment_type, scope)
            
            # 构建安全评估提示
            security_prompt = f"""
            作为系统安全专家，请评估以下系统安全状况：
            
            评估类型：{assessment_type}
            评估范围：{scope}
            安全数据：{json.dumps(security_data, ensure_ascii=False, indent=2)}
            
            请从以下维度进行安全评估：
            1. 漏洞风险分析
            2. 威胁检测结果
            3. 合规性检查
            4. 安全配置评估
            5. 访问控制审查
            6. 安全改进建议
            
            请提供详细的安全评估报告。
            """
            
            # 检索安全最佳实践
            rag_result = await rag_service.query(
                question=f"系统{assessment_type}安全评估和防护措施",
                collection_name=self.knowledge_collections["security_practices"]
            )
            
            enhanced_prompt = f"{security_prompt}\n\n安全指南：\n{rag_result.answer}"
            
            # 使用LLM生成安全评估
            llm_response = await llm_service.chat_completion(
                messages=[{"role": "user", "content": enhanced_prompt}],
                temperature=0.1,
                max_tokens=2000
            )
            
            content = llm_response.get("content", "")
            
            return SecurityAssessment(
                security_level=self._determine_security_level(security_data),
                vulnerabilities=security_data.get("vulnerabilities", []),
                security_score=security_data.get("security_score", 75.0),
                compliance_status=security_data.get("compliance_status", {}),
                threat_indicators=self._extract_list_items(content, "威胁指标"),
                security_recommendations=self._extract_list_items(content, "安全建议"),
                last_scan=datetime.now() - timedelta(days=1),
                next_scan=datetime.now() + timedelta(days=7)
            )
            
        except Exception as e:
            logger.error(f"安全评估失败: {e}")
            raise
    
    async def manage_integration(self, integration_id: str, operation: str) -> Dict[str, Any]:
        """
        管理系统集成
        """
        try:
            # 获取集成配置
            integration_config = await self._get_integration_config(integration_id)
            
            # 构建集成管理提示
            management_prompt = f"""
            作为系统集成专家，请处理以下集成管理请求：
            
            集成ID：{integration_id}
            操作类型：{operation}
            当前配置：{json.dumps(integration_config, ensure_ascii=False, indent=2)}
            
            请根据操作类型提供相应的处理方案：
            1. 操作执行步骤
            2. 配置变更建议
            3. 风险评估
            4. 测试验证方案
            5. 回滚计划
            6. 监控设置
            
            请确保操作安全可靠。
            """
            
            # 检索集成管理指南
            rag_result = await rag_service.query(
                question=f"系统集成{operation}操作最佳实践",
                collection_name=self.knowledge_collections["infrastructure_management"]
            )
            
            enhanced_prompt = f"{management_prompt}\n\n集成指南：\n{rag_result.answer}"
            
            # 使用LLM生成管理方案
            llm_response = await llm_service.chat_completion(
                messages=[{"role": "user", "content": enhanced_prompt}],
                temperature=0.2,
                max_tokens=1500
            )
            
            content = llm_response.get("content", "")
            
            # 执行实际操作（这里简化处理）
            operation_result = await self._execute_integration_operation(integration_id, operation)
            
            return {
                "integration_id": integration_id,
                "operation": operation,
                "status": operation_result.get("status", "completed"),
                "execution_steps": self._extract_list_items(content, "执行步骤"),
                "configuration_changes": self._extract_configuration_changes(content),
                "risks": self._extract_list_items(content, "风险"),
                "testing_plan": self._extract_section(content, "测试验证"),
                "rollback_plan": self._extract_section(content, "回滚计划"),
                "monitoring_setup": self._extract_monitoring_config(content),
                "operation_time": datetime.now()
            }
            
        except Exception as e:
            logger.error(f"集成管理失败: {e}")
            raise
    
    async def optimize_performance(self, component: str, optimization_goal: str) -> Dict[str, Any]:
        """
        优化系统性能
        """
        try:
            # 获取性能数据
            performance_data = await self._get_performance_data(component)
            
            # 构建性能优化提示
            optimization_prompt = f"""
            作为系统性能专家，请为以下组件制定性能优化方案：
            
            组件：{component}
            优化目标：{optimization_goal}
            当前性能：{json.dumps(performance_data, ensure_ascii=False, indent=2)}
            
            请提供详细的优化方案：
            1. 性能瓶颈分析
            2. 优化策略建议
            3. 具体实施步骤
            4. 预期效果评估
            5. 风险控制措施
            6. 监控验证方案
            
            请确保优化方案可行有效。
            """
            
            # 检索性能优化指南
            rag_result = await rag_service.query(
                question=f"{component}性能优化最佳实践和调优方法",
                collection_name=self.knowledge_collections["system_administration"]
            )
            
            enhanced_prompt = f"{optimization_prompt}\n\n优化指南：\n{rag_result.answer}"
            
            # 使用LLM生成优化方案
            llm_response = await llm_service.chat_completion(
                messages=[{"role": "user", "content": enhanced_prompt}],
                temperature=0.2,
                max_tokens=2000
            )
            
            content = llm_response.get("content", "")
            
            return {
                "component": component,
                "optimization_goal": optimization_goal,
                "current_performance": performance_data,
                "bottlenecks": self._extract_list_items(content, "瓶颈"),
                "optimization_strategies": self._extract_list_items(content, "策略"),
                "implementation_steps": self._extract_list_items(content, "实施步骤"),
                "expected_improvements": self._extract_expected_improvements(content),
                "risks": self._extract_list_items(content, "风险"),
                "monitoring_plan": self._extract_section(content, "监控验证"),
                "optimization_time": datetime.now()
            }
            
        except Exception as e:
            logger.error(f"性能优化失败: {e}")
            raise
    
    async def manage_infrastructure(self, resource_type: str, operation: str) -> Dict[str, Any]:
        """
        管理基础设施
        """
        try:
            # 获取基础设施状态
            infrastructure_data = await self._get_infrastructure_data(resource_type)
            
            # 构建基础设施管理提示
            management_prompt = f"""
            作为基础设施专家，请处理以下基础设施管理请求：
            
            资源类型：{resource_type}
            操作类型：{operation}
            当前状态：{json.dumps(infrastructure_data, ensure_ascii=False, indent=2)}
            
            请提供详细的管理方案：
            1. 操作前准备工作
            2. 具体执行步骤
            3. 配置参数建议
            4. 安全注意事项
            5. 验证测试方案
            6. 应急处理预案
            
            请确保操作规范安全。
            """
            
            # 检索基础设施管理指南
            rag_result = await rag_service.query(
                question=f"{resource_type}基础设施{operation}操作指南",
                collection_name=self.knowledge_collections["infrastructure_management"]
            )
            
            enhanced_prompt = f"{management_prompt}\n\n管理指南：\n{rag_result.answer}"
            
            # 使用LLM生成管理方案
            llm_response = await llm_service.chat_completion(
                messages=[{"role": "user", "content": enhanced_prompt}],
                temperature=0.2,
                max_tokens=1500
            )
            
            content = llm_response.get("content", "")
            
            # 执行实际操作（这里简化处理）
            operation_result = await self._execute_infrastructure_operation(resource_type, operation)
            
            return {
                "resource_type": resource_type,
                "operation": operation,
                "status": operation_result.get("status", "completed"),
                "preparation_steps": self._extract_list_items(content, "准备工作"),
                "execution_steps": self._extract_list_items(content, "执行步骤"),
                "configuration": self._extract_configuration_params(content),
                "security_notes": self._extract_list_items(content, "安全注意"),
                "validation_plan": self._extract_section(content, "验证测试"),
                "emergency_plan": self._extract_section(content, "应急处理"),
                "operation_time": datetime.now()
            }
            
        except Exception as e:
            logger.error(f"基础设施管理失败: {e}")
            raise
    
    # MCP工具处理方法
    
    async def _handle_check_system_health(self, **kwargs) -> Dict[str, Any]:
        """处理系统健康检查的MCP调用"""
        try:
            monitoring_type = kwargs.get("monitoring_type", "performance")
            time_range = kwargs.get("time_range", "last_24_hours")
            
            health_report = await self.monitor_system_health(monitoring_type, time_range)
            
            return {
                "success": True,
                "health_report": {
                    "overall_status": health_report.overall_status.value,
                    "uptime": health_report.uptime,
                    "alerts_count": len(health_report.alerts),
                    "recommendations_count": len(health_report.recommendations)
                }
            }
                    
        except Exception as e:
            logger.error(f"系统健康检查失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _handle_get_performance_metrics(self, **kwargs) -> Dict[str, Any]:
        """处理获取性能指标的MCP调用"""
        try:
            component = kwargs.get("component", "system")
            time_range = kwargs.get("time_range", "last_hour")
            
            metrics = await self._get_performance_data(component)
            
            return {
                "success": True,
                "metrics": metrics,
                "timestamp": datetime.now().isoformat()
            }
                    
        except Exception as e:
            logger.error(f"获取性能指标失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _handle_manage_security_scan(self, **kwargs) -> Dict[str, Any]:
        """处理安全扫描管理的MCP调用"""
        try:
            operation = kwargs.get("operation", "start")
            scan_type = kwargs.get("scan_type", "vulnerability")
            
            if operation == "start":
                scan_id = f"scan_{int(datetime.now().timestamp())}"
                return {
                    "success": True,
                    "scan_id": scan_id,
                    "status": "started",
                    "estimated_duration": "30 minutes"
                }
            elif operation == "status":
                return {
                    "success": True,
                    "status": "completed",
                    "findings": 5,
                    "critical_issues": 1
                }
            else:
                return {
                    "success": False,
                    "error": f"不支持的操作: {operation}"
                }
                    
        except Exception as e:
            logger.error(f"安全扫描管理失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _handle_configure_integration(self, **kwargs) -> Dict[str, Any]:
        """处理配置集成的MCP调用"""
        try:
            integration_id = kwargs.get("integration_id")
            operation = kwargs.get("operation", "update")
            config_data = kwargs.get("config_data", {})
            
            result = await self.manage_integration(integration_id, operation)
            
            return {
                "success": True,
                "integration_id": integration_id,
                "operation": operation,
                "status": result.get("status", "completed"),
                "message": f"集成{operation}操作完成"
            }
                    
        except Exception as e:
            logger.error(f"配置集成失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _handle_manage_backup(self, **kwargs) -> Dict[str, Any]:
        """处理备份管理的MCP调用"""
        try:
            operation = kwargs.get("operation", "status")
            backup_type = kwargs.get("backup_type", "full")
            
            if operation == "start":
                backup_id = f"backup_{int(datetime.now().timestamp())}"
                return {
                    "success": True,
                    "backup_id": backup_id,
                    "status": "started",
                    "estimated_duration": "2 hours"
                }
            elif operation == "status":
                return {
                    "success": True,
                    "last_backup": (datetime.now() - timedelta(days=1)).isoformat(),
                    "backup_size": "15.2 GB",
                    "status": "completed"
                }
            else:
                return {
                    "success": False,
                    "error": f"不支持的备份操作: {operation}"
                }
                    
        except Exception as e:
            logger.error(f"备份管理失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _handle_execute_maintenance(self, **kwargs) -> Dict[str, Any]:
        """处理执行维护的MCP调用"""
        try:
            maintenance_type = kwargs.get("maintenance_type", "routine")
            schedule = kwargs.get("schedule", "immediate")
            
            maintenance_id = f"maint_{int(datetime.now().timestamp())}"
            
            return {
                "success": True,
                "maintenance_id": maintenance_id,
                "type": maintenance_type,
                "schedule": schedule,
                "status": "scheduled",
                "estimated_downtime": "30 minutes"
            }
                    
        except Exception as e:
            logger.error(f"执行维护失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _handle_infrastructure_provision(self, **kwargs) -> Dict[str, Any]:
        """处理基础设施供应的MCP调用"""
        try:
            resource_type = kwargs.get("resource_type", "server")
            specifications = kwargs.get("specifications", {})
            
            result = await self.manage_infrastructure(resource_type, "provision")
            
            return {
                "success": True,
                "resource_type": resource_type,
                "resource_id": f"{resource_type}_{int(datetime.now().timestamp())}",
                "status": result.get("status", "provisioning"),
                "specifications": specifications
            }
                    
        except Exception as e:
            logger.error(f"基础设施供应失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _handle_deploy_configuration(self, **kwargs) -> Dict[str, Any]:
        """处理部署配置的MCP调用"""
        try:
            config_type = kwargs.get("config_type", "application")
            environment = kwargs.get("environment", "production")
            
            deployment_id = f"deploy_{int(datetime.now().timestamp())}"
            
            return {
                "success": True,
                "deployment_id": deployment_id,
                "config_type": config_type,
                "environment": environment,
                "status": "deployed",
                "deployment_time": datetime.now().isoformat()
            }
                    
        except Exception as e:
            logger.error(f"部署配置失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    # 辅助方法
    
    def _determine_monitoring_type(self, content: str) -> str:
        """确定监控类型"""
        content_lower = content.lower()
        
        if any(keyword in content_lower for keyword in ["性能", "performance"]):
            return MonitoringType.PERFORMANCE.value
        elif any(keyword in content_lower for keyword in ["可用性", "availability", "在线"]):
            return MonitoringType.AVAILABILITY.value
        elif any(keyword in content_lower for keyword in ["安全", "security"]):
            return MonitoringType.SECURITY.value
        elif any(keyword in content_lower for keyword in ["集成", "integration"]):
            return MonitoringType.INTEGRATION.value
        elif any(keyword in content_lower for keyword in ["资源", "resource", "cpu", "内存", "磁盘"]):
            return MonitoringType.RESOURCE.value
        else:
            return MonitoringType.PERFORMANCE.value
    
    def _determine_assessment_type(self, content: str) -> str:
        """确定评估类型"""
        content_lower = content.lower()
        
        if any(keyword in content_lower for keyword in ["漏洞", "vulnerability"]):
            return "vulnerability"
        elif any(keyword in content_lower for keyword in ["合规", "compliance"]):
            return "compliance"
        elif any(keyword in content_lower for keyword in ["威胁", "threat"]):
            return "threat"
        else:
            return "vulnerability"
    
    def _determine_security_scope(self, content: str) -> str:
        """确定安全范围"""
        content_lower = content.lower()
        
        if any(keyword in content_lower for keyword in ["网络", "network"]):
            return "network"
        elif any(keyword in content_lower for keyword in ["应用", "application"]):
            return "application"
        elif any(keyword in content_lower for keyword in ["数据", "data"]):
            return "data"
        else:
            return "system"
    
    def _extract_integration_id(self, content: str) -> str:
        """提取集成ID"""
        import re
        
        patterns = [
            r'集成[ID|id][：:](.+?)[\s,，]',
            r'integration[_\s]id[：:](.+?)[\s,，]',
            r'集成(.+?)[\s,，]'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return "default_integration"
    
    def _determine_integration_operation(self, content: str) -> str:
        """确定集成操作"""
        content_lower = content.lower()
        
        if any(keyword in content_lower for keyword in ["创建", "create"]):
            return "create"
        elif any(keyword in content_lower for keyword in ["更新", "update"]):
            return "update"
        elif any(keyword in content_lower for keyword in ["删除", "delete"]):
            return "delete"
        elif any(keyword in content_lower for keyword in ["同步", "sync"]):
            return "sync"
        elif any(keyword in content_lower for keyword in ["状态", "status"]):
            return "status"
        else:
            return "status"
    
    def _determine_component(self, content: str) -> str:
        """确定组件"""
        content_lower = content.lower()
        
        if any(keyword in content_lower for keyword in ["数据库", "database"]):
            return "database"
        elif any(keyword in content_lower for keyword in ["api", "接口"]):
            return "api"
        elif any(keyword in content_lower for keyword in ["前端", "frontend"]):
            return "frontend"
        elif any(keyword in content_lower for keyword in ["基础设施", "infrastructure"]):
            return "infrastructure"
        else:
            return "system"
    
    def _extract_optimization_goal(self, content: str) -> str:
        """提取优化目标"""
        content_lower = content.lower()
        
        if any(keyword in content_lower for keyword in ["响应时间", "response time"]):
            return "improve_response_time"
        elif any(keyword in content_lower for keyword in ["吞吐量", "throughput"]):
            return "increase_throughput"
        elif any(keyword in content_lower for keyword in ["资源利用", "resource utilization"]):
            return "optimize_resource_usage"
        elif any(keyword in content_lower for keyword in ["稳定性", "stability"]):
            return "improve_stability"
        else:
            return "general_optimization"
    
    def _determine_resource_type(self, content: str) -> str:
        """确定资源类型"""
        content_lower = content.lower()
        
        if any(keyword in content_lower for keyword in ["服务器", "server"]):
            return "server"
        elif any(keyword in content_lower for keyword in ["数据库", "database"]):
            return "database"
        elif any(keyword in content_lower for keyword in ["存储", "storage"]):
            return "storage"
        elif any(keyword in content_lower for keyword in ["网络", "network"]):
            return "network"
        else:
            return "server"
    
    def _determine_infrastructure_operation(self, content: str) -> str:
        """确定基础设施操作"""
        content_lower = content.lower()
        
        if any(keyword in content_lower for keyword in ["供应", "provision"]):
            return "provision"
        elif any(keyword in content_lower for keyword in ["配置", "configure"]):
            return "configure"
        elif any(keyword in content_lower for keyword in ["扩展", "scale"]):
            return "scale"
        elif any(keyword in content_lower for keyword in ["监控", "monitor"]):
            return "monitor"
        else:
            return "configure"
    
    async def _get_monitoring_data(self, monitoring_type: str, time_range: str) -> Dict[str, Any]:
        """获取监控数据"""
        # 简化实现，返回模拟数据
        return {
            "monitoring_type": monitoring_type,
            "time_range": time_range,
            "performance_metrics": {
                "cpu_usage": 65.2,
                "memory_usage": 78.5,
                "disk_usage": 45.3,
                "network_io": 23.7,
                "response_time": 150.5,
                "throughput": 1250.0,
                "error_rate": 0.5
            },
            "alerts": [
                {
                    "level": "warning",
                    "message": "CPU使用率较高",
                    "timestamp": datetime.now().isoformat()
                }
            ],
            "uptime": 99.95,
            "last_updated": datetime.now().isoformat()
        }
    
    async def _get_security_data(self, assessment_type: str, scope: str) -> Dict[str, Any]:
        """获取安全数据"""
        # 简化实现，返回模拟数据
        return {
            "assessment_type": assessment_type,
            "scope": scope,
            "security_score": 82.5,
            "vulnerabilities": [
                {
                    "severity": "medium",
                    "type": "configuration",
                    "description": "SSL配置需要更新",
                    "affected_component": "web_server"
                },
                {
                    "severity": "low",
                    "type": "software",
                    "description": "依赖包版本过旧",
                    "affected_component": "application"
                }
            ],
            "compliance_status": {
                "GDPR": "compliant",
                "ISO27001": "partial",
                "SOX": "compliant"
            },
            "threat_indicators": [],
            "last_scan": datetime.now().isoformat()
        }
    
    async def _get_integration_config(self, integration_id: str) -> Dict[str, Any]:
        """获取集成配置"""
        # 简化实现，返回模拟数据
        return {
            "integration_id": integration_id,
            "name": f"Integration {integration_id}",
            "type": "api_integration",
            "status": "active",
            "endpoint": "https://api.example.com/v1",
            "authentication": {
                "type": "oauth2",
                "token_expires": "2024-12-31"
            },
            "sync_schedule": "every_hour",
            "last_sync": datetime.now().isoformat(),
            "error_count": 0
        }
    
    async def _get_performance_data(self, component: str) -> Dict[str, Any]:
        """获取性能数据"""
        # 简化实现，返回模拟数据
        return {
            "component": component,
            "cpu_usage": 68.5,
            "memory_usage": 72.3,
            "disk_io": 45.2,
            "network_io": 28.7,
            "response_times": {
                "avg": 145.5,
                "p95": 280.3,
                "p99": 450.7
            },
            "throughput": {
                "requests_per_second": 1250.0,
                "transactions_per_minute": 75000.0
            },
            "error_rates": {
                "4xx_errors": 2.1,
                "5xx_errors": 0.3
            },
            "timestamp": datetime.now().isoformat()
        }
    
    async def _get_infrastructure_data(self, resource_type: str) -> Dict[str, Any]:
        """获取基础设施数据"""
        # 简化实现，返回模拟数据
        return {
            "resource_type": resource_type,
            "current_capacity": {
                "cpu_cores": 8,
                "memory_gb": 32,
                "storage_gb": 500
            },
            "utilization": {
                "cpu": 65.2,
                "memory": 78.5,
                "storage": 45.3
            },
            "status": "running",
            "health_score": 85.7,
            "last_maintenance": (datetime.now() - timedelta(days=7)).isoformat(),
            "next_maintenance": (datetime.now() + timedelta(days=23)).isoformat()
        }
    
    def _determine_system_status(self, monitoring_data: Dict[str, Any], analysis_content: str) -> SystemStatus:
        """确定系统状态"""
        performance_metrics = monitoring_data.get("performance_metrics", {})
        alerts = monitoring_data.get("alerts", [])
        
        # 检查关键指标
        cpu_usage = performance_metrics.get("cpu_usage", 0)
        memory_usage = performance_metrics.get("memory_usage", 0)
        error_rate = performance_metrics.get("error_rate", 0)
        
        # 检查是否有严重告警
        critical_alerts = [alert for alert in alerts if alert.get("level") == "critical"]
        warning_alerts = [alert for alert in alerts if alert.get("level") == "warning"]
        
        if critical_alerts or cpu_usage > 90 or memory_usage > 95 or error_rate > 5:
            return SystemStatus.CRITICAL
        elif warning_alerts or cpu_usage > 80 or memory_usage > 85 or error_rate > 2:
            return SystemStatus.WARNING
        elif "宕机" in analysis_content or "down" in analysis_content.lower():
            return SystemStatus.DOWN
        else:
            return SystemStatus.HEALTHY
    
    def _determine_security_level(self, security_data: Dict[str, Any]) -> SecurityLevel:
        """确定安全级别"""
        vulnerabilities = security_data.get("vulnerabilities", [])
        security_score = security_data.get("security_score", 75.0)
        
        # 检查严重漏洞
        critical_vulns = [v for v in vulnerabilities if v.get("severity") == "critical"]
        high_vulns = [v for v in vulnerabilities if v.get("severity") == "high"]
        
        if critical_vulns or security_score < 50:
            return SecurityLevel.CRITICAL
        elif high_vulns or security_score < 70:
            return SecurityLevel.HIGH
        elif security_score < 85:
            return SecurityLevel.MEDIUM
        else:
            return SecurityLevel.LOW
    
    def _extract_component_status(self, monitoring_data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """提取组件状态"""
        # 简化实现，基于性能指标生成组件状态
        performance_metrics = monitoring_data.get("performance_metrics", {})
        
        components = {
            "web_server": {
                "status": "healthy" if performance_metrics.get("response_time", 0) < 200 else "warning",
                "metrics": {
                    "response_time": performance_metrics.get("response_time", 0),
                    "throughput": performance_metrics.get("throughput", 0)
                }
            },
            "database": {
                "status": "healthy" if performance_metrics.get("cpu_usage", 0) < 80 else "warning",
                "metrics": {
                    "cpu_usage": performance_metrics.get("cpu_usage", 0),
                    "memory_usage": performance_metrics.get("memory_usage", 0)
                }
            },
            "cache": {
                "status": "healthy",
                "metrics": {
                    "hit_rate": 95.2,
                    "memory_usage": 65.3
                }
            }
        }
        
        return components
    
    def _get_last_incident_time(self) -> Optional[datetime]:
        """获取最后事故时间"""
        # 简化实现，返回模拟时间
        return datetime.now() - timedelta(days=15)
    
    async def _execute_integration_operation(self, integration_id: str, operation: str) -> Dict[str, Any]:
        """执行集成操作"""
        # 简化实现，返回操作结果
        return {
            "status": "completed",
            "operation_id": f"op_{int(datetime.now().timestamp())}",
            "duration": "30 seconds",
            "changes_applied": True
        }
    
    async def _execute_infrastructure_operation(self, resource_type: str, operation: str) -> Dict[str, Any]:
        """执行基础设施操作"""
        # 简化实现，返回操作结果
        return {
            "status": "completed",
            "operation_id": f"infra_op_{int(datetime.now().timestamp())}",
            "resource_id": f"{resource_type}_{int(datetime.now().timestamp())}",
            "duration": "5 minutes"
        }
    
    # 响应格式化方法
    
    async def _format_system_health_response(self, data: SystemHealthReport) -> tuple[str, List[str]]:
        """格式化系统健康响应"""
        status_emoji = {
            SystemStatus.HEALTHY: "🟢",
            SystemStatus.WARNING: "🟡", 
            SystemStatus.CRITICAL: "🔴",
            SystemStatus.DOWN: "⚫"
        }
        
        content = f"""## 系统健康报告

### 总体状态: {status_emoji.get(data.overall_status, '🟡')} {data.overall_status.value.upper()}

### 系统可用性: {data.uptime:.2f}%

### 关键性能指标
"""
        for metric, value in data.performance_metrics.items():
            content += f"• **{metric}**: {value}\n"
        
        if data.alerts:
            content += f"\n### 当前告警 ({len(data.alerts)}个)\n"
            for alert in data.alerts[:5]:  # 只显示前5个告警
                level_emoji = "🔴" if alert.get("level") == "critical" else "🟡"
                content += f"{level_emoji} {alert.get('message', '未知告警')}\n"
        
        content += f"""
### 组件状态
"""
        for component, status in data.components.items():
            status_text = status.get("status", "unknown")
            status_emoji_comp = "🟢" if status_text == "healthy" else "🟡"
            content += f"{status_emoji_comp} **{component}**: {status_text}\n"
        
        if data.recommendations:
            content += f"""
### 改进建议
{chr(10).join(f'• {rec}' for rec in data.recommendations)}
"""
        
        content += f"\n**报告时间**: {data.report_time.strftime('%Y-%m-%d %H:%M:%S')}"
        
        suggestions = [
            "查看详细告警信息",
            "执行性能优化",
            "设置监控阈值",
            "制定应急预案"
        ]
        
        return content, suggestions
    
    async def _format_security_assessment_response(self, data: SecurityAssessment) -> tuple[str, List[str]]:
        """格式化安全评估响应"""
        level_emoji = {
            SecurityLevel.LOW: "🟢",
            SecurityLevel.MEDIUM: "🟡",
            SecurityLevel.HIGH: "🟠",
            SecurityLevel.CRITICAL: "🔴"
        }
        
        content = f"""## 安全评估报告

### 安全等级: {level_emoji.get(data.security_level, '🟡')} {data.security_level.value.upper()}
### 安全评分: {data.security_score:.1f}/100

### 漏洞概览 ({len(data.vulnerabilities)}个)
"""
        
        severity_counts = {}
        for vuln in data.vulnerabilities:
            severity = vuln.get("severity", "unknown")
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        for severity, count in severity_counts.items():
            emoji = "🔴" if severity == "critical" else "🟠" if severity == "high" else "🟡"
            content += f"{emoji} **{severity}**: {count}个\n"
        
        if data.vulnerabilities:
            content += "\n### 主要漏洞\n"
            for vuln in data.vulnerabilities[:3]:  # 只显示前3个漏洞
                severity_emoji = "🔴" if vuln.get("severity") == "critical" else "🟡"
                content += f"{severity_emoji} {vuln.get('description', '未知漏洞')} ({vuln.get('affected_component', '未知组件')})\n"
        
        content += f"""
### 合规状态
"""
        for standard, status in data.compliance_status.items():
            status_emoji = "🟢" if status == "compliant" else "🟡" if status == "partial" else "🔴"
            content += f"{status_emoji} **{standard}**: {status}\n"
        
        if data.security_recommendations:
            content += f"""
### 安全建议
{chr(10).join(f'• {rec}' for rec in data.security_recommendations)}
"""
        
        content += f"""
**上次扫描**: {data.last_scan.strftime('%Y-%m-%d %H:%M')}
**下次扫描**: {data.next_scan.strftime('%Y-%m-%d %H:%M')}
"""
        
        suggestions = [
            "修复高危漏洞",
            "更新安全配置",
            "加强访问控制",
            "制定安全策略"
        ]
        
        return content, suggestions
    
    async def _format_integration_result_response(self, data: Dict[str, Any]) -> tuple[str, List[str]]:
        """格式化集成结果响应"""
        content = f"""## 集成管理结果

### 操作概览
- **集成ID**: {data['integration_id']}
- **操作类型**: {data['operation']}
- **执行状态**: {data['status']}
- **操作时间**: {data['operation_time'].strftime('%Y-%m-%d %H:%M:%S')}

### 执行步骤
{chr(10).join(f'{i+1}. {step}' for i, step in enumerate(data.get('execution_steps', [])))}

### 配置变更
{chr(10).join(f'• {change}' for change in data.get('configuration_changes', []))}

### 风险评估
{chr(10).join(f'• {risk}' for risk in data.get('risks', []))}

### 测试验证方案
{data.get('testing_plan', '待制定测试方案')}

### 回滚计划
{data.get('rollback_plan', '待制定回滚方案')}
"""
        
        suggestions = [
            "执行测试验证",
            "监控集成状态",
            "准备回滚方案",
            "更新文档记录"
        ]
        
        return content, suggestions
    
    async def _format_optimization_result_response(self, data: Dict[str, Any]) -> tuple[str, List[str]]:
        """格式化优化结果响应"""
        content = f"""## 性能优化方案

### 优化目标
- **组件**: {data['component']}
- **目标**: {data['optimization_goal']}
- **优化时间**: {data['optimization_time'].strftime('%Y-%m-%d %H:%M:%S')}

### 当前性能基线
"""
        current_perf = data.get('current_performance', {})
        for metric, value in current_perf.items():
            if isinstance(value, dict):
                content += f"• **{metric}**:\n"
                for sub_metric, sub_value in value.items():
                    content += f"  - {sub_metric}: {sub_value}\n"
            else:
                content += f"• **{metric}**: {value}\n"
        
        content += f"""
### 性能瓶颈
{chr(10).join(f'• {bottleneck}' for bottleneck in data.get('bottlenecks', []))}

### 优化策略
{chr(10).join(f'• {strategy}' for strategy in data.get('optimization_strategies', []))}

### 实施步骤
{chr(10).join(f'{i+1}. {step}' for i, step in enumerate(data.get('implementation_steps', [])))}

### 预期改进
{chr(10).join(f'• {improvement}' for improvement in data.get('expected_improvements', []))}

### 风险控制
{chr(10).join(f'• {risk}' for risk in data.get('risks', []))}

### 监控验证
{data.get('monitoring_plan', '制定监控验证方案')}
"""
        
        suggestions = [
            "开始实施优化",
            "设置性能监控",
            "制定回滚计划",
            "验证优化效果"
        ]
        
        return content, suggestions
    
    async def _format_infrastructure_result_response(self, data: Dict[str, Any]) -> tuple[str, List[str]]:
        """格式化基础设施结果响应"""
        content = f"""## 基础设施管理结果

### 操作概览
- **资源类型**: {data['resource_type']}
- **操作类型**: {data['operation']}
- **执行状态**: {data['status']}
- **操作时间**: {data['operation_time'].strftime('%Y-%m-%d %H:%M:%S')}

### 准备工作
{chr(10).join(f'• {prep}' for prep in data.get('preparation_steps', []))}

### 执行步骤
{chr(10).join(f'{i+1}. {step}' for i, step in enumerate(data.get('execution_steps', [])))}

### 配置参数
{chr(10).join(f'• {param}' for param in data.get('configuration', []))}

### 安全注意事项
{chr(10).join(f'• {note}' for note in data.get('security_notes', []))}

### 验证测试方案
{data.get('validation_plan', '制定验证测试方案')}

### 应急处理预案
{data.get('emergency_plan', '制定应急处理预案')}
"""
        
        suggestions = [
            "执行验证测试",
            "监控资源状态",
            "更新配置文档",
            "培训运维人员"
        ]
        
        return content, suggestions
    
    async def _format_knowledge_based_response(self, data: Dict[str, Any]) -> tuple[str, List[str]]:
        """格式化基于知识的响应"""
        content = f"""## 系统管理建议

{data['answer']}

### 参考来源
{chr(10).join(f'• {source}' for source in data.get('sources', []))}

**置信度**: {data.get('confidence', 0.5):.1%}
"""
        
        suggestions = [
            "获取详细操作指南",
            "查看相关案例",
            "制定实施计划",
            "寻求专业支持"
        ]
        
        return content, suggestions
    
    async def _format_general_response(self, data: Dict[str, Any]) -> tuple[str, List[str]]:
        """格式化一般响应"""
        content = "作为系统管理专家，我已经处理了您的请求。如果您需要更具体的技术指导，请提供更多详细信息。"
        
        suggestions = [
            "明确具体需求",
            "提供系统环境信息",
            "选择具体的管理任务",
            "咨询技术支持"
        ]
        
        return content, suggestions
    
    async def _integrate_collaboration_result(self, collaboration_result: Dict[str, Any]) -> str:
        """整合协作结果"""
        results = collaboration_result.get("collaboration_results", [])
        if not results:
            return ""
        
        content = "### 协作Agent建议\n\n"
        for result in results:
            if "error" not in result:
                agent_id = result.get("agent_id", "未知Agent")
                agent_result = result.get("result", {})
                if isinstance(agent_result, dict) and "content" in agent_result:
                    content += f"**{agent_id}**: {agent_result['content'][:200]}...\n\n"
        
        return content
    
    def _calculate_response_confidence(
        self, 
        task_result: Dict[str, Any], 
        collaboration_result: Optional[Dict[str, Any]] = None
    ) -> float:
        """计算响应置信度"""
        base_confidence = 0.85  # 系统管理通常有较高的确定性
        
        # 根据任务结果调整置信度
        if task_result.get("success"):
            response_type = task_result.get("response_type", "general")
            if response_type in ["system_health_report", "security_assessment"]:
                base_confidence = 0.9  # 监控和评估数据较为准确
            elif response_type in ["integration_result", "infrastructure_result"]:
                base_confidence = 0.8  # 操作结果有一定不确定性
        else:
            base_confidence = 0.3
        
        # 如果有协作结果，略微提升置信度
        if collaboration_result and collaboration_result.get("success"):
            base_confidence = min(base_confidence + 0.05, 1.0)
        
        return base_confidence
    
    def _generate_next_actions(self, task_result: Dict[str, Any]) -> List[str]:
        """生成下一步行动建议"""
        response_type = task_result.get("response_type", "general")
        
        if response_type == "system_health_report":
            return ["处理告警问题", "优化性能瓶颈", "更新监控配置", "制定维护计划"]
        elif response_type == "security_assessment":
            return ["修复安全漏洞", "更新安全策略", "加强访问控制", "安排安全培训"]
        elif response_type == "integration_result":
            return ["验证集成功能", "监控集成状态", "更新集成文档", "培训使用人员"]
        elif response_type == "optimization_result":
            return ["实施优化方案", "监控性能改进", "验证优化效果", "调整优化策略"]
        elif response_type == "infrastructure_result":
            return ["验证基础设施", "更新配置文档", "培训运维团队", "建立监控机制"]
        else:
            return ["明确技术需求", "收集系统信息", "制定实施计划", "寻求技术支持"]
    
    # 内容解析辅助方法
    
    def _extract_section(self, content: str, section_name: str) -> str:
        """提取内容中的特定章节"""
        import re
        
        patterns = [
            rf'{section_name}[：:]\s*(.+?)(?=\n\n|\n[#*]|$)',
            rf'### {section_name}\s*(.+?)(?=\n\n|\n###|$)',
            rf'## {section_name}\s*(.+?)(?=\n\n|\n##|$)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.DOTALL)
            if match:
                return match.group(1).strip()
        
        return f"关于{section_name}的详细信息"
    
    def _extract_list_items(self, content: str, section_name: str) -> List[str]:
        """提取列表项"""
        import re
        
        # 寻找章节后的列表项
        section_pattern = rf'{section_name}[：:]?\s*\n((?:[-•*]\s*.+\n?)+)'
        match = re.search(section_pattern, content, re.MULTILINE)
        
        if match:
            list_content = match.group(1)
            items = re.findall(r'[-•*]\s*(.+)', list_content)
            return [item.strip() for item in items if item.strip()]
        
        # 如果没找到，返回默认项
        return [f"{section_name}相关项目1", f"{section_name}相关项目2"]
    
    def _extract_configuration_changes(self, content: str) -> List[str]:
        """提取配置变更"""
        return self._extract_list_items(content, "配置变更")
    
    def _extract_monitoring_config(self, content: str) -> Dict[str, Any]:
        """提取监控配置"""
        # 简化实现，返回默认监控配置
        return {
            "health_check_interval": "5分钟",
            "alert_threshold": "80%",
            "notification_channels": ["邮件", "短信"],
            "dashboard_enabled": True,
            "log_retention": "30天"
        }
    
    def _extract_expected_improvements(self, content: str) -> List[str]:
        """提取预期改进"""
        return self._extract_list_items(content, "预期改进")
    
    def _extract_configuration_params(self, content: str) -> List[str]:
        """提取配置参数"""
        return self._extract_list_items(content, "配置参数")
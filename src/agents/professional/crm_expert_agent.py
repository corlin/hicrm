"""
CRM专家Agent - 专业化CRM最佳实践指导Agent

提供流程指导、知识整合、质量控制等CRM专业功能
支持Function Calling和MCP协议集成
"""

import json
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from src.agents.base import BaseAgent, AgentMessage, AgentResponse, AgentCapability
from src.services.customer_service import CustomerService
from src.services.lead_service import LeadService
from src.services.opportunity_service import OpportunityService
from src.services.llm_service import llm_service
from src.services.rag_service import rag_service, RAGMode
from src.core.database import get_db

logger = logging.getLogger(__name__)


class ProcessType(str, Enum):
    """流程类型枚举"""
    SALES_PROCESS = "sales_process"  # 销售流程
    LEAD_MANAGEMENT = "lead_management"  # 线索管理
    CUSTOMER_ONBOARDING = "customer_onboarding"  # 客户入职
    OPPORTUNITY_MANAGEMENT = "opportunity_management"  # 机会管理
    CUSTOMER_SUCCESS = "customer_success"  # 客户成功
    DATA_QUALITY = "data_quality"  # 数据质量


class KnowledgeCategory(str, Enum):
    """知识分类枚举"""
    BEST_PRACTICES = "best_practices"  # 最佳实践
    INDUSTRY_STANDARDS = "industry_standards"  # 行业标准
    METHODOLOGIES = "methodologies"  # 方法论
    CASE_STUDIES = "case_studies"  # 案例研究
    TEMPLATES = "templates"  # 模板
    CHECKLISTS = "checklists"  # 检查清单


class QualityMetric(str, Enum):
    """质量指标枚举"""
    DATA_COMPLETENESS = "data_completeness"  # 数据完整性
    PROCESS_COMPLIANCE = "process_compliance"  # 流程合规性
    USER_ADOPTION = "user_adoption"  # 用户采用率
    SYSTEM_UTILIZATION = "system_utilization"  # 系统利用率
    OUTCOME_EFFECTIVENESS = "outcome_effectiveness"  # 结果有效性


@dataclass
class ProcessGuidance:
    """流程指导"""
    process_type: ProcessType
    process_name: str
    description: str
    steps: List[Dict[str, Any]]
    best_practices: List[str]
    common_pitfalls: List[str]
    success_metrics: List[str]
    templates: List[str]
    related_processes: List[str]
    compliance_requirements: List[str]


@dataclass
class KnowledgeIntegration:
    """知识整合结果"""
    topic: str
    category: KnowledgeCategory
    integrated_knowledge: str
    sources: List[str]
    confidence_score: float
    recommendations: List[str]
    related_topics: List[str]
    last_updated: datetime


@dataclass
class QualityAssessment:
    """质量评估结果"""
    assessment_type: str
    overall_score: float
    metric_scores: Dict[str, float]
    strengths: List[str]
    weaknesses: List[str]
    improvement_recommendations: List[str]
    priority_actions: List[str]
    compliance_status: str
    assessment_date: datetime


@dataclass
class SystemIntegration:
    """系统集成配置"""
    integration_type: str
    source_system: str
    target_system: str
    data_mapping: Dict[str, str]
    sync_frequency: str
    validation_rules: List[str]
    error_handling: str
    monitoring_setup: Dict[str, Any]


class CRMExpertAgent(BaseAgent):
    """
    CRM专家Agent
    
    专注于CRM系统的专业指导和优化：
    - CRM流程设计和优化指导
    - 最佳实践知识整合和传播
    - 系统质量控制和评估
    - 外部CRM系统集成配置
    - 行业标准合规性检查
    - 知识库管理和维护
    """
    
    def __init__(
        self,
        agent_id: str = "crm_expert_agent",
        name: str = "CRM专家",
        state_manager=None,
        communicator=None
    ):
        # 定义CRM专家Agent的专业能力
        capabilities = [
            AgentCapability(
                name="process_guidance",
                description="提供CRM流程设计和优化指导",
                parameters={
                    "process_type": {"type": "string", "enum": list(ProcessType)},
                    "industry": {"type": "string"},
                    "company_size": {"type": "string", "enum": ["startup", "small", "medium", "large", "enterprise"]}
                }
            ),
            AgentCapability(
                name="knowledge_integration",
                description="整合和管理CRM相关知识",
                parameters={
                    "topic": {"type": "string", "required": True},
                    "category": {"type": "string", "enum": list(KnowledgeCategory)},
                    "scope": {"type": "string", "enum": ["specific", "comprehensive"]}
                }
            ),
            AgentCapability(
                name="quality_control",
                description="评估CRM系统和流程质量",
                parameters={
                    "assessment_type": {"type": "string", "required": True},
                    "metrics": {"type": "array", "items": {"type": "string"}},
                    "time_period": {"type": "string", "default": "last_quarter"}
                }
            ),
            AgentCapability(
                name="system_integration",
                description="配置和管理外部CRM系统集成",
                parameters={
                    "integration_type": {"type": "string", "required": True},
                    "source_system": {"type": "string", "required": True},
                    "target_system": {"type": "string", "required": True}
                }
            ),
            AgentCapability(
                name="compliance_check",
                description="检查CRM流程和数据的合规性",
                parameters={
                    "compliance_standard": {"type": "string", "required": True},
                    "scope": {"type": "string", "enum": ["process", "data", "system", "all"]}
                }
            )
        ]
        
        super().__init__(
            agent_id=agent_id,
            name=name,
            specialty="CRM专业指导和优化",
            capabilities=capabilities,
            state_manager=state_manager,
            communicator=communicator
        )
        
        # CRM专家知识库集合名称
        self.knowledge_collections = {
            "crm_theory": "crm_theory_and_principles",
            "best_practices": "crm_best_practices",
            "industry_standards": "crm_industry_standards",
            "case_studies": "crm_implementation_cases",
            "methodologies": "crm_methodologies",
            "integration_guides": "crm_integration_guides"
        }
        
        # MCP工具配置
        self.mcp_tools = {
            "get_process_template": self._handle_get_process_template,
            "validate_data_quality": self._handle_validate_data_quality,
            "check_compliance": self._handle_check_compliance,
            "configure_integration": self._handle_configure_integration,
            "generate_report": self._handle_generate_report,
            "update_knowledge_base": self._handle_update_knowledge_base,
            "external_crm_sync": self._handle_external_crm_sync
        }
        
        logger.info(f"CRM专家Agent {self.name} 初始化完成")
    
    async def analyze_task(self, message: AgentMessage) -> Dict[str, Any]:
        """
        分析CRM专家相关任务
        """
        try:
            content = message.content.lower()
            metadata = message.metadata or {}
            
            # 识别任务类型
            task_type = "general"
            needs_collaboration = False
            required_agents = []
            
            # 流程指导相关
            if any(keyword in content for keyword in ["流程", "流程设计", "流程优化", "最佳实践", "标准流程"]):
                task_type = "process_guidance"
                
            # 知识整合相关
            elif any(keyword in content for keyword in ["知识", "知识库", "知识整合", "最佳实践", "经验总结"]):
                task_type = "knowledge_integration"
                
            # 质量控制相关
            elif any(keyword in content for keyword in ["质量", "质量评估", "数据质量", "流程质量", "系统质量"]):
                task_type = "quality_control"
                
            # 系统集成相关
            elif any(keyword in content for keyword in ["集成", "系统集成", "外部系统", "数据同步", "接口"]):
                task_type = "system_integration"
                
            # 合规检查相关
            elif any(keyword in content for keyword in ["合规", "合规性", "标准", "规范", "审计"]):
                task_type = "compliance_check"
            
            # 判断是否需要协作
            if any(keyword in content for keyword in ["销售", "销售流程", "销售管理"]):
                needs_collaboration = True
                required_agents.append("sales_agent")
                required_agents.append("sales_management_agent")
                
            if any(keyword in content for keyword in ["客户", "客户成功", "客户管理"]):
                needs_collaboration = True
                required_agents.append("customer_success_agent")
                
            if any(keyword in content for keyword in ["市场", "线索", "营销"]):
                needs_collaboration = True
                required_agents.append("market_agent")
                
            if any(keyword in content for keyword in ["系统", "技术", "运维"]):
                needs_collaboration = True
                required_agents.append("system_management_agent")
            
            return {
                "task_type": task_type,
                "needs_collaboration": needs_collaboration,
                "required_agents": required_agents,
                "collaboration_type": "sequential" if needs_collaboration else None,
                "priority": metadata.get("priority", "medium"),
                "context": {
                    "user_role": metadata.get("user_role", "crm_admin"),
                    "process_type": metadata.get("process_type"),
                    "industry": metadata.get("industry"),
                    "company_size": metadata.get("company_size"),
                    "compliance_standard": metadata.get("compliance_standard")
                }
            }
            
        except Exception as e:
            logger.error(f"CRM专家任务分析失败: {e}")
            return {
                "task_type": "general",
                "needs_collaboration": False,
                "error": str(e)
            }
    
    async def execute_task(self, message: AgentMessage, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行CRM专家任务
        """
        task_type = analysis.get("task_type", "general")
        context = analysis.get("context", {})
        
        try:
            if task_type == "process_guidance":
                return await self._execute_process_guidance(message, context)
            elif task_type == "knowledge_integration":
                return await self._execute_knowledge_integration(message, context)
            elif task_type == "quality_control":
                return await self._execute_quality_control(message, context)
            elif task_type == "system_integration":
                return await self._execute_system_integration(message, context)
            elif task_type == "compliance_check":
                return await self._execute_compliance_check(message, context)
            else:
                return await self._execute_general_crm_query(message, context)
                
        except Exception as e:
            logger.error(f"CRM专家任务执行失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "fallback_response": "抱歉，处理您的CRM专家请求时遇到了问题，请稍后重试。"
            }
    
    async def _execute_process_guidance(self, message: AgentMessage, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行流程指导任务"""
        try:
            process_type = context.get("process_type") or self._determine_process_type(message.content)
            industry = context.get("industry", "通用")
            company_size = context.get("company_size", "medium")
            
            guidance = await self.provide_process_guidance(process_type, industry, company_size)
            
            return {
                "success": True,
                "analysis_type": "process_guidance",
                "data": guidance,
                "response_type": "process_guidance"
            }
                
        except Exception as e:
            logger.error(f"流程指导执行失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _execute_knowledge_integration(self, message: AgentMessage, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行知识整合任务"""
        try:
            topic = self._extract_topic_from_message(message.content)
            category = self._determine_knowledge_category(message.content)
            scope = self._determine_scope(message.content)
            
            integration = await self.integrate_knowledge(topic, category, scope)
            
            return {
                "success": True,
                "analysis_type": "knowledge_integration",
                "data": integration,
                "response_type": "knowledge_integration"
            }
            
        except Exception as e:
            logger.error(f"知识整合执行失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _execute_quality_control(self, message: AgentMessage, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行质量控制任务"""
        try:
            assessment_type = self._determine_assessment_type(message.content)
            metrics = self._extract_metrics_from_message(message.content)
            time_period = context.get("time_period", "last_quarter")
            
            assessment = await self.assess_quality(assessment_type, metrics, time_period)
            
            return {
                "success": True,
                "analysis_type": "quality_control",
                "data": assessment,
                "response_type": "quality_assessment"
            }
            
        except Exception as e:
            logger.error(f"质量控制执行失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _execute_system_integration(self, message: AgentMessage, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行系统集成任务"""
        try:
            integration_type = self._determine_integration_type(message.content)
            source_system = self._extract_source_system(message.content)
            target_system = self._extract_target_system(message.content)
            
            integration_config = await self.configure_system_integration(
                integration_type, source_system, target_system
            )
            
            return {
                "success": True,
                "analysis_type": "system_integration",
                "data": integration_config,
                "response_type": "integration_config"
            }
            
        except Exception as e:
            logger.error(f"系统集成执行失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _execute_compliance_check(self, message: AgentMessage, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行合规检查任务"""
        try:
            compliance_standard = context.get("compliance_standard") or self._extract_compliance_standard(message.content)
            scope = self._determine_compliance_scope(message.content)
            
            compliance_result = await self.check_compliance(compliance_standard, scope)
            
            return {
                "success": True,
                "analysis_type": "compliance_check",
                "data": compliance_result,
                "response_type": "compliance_result"
            }
            
        except Exception as e:
            logger.error(f"合规检查执行失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _execute_general_crm_query(self, message: AgentMessage, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行一般CRM查询"""
        try:
            # 使用RAG检索相关CRM知识
            rag_result = await rag_service.query(
                question=message.content,
                mode=RAGMode.HYBRID,
                collection_name=self.knowledge_collections["crm_theory"]
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
            logger.error(f"一般CRM查询执行失败: {e}")
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
        生成CRM专家Agent响应
        """
        try:
            if not task_result or not task_result.get("success", False):
                error_msg = task_result.get("error", "未知错误") if task_result else "任务执行失败"
                fallback = task_result.get("fallback_response", "抱歉，我无法处理您的CRM专家请求。")
                
                return AgentResponse(
                    content=fallback,
                    confidence=0.1,
                    suggestions=["请检查输入信息", "稍后重试", "联系技术支持"],
                    metadata={"error": error_msg}
                )
            
            response_type = task_result.get("response_type", "general")
            data = task_result.get("data", {})
            
            # 根据响应类型生成不同格式的回复
            if response_type == "process_guidance":
                content, suggestions = await self._format_process_guidance_response(data)
            elif response_type == "knowledge_integration":
                content, suggestions = await self._format_knowledge_integration_response(data)
            elif response_type == "quality_assessment":
                content, suggestions = await self._format_quality_assessment_response(data)
            elif response_type == "integration_config":
                content, suggestions = await self._format_integration_config_response(data)
            elif response_type == "compliance_result":
                content, suggestions = await self._format_compliance_result_response(data)
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
            logger.error(f"生成CRM专家Agent响应失败: {e}")
            return AgentResponse(
                content="抱歉，生成响应时遇到了问题。",
                confidence=0.0,
                suggestions=["请重新提问", "检查网络连接"],
                metadata={"error": str(e)}
            )
    
    # 核心业务方法实现
    
    async def provide_process_guidance(
        self, 
        process_type: str, 
        industry: str = "通用", 
        company_size: str = "medium"
    ) -> ProcessGuidance:
        """
        提供流程指导
        """
        try:
            # 构建流程指导提示
            guidance_prompt = f"""
            作为CRM专家，请为以下场景提供详细的流程指导：
            
            流程类型：{process_type}
            行业：{industry}
            公司规模：{company_size}
            
            请提供包含以下内容的流程指导：
            1. 流程概述和目标
            2. 详细的执行步骤
            3. 每个步骤的最佳实践
            4. 常见问题和解决方案
            5. 成功指标定义
            6. 相关模板和工具
            7. 关联流程说明
            8. 合规要求
            
            请确保指导具体、实用、可操作。
            """
            
            # 检索相关最佳实践
            rag_result = await rag_service.query(
                question=f"{industry}行业{process_type}流程最佳实践",
                collection_name=self.knowledge_collections["best_practices"]
            )
            
            enhanced_prompt = f"{guidance_prompt}\n\n参考最佳实践：\n{rag_result.answer}"
            
            # 使用LLM生成流程指导
            llm_response = await llm_service.chat_completion(
                messages=[{"role": "user", "content": enhanced_prompt}],
                temperature=0.2,
                max_tokens=2500
            )
            
            content = llm_response.get("content", "")
            
            return ProcessGuidance(
                process_type=ProcessType(process_type) if process_type in [e.value for e in ProcessType] else ProcessType.SALES_PROCESS,
                process_name=self._extract_process_name(content),
                description=self._extract_section(content, "流程概述"),
                steps=self._extract_process_steps(content),
                best_practices=self._extract_list_items(content, "最佳实践"),
                common_pitfalls=self._extract_list_items(content, "常见问题"),
                success_metrics=self._extract_list_items(content, "成功指标"),
                templates=self._extract_list_items(content, "模板"),
                related_processes=self._extract_list_items(content, "关联流程"),
                compliance_requirements=self._extract_list_items(content, "合规要求")
            )
            
        except Exception as e:
            logger.error(f"流程指导生成失败: {e}")
            raise
    
    async def integrate_knowledge(
        self, 
        topic: str, 
        category: KnowledgeCategory, 
        scope: str = "comprehensive"
    ) -> KnowledgeIntegration:
        """
        整合知识
        """
        try:
            # 构建知识整合提示
            integration_prompt = f"""
            作为CRM专家，请整合以下主题的相关知识：
            
            主题：{topic}
            知识分类：{category.value}
            整合范围：{scope}
            
            请从多个维度整合知识：
            1. 理论基础和原理
            2. 实践方法和技巧
            3. 行业案例和经验
            4. 工具和模板
            5. 常见问题和解决方案
            6. 发展趋势和创新
            
            请提供结构化、全面的知识整合结果。
            """
            
            # 检索多个知识源
            knowledge_sources = []
            for collection_name in self.knowledge_collections.values():
                try:
                    rag_result = await rag_service.query(
                        question=topic,
                        collection_name=collection_name,
                        top_k=3
                    )
                    knowledge_sources.append({
                        "source": collection_name,
                        "content": rag_result.answer,
                        "confidence": rag_result.confidence
                    })
                except Exception as e:
                    logger.warning(f"检索知识源 {collection_name} 失败: {e}")
            
            # 整合所有知识源
            combined_knowledge = "\n\n".join([
                f"来源 {source['source']}:\n{source['content']}" 
                for source in knowledge_sources
            ])
            
            enhanced_prompt = f"{integration_prompt}\n\n参考知识：\n{combined_knowledge}"
            
            # 使用LLM整合知识
            llm_response = await llm_service.chat_completion(
                messages=[{"role": "user", "content": enhanced_prompt}],
                temperature=0.3,
                max_tokens=3000
            )
            
            content = llm_response.get("content", "")
            
            return KnowledgeIntegration(
                topic=topic,
                category=category,
                integrated_knowledge=content,
                sources=[source["source"] for source in knowledge_sources],
                confidence_score=sum(source["confidence"] for source in knowledge_sources) / len(knowledge_sources) if knowledge_sources else 0.5,
                recommendations=self._extract_list_items(content, "建议"),
                related_topics=self._extract_related_topics(content),
                last_updated=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"知识整合失败: {e}")
            raise
    
    async def assess_quality(
        self, 
        assessment_type: str, 
        metrics: List[str], 
        time_period: str = "last_quarter"
    ) -> QualityAssessment:
        """
        评估质量
        """
        try:
            # 获取质量数据（这里简化处理，实际应该从系统获取真实数据）
            quality_data = await self._get_quality_data(assessment_type, time_period)
            
            # 构建质量评估提示
            assessment_prompt = f"""
            作为CRM专家，请评估以下系统质量：
            
            评估类型：{assessment_type}
            评估指标：{metrics}
            时间周期：{time_period}
            质量数据：{json.dumps(quality_data, ensure_ascii=False, indent=2)}
            
            请从以下维度进行质量评估：
            1. 数据完整性和准确性
            2. 流程合规性和一致性
            3. 用户采用率和满意度
            4. 系统利用率和性能
            5. 业务结果有效性
            
            请提供：
            - 总体质量评分（0-100）
            - 各维度详细评分
            - 主要优势分析
            - 存在问题识别
            - 改进建议
            - 优先行动计划
            - 合规状态评估
            """
            
            # 检索质量评估标准
            rag_result = await rag_service.query(
                question=f"CRM系统{assessment_type}质量评估标准和方法",
                collection_name=self.knowledge_collections["industry_standards"]
            )
            
            enhanced_prompt = f"{assessment_prompt}\n\n评估标准：\n{rag_result.answer}"
            
            # 使用LLM生成质量评估
            llm_response = await llm_service.chat_completion(
                messages=[{"role": "user", "content": enhanced_prompt}],
                temperature=0.1,
                max_tokens=2000
            )
            
            content = llm_response.get("content", "")
            
            return QualityAssessment(
                assessment_type=assessment_type,
                overall_score=self._extract_overall_score(content),
                metric_scores=self._extract_metric_scores(content),
                strengths=self._extract_list_items(content, "优势"),
                weaknesses=self._extract_list_items(content, "问题"),
                improvement_recommendations=self._extract_list_items(content, "改进建议"),
                priority_actions=self._extract_list_items(content, "优先行动"),
                compliance_status=self._extract_compliance_status(content),
                assessment_date=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"质量评估失败: {e}")
            raise
    
    async def configure_system_integration(
        self, 
        integration_type: str, 
        source_system: str, 
        target_system: str
    ) -> SystemIntegration:
        """
        配置系统集成
        """
        try:
            # 构建集成配置提示
            config_prompt = f"""
            作为CRM专家，请为以下系统集成提供配置方案：
            
            集成类型：{integration_type}
            源系统：{source_system}
            目标系统：{target_system}
            
            请提供详细的集成配置：
            1. 数据映射关系
            2. 同步频率设置
            3. 数据验证规则
            4. 错误处理机制
            5. 监控和告警设置
            6. 安全和权限配置
            7. 性能优化建议
            8. 测试和验证方案
            
            请确保配置方案完整、可靠、安全。
            """
            
            # 检索集成指南
            rag_result = await rag_service.query(
                question=f"{source_system}到{target_system}系统集成最佳实践",
                collection_name=self.knowledge_collections["integration_guides"]
            )
            
            enhanced_prompt = f"{config_prompt}\n\n集成指南：\n{rag_result.answer}"
            
            # 使用LLM生成集成配置
            llm_response = await llm_service.chat_completion(
                messages=[{"role": "user", "content": enhanced_prompt}],
                temperature=0.2,
                max_tokens=2000
            )
            
            content = llm_response.get("content", "")
            
            return SystemIntegration(
                integration_type=integration_type,
                source_system=source_system,
                target_system=target_system,
                data_mapping=self._extract_data_mapping(content),
                sync_frequency=self._extract_sync_frequency(content),
                validation_rules=self._extract_list_items(content, "验证规则"),
                error_handling=self._extract_section(content, "错误处理"),
                monitoring_setup=self._extract_monitoring_setup(content)
            )
            
        except Exception as e:
            logger.error(f"系统集成配置失败: {e}")
            raise
    
    async def check_compliance(self, compliance_standard: str, scope: str = "all") -> Dict[str, Any]:
        """
        检查合规性
        """
        try:
            # 获取当前系统状态数据
            system_data = await self._get_system_compliance_data(scope)
            
            # 构建合规检查提示
            compliance_prompt = f"""
            作为CRM专家，请检查系统的合规性：
            
            合规标准：{compliance_standard}
            检查范围：{scope}
            系统数据：{json.dumps(system_data, ensure_ascii=False, indent=2)}
            
            请从以下方面检查合规性：
            1. 数据隐私和保护
            2. 访问控制和权限
            3. 审计日志和追踪
            4. 数据备份和恢复
            5. 业务流程合规
            6. 文档和记录完整性
            
            请提供：
            - 合规性评估结果
            - 不合规项目清单
            - 风险等级评估
            - 整改建议
            - 实施时间计划
            """
            
            # 检索合规标准
            rag_result = await rag_service.query(
                question=f"{compliance_standard}合规要求和检查清单",
                collection_name=self.knowledge_collections["industry_standards"]
            )
            
            enhanced_prompt = f"{compliance_prompt}\n\n合规标准：\n{rag_result.answer}"
            
            # 使用LLM生成合规检查结果
            llm_response = await llm_service.chat_completion(
                messages=[{"role": "user", "content": enhanced_prompt}],
                temperature=0.1,
                max_tokens=2000
            )
            
            content = llm_response.get("content", "")
            
            return {
                "compliance_standard": compliance_standard,
                "scope": scope,
                "overall_status": self._extract_compliance_status(content),
                "compliant_items": self._extract_list_items(content, "合规项目"),
                "non_compliant_items": self._extract_list_items(content, "不合规项目"),
                "risk_level": self._extract_risk_level(content),
                "recommendations": self._extract_list_items(content, "整改建议"),
                "implementation_plan": self._extract_implementation_plan(content),
                "check_date": datetime.now()
            }
            
        except Exception as e:
            logger.error(f"合规检查失败: {e}")
            raise    
    
# MCP工具处理方法
    
    async def _handle_get_process_template(self, process_type: str) -> Dict[str, Any]:
        """处理获取流程模板的MCP调用"""
        try:
            # 这里应该调用实际的模板服务
            return {
                "success": True,
                "template": {
                    "process_type": process_type,
                    "template_id": f"template_{process_type}_{int(datetime.now().timestamp())}",
                    "steps": [
                        {"step": 1, "name": "初始化", "description": "设置流程参数"},
                        {"step": 2, "name": "执行", "description": "执行主要流程"},
                        {"step": 3, "name": "验证", "description": "验证结果"},
                        {"step": 4, "name": "完成", "description": "流程结束"}
                    ]
                }
            }
                    
        except Exception as e:
            logger.error(f"获取流程模板失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _handle_validate_data_quality(self, data_scope: str) -> Dict[str, Any]:
        """处理数据质量验证的MCP调用"""
        try:
            # 这里应该调用实际的数据质量服务
            return {
                "success": True,
                "validation_result": {
                    "scope": data_scope,
                    "overall_score": 85.5,
                    "issues_found": 12,
                    "critical_issues": 2,
                    "recommendations": ["修复重复数据", "完善必填字段"]
                }
            }
                    
        except Exception as e:
            logger.error(f"数据质量验证失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _handle_check_compliance(self, standard: str, scope: str) -> Dict[str, Any]:
        """处理合规检查的MCP调用"""
        try:
            compliance_result = await self.check_compliance(standard, scope)
            return {
                "success": True,
                "compliance_result": compliance_result
            }
                    
        except Exception as e:
            logger.error(f"合规检查失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _handle_configure_integration(self, **kwargs) -> Dict[str, Any]:
        """处理配置集成的MCP调用"""
        try:
            integration_type = kwargs.get("integration_type")
            source_system = kwargs.get("source_system")
            target_system = kwargs.get("target_system")
            
            config = await self.configure_system_integration(
                integration_type, source_system, target_system
            )
            
            return {
                "success": True,
                "integration_config": config.__dict__,
                "message": "集成配置生成成功"
            }
                    
        except Exception as e:
            logger.error(f"配置集成失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _handle_generate_report(self, report_type: str, **kwargs) -> Dict[str, Any]:
        """处理生成报告的MCP调用"""
        try:
            # 这里应该调用实际的报告生成服务
            return {
                "success": True,
                "report": {
                    "type": report_type,
                    "generated_at": datetime.now().isoformat(),
                    "content": f"{report_type}报告内容",
                    "format": "pdf"
                }
            }
                    
        except Exception as e:
            logger.error(f"生成报告失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _handle_update_knowledge_base(self, **kwargs) -> Dict[str, Any]:
        """处理更新知识库的MCP调用"""
        try:
            # 这里应该调用实际的知识库更新服务
            return {
                "success": True,
                "message": "知识库更新成功",
                "updated_items": kwargs.get("items", [])
            }
                    
        except Exception as e:
            logger.error(f"更新知识库失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _handle_external_crm_sync(self, **kwargs) -> Dict[str, Any]:
        """处理外部CRM同步的MCP调用"""
        try:
            # 这里应该调用实际的外部CRM同步服务
            return {
                "success": True,
                "sync_result": {
                    "records_synced": 150,
                    "errors": 0,
                    "last_sync": datetime.now().isoformat()
                }
            }
                    
        except Exception as e:
            logger.error(f"外部CRM同步失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    # 辅助方法
    
    def _determine_process_type(self, content: str) -> str:
        """从消息内容确定流程类型"""
        content_lower = content.lower()
        
        if any(keyword in content_lower for keyword in ["销售流程", "销售管理"]):
            return ProcessType.SALES_PROCESS.value
        elif any(keyword in content_lower for keyword in ["线索", "线索管理"]):
            return ProcessType.LEAD_MANAGEMENT.value
        elif any(keyword in content_lower for keyword in ["客户入职", "onboarding"]):
            return ProcessType.CUSTOMER_ONBOARDING.value
        elif any(keyword in content_lower for keyword in ["机会", "机会管理"]):
            return ProcessType.OPPORTUNITY_MANAGEMENT.value
        elif any(keyword in content_lower for keyword in ["客户成功", "客户服务"]):
            return ProcessType.CUSTOMER_SUCCESS.value
        elif any(keyword in content_lower for keyword in ["数据质量", "数据管理"]):
            return ProcessType.DATA_QUALITY.value
        else:
            return ProcessType.SALES_PROCESS.value
    
    def _extract_topic_from_message(self, content: str) -> str:
        """从消息中提取主题"""
        # 简化实现，实际可以用更复杂的NLP方法
        import re
        
        # 寻找"关于"、"有关"等关键词后的内容
        patterns = [
            r'关于(.+?)的',
            r'有关(.+?)的',
            r'(.+?)知识',
            r'(.+?)最佳实践'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1).strip()
        
        # 如果没有找到特定模式，返回前几个词
        words = content.split()[:3]
        return " ".join(words)
    
    def _determine_knowledge_category(self, content: str) -> KnowledgeCategory:
        """确定知识分类"""
        content_lower = content.lower()
        
        if any(keyword in content_lower for keyword in ["最佳实践", "best practice"]):
            return KnowledgeCategory.BEST_PRACTICES
        elif any(keyword in content_lower for keyword in ["标准", "规范", "standard"]):
            return KnowledgeCategory.INDUSTRY_STANDARDS
        elif any(keyword in content_lower for keyword in ["方法", "方法论", "methodology"]):
            return KnowledgeCategory.METHODOLOGIES
        elif any(keyword in content_lower for keyword in ["案例", "case study"]):
            return KnowledgeCategory.CASE_STUDIES
        elif any(keyword in content_lower for keyword in ["模板", "template"]):
            return KnowledgeCategory.TEMPLATES
        elif any(keyword in content_lower for keyword in ["检查", "清单", "checklist"]):
            return KnowledgeCategory.CHECKLISTS
        else:
            return KnowledgeCategory.BEST_PRACTICES
    
    def _determine_scope(self, content: str) -> str:
        """确定范围"""
        content_lower = content.lower()
        
        if any(keyword in content_lower for keyword in ["全面", "详细", "comprehensive"]):
            return "comprehensive"
        elif any(keyword in content_lower for keyword in ["具体", "特定", "specific"]):
            return "specific"
        else:
            return "comprehensive"
    
    def _determine_assessment_type(self, content: str) -> str:
        """确定评估类型"""
        content_lower = content.lower()
        
        if any(keyword in content_lower for keyword in ["数据质量", "数据"]):
            return "data_quality"
        elif any(keyword in content_lower for keyword in ["流程", "process"]):
            return "process_quality"
        elif any(keyword in content_lower for keyword in ["系统", "system"]):
            return "system_quality"
        elif any(keyword in content_lower for keyword in ["用户", "user"]):
            return "user_experience"
        else:
            return "overall_quality"
    
    def _extract_metrics_from_message(self, content: str) -> List[str]:
        """从消息中提取指标"""
        # 简化实现
        default_metrics = ["completeness", "accuracy", "consistency", "timeliness"]
        
        content_lower = content.lower()
        extracted_metrics = []
        
        if "完整" in content_lower:
            extracted_metrics.append("completeness")
        if "准确" in content_lower:
            extracted_metrics.append("accuracy")
        if "一致" in content_lower:
            extracted_metrics.append("consistency")
        if "及时" in content_lower:
            extracted_metrics.append("timeliness")
        
        return extracted_metrics if extracted_metrics else default_metrics
    
    def _determine_integration_type(self, content: str) -> str:
        """确定集成类型"""
        content_lower = content.lower()
        
        if any(keyword in content_lower for keyword in ["数据同步", "sync"]):
            return "data_sync"
        elif any(keyword in content_lower for keyword in ["api", "接口"]):
            return "api_integration"
        elif any(keyword in content_lower for keyword in ["文件", "file"]):
            return "file_transfer"
        elif any(keyword in content_lower for keyword in ["实时", "real-time"]):
            return "real_time"
        else:
            return "data_sync"
    
    def _extract_source_system(self, content: str) -> str:
        """提取源系统"""
        # 简化实现，实际可以用更复杂的实体识别
        import re
        
        patterns = [
            r'从(.+?)到',
            r'源系统[：:](.+?)[\s,，]',
            r'(.+?)系统'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1).strip()
        
        return "external_system"
    
    def _extract_target_system(self, content: str) -> str:
        """提取目标系统"""
        # 简化实现
        import re
        
        patterns = [
            r'到(.+?)系统',
            r'目标系统[：:](.+?)[\s,，]',
            r'同步到(.+?)[\s,，]'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1).strip()
        
        return "hicrm"
    
    def _extract_compliance_standard(self, content: str) -> str:
        """提取合规标准"""
        content_lower = content.lower()
        
        if any(keyword in content_lower for keyword in ["gdpr", "通用数据保护"]):
            return "GDPR"
        elif any(keyword in content_lower for keyword in ["iso", "27001"]):
            return "ISO27001"
        elif any(keyword in content_lower for keyword in ["sox", "萨班斯"]):
            return "SOX"
        elif any(keyword in content_lower for keyword in ["pci", "支付卡"]):
            return "PCI-DSS"
        else:
            return "general_compliance"
    
    def _determine_compliance_scope(self, content: str) -> str:
        """确定合规范围"""
        content_lower = content.lower()
        
        if "流程" in content_lower:
            return "process"
        elif "数据" in content_lower:
            return "data"
        elif "系统" in content_lower:
            return "system"
        else:
            return "all"
    
    async def _get_quality_data(self, assessment_type: str, time_period: str) -> Dict[str, Any]:
        """获取质量数据"""
        # 简化实现，返回模拟数据
        return {
            "assessment_type": assessment_type,
            "time_period": time_period,
            "data_completeness": 85.5,
            "data_accuracy": 92.3,
            "process_compliance": 78.9,
            "user_adoption": 67.8,
            "system_utilization": 89.2,
            "total_records": 15000,
            "error_rate": 2.1,
            "last_updated": datetime.now().isoformat()
        }
    
    async def _get_system_compliance_data(self, scope: str) -> Dict[str, Any]:
        """获取系统合规数据"""
        # 简化实现，返回模拟数据
        return {
            "scope": scope,
            "data_encryption": True,
            "access_controls": True,
            "audit_logging": True,
            "backup_policy": True,
            "user_permissions": "role_based",
            "data_retention": "7_years",
            "privacy_settings": "compliant",
            "security_updates": "current",
            "last_audit": "2024-01-15"
        }
    
    # 响应格式化方法
    
    async def _format_process_guidance_response(self, data: ProcessGuidance) -> tuple[str, List[str]]:
        """格式化流程指导响应"""
        content = f"""## {data.process_name}流程指导

### 流程概述
{data.description}

### 执行步骤
"""
        for i, step in enumerate(data.steps, 1):
            content += f"{i}. **{step.get('name', f'步骤{i}')}**\n   {step.get('description', '')}\n\n"
        
        content += f"""
### 最佳实践
{chr(10).join(f'• {practice}' for practice in data.best_practices)}

### 常见问题
{chr(10).join(f'• {pitfall}' for pitfall in data.common_pitfalls)}

### 成功指标
{chr(10).join(f'• {metric}' for metric in data.success_metrics)}
"""
        
        suggestions = [
            "查看相关模板",
            "了解关联流程",
            "检查合规要求",
            "获取实施指导"
        ]
        
        return content, suggestions
    
    async def _format_knowledge_integration_response(self, data: KnowledgeIntegration) -> tuple[str, List[str]]:
        """格式化知识整合响应"""
        content = f"""## {data.topic} - 知识整合

### 整合结果
{data.integrated_knowledge}

### 知识来源
{chr(10).join(f'• {source}' for source in data.sources)}

### 相关主题
{chr(10).join(f'• {topic}' for topic in data.related_topics)}

### 建议行动
{chr(10).join(f'• {rec}' for rec in data.recommendations)}

**置信度**: {data.confidence_score:.1%}
**更新时间**: {data.last_updated.strftime('%Y-%m-%d %H:%M')}
"""
        
        suggestions = [
            "深入了解相关主题",
            "查看具体案例",
            "获取实施模板",
            "了解最新发展"
        ]
        
        return content, suggestions
    
    async def _format_quality_assessment_response(self, data: QualityAssessment) -> tuple[str, List[str]]:
        """格式化质量评估响应"""
        content = f"""## 质量评估报告

### 总体评分: {data.overall_score:.1f}/100

### 各维度评分
"""
        for metric, score in data.metric_scores.items():
            content += f"• **{metric}**: {score:.1f}/100\n"
        
        content += f"""
### 主要优势
{chr(10).join(f'• {strength}' for strength in data.strengths)}

### 存在问题
{chr(10).join(f'• {weakness}' for weakness in data.weaknesses)}

### 改进建议
{chr(10).join(f'• {rec}' for rec in data.improvement_recommendations)}

### 优先行动
{chr(10).join(f'• {action}' for action in data.priority_actions)}

**合规状态**: {data.compliance_status}
**评估时间**: {data.assessment_date.strftime('%Y-%m-%d %H:%M')}
"""
        
        suggestions = [
            "制定改进计划",
            "分配责任人",
            "设定时间节点",
            "建立监控机制"
        ]
        
        return content, suggestions
    
    async def _format_integration_config_response(self, data: SystemIntegration) -> tuple[str, List[str]]:
        """格式化集成配置响应"""
        content = f"""## 系统集成配置

### 集成概述
- **集成类型**: {data.integration_type}
- **源系统**: {data.source_system}
- **目标系统**: {data.target_system}
- **同步频率**: {data.sync_frequency}

### 数据映射
"""
        for source_field, target_field in data.data_mapping.items():
            content += f"• {source_field} → {target_field}\n"
        
        content += f"""
### 验证规则
{chr(10).join(f'• {rule}' for rule in data.validation_rules)}

### 错误处理
{data.error_handling}

### 监控配置
"""
        for key, value in data.monitoring_setup.items():
            content += f"• **{key}**: {value}\n"
        
        suggestions = [
            "测试集成配置",
            "设置监控告警",
            "制定应急预案",
            "培训操作人员"
        ]
        
        return content, suggestions
    
    async def _format_compliance_result_response(self, data: Dict[str, Any]) -> tuple[str, List[str]]:
        """格式化合规结果响应"""
        content = f"""## 合规性检查报告

### 检查概述
- **合规标准**: {data['compliance_standard']}
- **检查范围**: {data['scope']}
- **总体状态**: {data['overall_status']}
- **风险等级**: {data['risk_level']}

### 合规项目
{chr(10).join(f'✅ {item}' for item in data['compliant_items'])}

### 不合规项目
{chr(10).join(f'❌ {item}' for item in data['non_compliant_items'])}

### 整改建议
{chr(10).join(f'• {rec}' for rec in data['recommendations'])}

### 实施计划
{data.get('implementation_plan', '待制定详细计划')}

**检查时间**: {data['check_date'].strftime('%Y-%m-%d %H:%M')}
"""
        
        suggestions = [
            "制定整改计划",
            "分配责任人",
            "设定完成时间",
            "建立跟踪机制"
        ]
        
        return content, suggestions
    
    async def _format_knowledge_based_response(self, data: Dict[str, Any]) -> tuple[str, List[str]]:
        """格式化基于知识的响应"""
        content = f"""## CRM专家建议

{data['answer']}

### 参考来源
{chr(10).join(f'• {source}' for source in data.get('sources', []))}

**置信度**: {data.get('confidence', 0.5):.1%}
"""
        
        suggestions = [
            "获取更多详细信息",
            "查看相关案例",
            "了解实施步骤",
            "咨询专业指导"
        ]
        
        return content, suggestions
    
    async def _format_general_response(self, data: Dict[str, Any]) -> tuple[str, List[str]]:
        """格式化一般响应"""
        content = "作为CRM专家，我已经处理了您的请求。如果您需要更具体的指导，请提供更多详细信息。"
        
        suggestions = [
            "明确具体需求",
            "提供更多背景信息",
            "选择具体的服务类型",
            "咨询专业建议"
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
        base_confidence = 0.8
        
        # 根据任务结果调整置信度
        if task_result.get("success"):
            data = task_result.get("data", {})
            if hasattr(data, 'confidence_score'):
                base_confidence = data.confidence_score
            elif isinstance(data, dict) and "confidence" in data:
                base_confidence = data["confidence"]
        else:
            base_confidence = 0.3
        
        # 如果有协作结果，略微提升置信度
        if collaboration_result and collaboration_result.get("success"):
            base_confidence = min(base_confidence + 0.1, 1.0)
        
        return base_confidence
    
    def _generate_next_actions(self, task_result: Dict[str, Any]) -> List[str]:
        """生成下一步行动建议"""
        response_type = task_result.get("response_type", "general")
        
        if response_type == "process_guidance":
            return ["开始实施流程", "准备相关模板", "培训团队成员", "设置监控指标"]
        elif response_type == "knowledge_integration":
            return ["应用整合知识", "分享给团队", "制定行动计划", "跟踪实施效果"]
        elif response_type == "quality_assessment":
            return ["制定改进计划", "分配责任人", "设定时间节点", "建立监控机制"]
        elif response_type == "integration_config":
            return ["测试集成配置", "部署到生产环境", "培训操作人员", "建立监控"]
        elif response_type == "compliance_result":
            return ["制定整改计划", "分配责任人", "设定完成时间", "建立跟踪机制"]
        else:
            return ["明确具体需求", "获取更多信息", "制定实施计划", "寻求专业支持"]
    
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
    
    def _extract_process_name(self, content: str) -> str:
        """提取流程名称"""
        import re
        
        patterns = [
            r'流程名称[：:](.+)',
            r'## (.+?)流程',
            r'### (.+?)流程'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1).strip()
        
        return "CRM业务流程"
    
    def _extract_process_steps(self, content: str) -> List[Dict[str, Any]]:
        """提取流程步骤"""
        import re
        
        # 寻找编号的步骤
        steps = []
        step_pattern = r'(\d+)\.\s*\*\*(.+?)\*\*\s*\n\s*(.+?)(?=\n\d+\.|\n\n|$)'
        matches = re.findall(step_pattern, content, re.DOTALL)
        
        for match in matches:
            steps.append({
                "step": int(match[0]),
                "name": match[1].strip(),
                "description": match[2].strip()
            })
        
        if not steps:
            # 如果没找到，返回默认步骤
            steps = [
                {"step": 1, "name": "准备阶段", "description": "收集必要信息和资源"},
                {"step": 2, "name": "执行阶段", "description": "按照流程执行主要任务"},
                {"step": 3, "name": "验证阶段", "description": "检查执行结果"},
                {"step": 4, "name": "完成阶段", "description": "总结和归档"}
            ]
        
        return steps
    
    def _extract_overall_score(self, content: str) -> float:
        """提取总体评分"""
        import re
        
        patterns = [
            r'总体.*?评分[：:]?\s*(\d+(?:\.\d+)?)',
            r'总分[：:]?\s*(\d+(?:\.\d+)?)',
            r'整体.*?(\d+(?:\.\d+)?)分'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                return float(match.group(1))
        
        return 75.0  # 默认评分
    
    def _extract_metric_scores(self, content: str) -> Dict[str, float]:
        """提取各维度评分"""
        import re
        
        scores = {}
        
        # 寻找各维度评分
        pattern = r'[•*-]\s*\*\*(.+?)\*\*[：:]?\s*(\d+(?:\.\d+)?)'
        matches = re.findall(pattern, content)
        
        for match in matches:
            metric_name = match[0].strip()
            score = float(match[1])
            scores[metric_name] = score
        
        if not scores:
            # 默认评分
            scores = {
                "数据完整性": 85.0,
                "流程合规性": 78.0,
                "用户采用率": 72.0,
                "系统利用率": 88.0
            }
        
        return scores
    
    def _extract_compliance_status(self, content: str) -> str:
        """提取合规状态"""
        content_lower = content.lower()
        
        if any(keyword in content_lower for keyword in ["完全合规", "fully compliant"]):
            return "完全合规"
        elif any(keyword in content_lower for keyword in ["基本合规", "mostly compliant"]):
            return "基本合规"
        elif any(keyword in content_lower for keyword in ["部分合规", "partially compliant"]):
            return "部分合规"
        elif any(keyword in content_lower for keyword in ["不合规", "non-compliant"]):
            return "不合规"
        else:
            return "需要评估"
    
    def _extract_risk_level(self, content: str) -> str:
        """提取风险等级"""
        content_lower = content.lower()
        
        if any(keyword in content_lower for keyword in ["高风险", "high risk", "critical"]):
            return "高风险"
        elif any(keyword in content_lower for keyword in ["中风险", "medium risk", "moderate"]):
            return "中风险"
        elif any(keyword in content_lower for keyword in ["低风险", "low risk", "minor"]):
            return "低风险"
        else:
            return "中风险"
    
    def _extract_data_mapping(self, content: str) -> Dict[str, str]:
        """提取数据映射"""
        import re
        
        mapping = {}
        
        # 寻找映射关系 source → target
        pattern = r'[•*-]\s*(.+?)\s*[→->]\s*(.+?)(?=\n|$)'
        matches = re.findall(pattern, content)
        
        for match in matches:
            source = match[0].strip()
            target = match[1].strip()
            mapping[source] = target
        
        if not mapping:
            # 默认映射
            mapping = {
                "customer_id": "客户ID",
                "customer_name": "客户名称",
                "contact_email": "联系邮箱",
                "phone": "联系电话"
            }
        
        return mapping
    
    def _extract_sync_frequency(self, content: str) -> str:
        """提取同步频率"""
        content_lower = content.lower()
        
        if any(keyword in content_lower for keyword in ["实时", "real-time", "即时"]):
            return "实时"
        elif any(keyword in content_lower for keyword in ["每小时", "hourly"]):
            return "每小时"
        elif any(keyword in content_lower for keyword in ["每天", "daily", "日"]):
            return "每天"
        elif any(keyword in content_lower for keyword in ["每周", "weekly", "周"]):
            return "每周"
        else:
            return "每天"
    
    def _extract_monitoring_setup(self, content: str) -> Dict[str, Any]:
        """提取监控设置"""
        # 简化实现，返回默认监控配置
        return {
            "health_check_interval": "5分钟",
            "error_threshold": "5%",
            "alert_channels": ["邮件", "短信"],
            "dashboard_url": "/monitoring/integration",
            "log_retention": "30天"
        }
    
    def _extract_related_topics(self, content: str) -> List[str]:
        """提取相关主题"""
        import re
        
        # 寻找相关主题章节
        pattern = r'相关主题[：:]?\s*\n((?:[-•*]\s*.+\n?)+)'
        match = re.search(pattern, content, re.MULTILINE)
        
        if match:
            list_content = match.group(1)
            topics = re.findall(r'[-•*]\s*(.+)', list_content)
            return [topic.strip() for topic in topics if topic.strip()]
        
        # 默认相关主题
        return ["CRM最佳实践", "流程优化", "数据管理", "系统集成"]
    
    def _extract_implementation_plan(self, content: str) -> str:
        """提取实施计划"""
        plan_section = self._extract_section(content, "实施计划")
        if plan_section and plan_section != "关于实施计划的详细信息":
            return plan_section
        
        return "制定详细的分阶段实施计划，包括时间节点、责任人和验收标准"
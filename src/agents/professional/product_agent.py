"""
产品Agent - 专业化产品支持Agent

提供产品匹配、方案推荐、实施规划等产品专业功能
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
from src.services.opportunity_service import OpportunityService
from src.services.llm_service import llm_service
from src.services.rag_service import rag_service, RAGMode
from src.core.database import get_db

logger = logging.getLogger(__name__)


class SolutionType(str, Enum):
    """解决方案类型枚举"""
    STANDARD = "standard"  # 标准方案
    CUSTOMIZED = "customized"  # 定制方案
    HYBRID = "hybrid"  # 混合方案
    ENTERPRISE = "enterprise"  # 企业级方案


class ImplementationPhase(str, Enum):
    """实施阶段枚举"""
    PLANNING = "planning"  # 规划阶段
    PREPARATION = "preparation"  # 准备阶段
    DEPLOYMENT = "deployment"  # 部署阶段
    TESTING = "testing"  # 测试阶段
    TRAINING = "training"  # 培训阶段
    GO_LIVE = "go_live"  # 上线阶段
    SUPPORT = "support"  # 支持阶段


class TechnicalComplexity(str, Enum):
    """技术复杂度枚举"""
    LOW = "low"  # 低复杂度
    MEDIUM = "medium"  # 中等复杂度
    HIGH = "high"  # 高复杂度
    VERY_HIGH = "very_high"  # 极高复杂度


@dataclass
class ProductInfo:
    """产品信息"""
    id: str
    name: str
    category: str
    description: str
    features: List[str]
    technical_specs: Dict[str, Any]
    pricing: Dict[str, Any]
    compatibility: List[str]
    target_industries: List[str]
    implementation_time: str


@dataclass
class SolutionMatch:
    """产品方案匹配结果"""
    customer_id: str
    requirements: List[str]
    recommended_products: List[ProductInfo]
    solution_type: SolutionType
    match_score: float
    technical_fit: Dict[str, Any]
    business_fit: Dict[str, Any]
    implementation_complexity: TechnicalComplexity
    estimated_timeline: str
    estimated_cost: Dict[str, Any]
    risks: List[str]
    benefits: List[str]
    alternatives: List[Dict[str, Any]]
    match_date: datetime


@dataclass
class TechnicalProposal:
    """技术方案"""
    proposal_id: str
    customer_id: str
    solution_overview: str
    technical_architecture: Dict[str, Any]
    implementation_phases: List[Dict[str, Any]]
    resource_requirements: Dict[str, Any]
    timeline: Dict[str, Any]
    deliverables: List[Dict[str, Any]]
    success_criteria: List[str]
    risk_mitigation: List[Dict[str, Any]]
    support_model: Dict[str, Any]
    proposal_date: datetime
    validity_period: int  # days


@dataclass
class ImplementationPlan:
    """实施规划"""
    plan_id: str
    project_name: str
    customer_id: str
    solution_components: List[Dict[str, Any]]
    phases: List[Dict[str, Any]]
    milestones: List[Dict[str, Any]]
    resource_allocation: Dict[str, Any]
    timeline: Dict[str, Any]
    dependencies: List[Dict[str, Any]]
    risk_assessment: List[Dict[str, Any]]
    quality_assurance: Dict[str, Any]
    change_management: Dict[str, Any]
    success_metrics: List[str]
    plan_date: datetime


class ProductAgent(BaseAgent):
    """
    产品专业Agent
    
    专注于产品和技术方案，提供智能化的产品支持：
    - 产品匹配和方案推荐
    - 技术方案生成
    - 实施规划制定
    - 技术支持和咨询
    - 产品数据库访问
    """
    
    def __init__(
        self,
        agent_id: str = "product_agent",
        name: str = "产品专家",
        state_manager=None,
        communicator=None
    ):
        # 定义产品Agent的专业能力
        capabilities = [
            AgentCapability(
                name="match_solution",
                description="基于客户需求匹配最适合的产品解决方案",
                parameters={
                    "requirements": {"type": "array", "items": {"type": "string"}, "required": True},
                    "customer_context": {"type": "object", "required": True},
                    "solution_type": {"type": "string", "enum": list(SolutionType)},
                    "budget_range": {"type": "object"}
                }
            ),
            AgentCapability(
                name="generate_technical_proposal",
                description="生成详细的技术方案和实施建议",
                parameters={
                    "customer_id": {"type": "string", "required": True},
                    "solution_requirements": {"type": "object", "required": True},
                    "proposal_type": {"type": "string", "enum": ["standard", "detailed", "executive"]},
                    "include_pricing": {"type": "boolean", "default": True}
                }
            ),
            AgentCapability(
                name="create_implementation_plan",
                description="制定详细的实施规划和项目计划",
                parameters={
                    "project_scope": {"type": "object", "required": True},
                    "timeline_constraints": {"type": "object"},
                    "resource_constraints": {"type": "object"},
                    "risk_tolerance": {"type": "string", "enum": ["low", "medium", "high"]}
                }
            ),
            AgentCapability(
                name="provide_technical_support",
                description="提供技术咨询和问题解答",
                parameters={
                    "technical_question": {"type": "string", "required": True},
                    "context": {"type": "object"},
                    "urgency": {"type": "string", "enum": ["low", "medium", "high", "critical"]}
                }
            ),
            AgentCapability(
                name="product_database_access",
                description="访问产品数据库获取产品信息",
                parameters={
                    "query_type": {"type": "string", "required": True},
                    "filters": {"type": "object"},
                    "include_details": {"type": "boolean", "default": True}
                }
            )
        ]
        
        super().__init__(
            agent_id=agent_id,
            name=name,
            specialty="产品方案与技术支持",
            capabilities=capabilities,
            state_manager=state_manager,
            communicator=communicator
        )
        
        # 产品知识库集合名称
        self.knowledge_collections = {
            "product_catalog": "product_catalog",
            "technical_docs": "technical_documentation",
            "implementation_guides": "implementation_best_practices",
            "solution_templates": "solution_templates",
            "case_studies": "product_case_studies",
            "troubleshooting": "technical_troubleshooting"
        }
        
        # MCP工具配置
        self.mcp_tools = {
            "get_product_info": self._handle_get_product_info,
            "search_solutions": self._handle_search_solutions,
            "generate_quote": self._handle_generate_quote,
            "create_project_plan": self._handle_create_project_plan,
            "access_technical_docs": self._handle_access_technical_docs
        }
        
        logger.info(f"产品Agent {self.name} 初始化完成")
    
    async def analyze_task(self, message: AgentMessage) -> Dict[str, Any]:
        """
        分析产品相关任务
        """
        try:
            content = message.content.lower()
            metadata = message.metadata or {}
            
            # 识别任务类型
            task_type = "general"
            needs_collaboration = False
            required_agents = []
            
            # 产品匹配相关
            if any(keyword in content for keyword in ["产品匹配", "方案推荐", "解决方案", "产品选择", "技术选型"]):
                task_type = "solution_matching"
                
            # 技术方案相关
            elif any(keyword in content for keyword in ["技术方案", "技术建议", "架构设计", "方案设计"]):
                task_type = "technical_proposal"
                
            # 实施规划相关
            elif any(keyword in content for keyword in ["实施规划", "项目计划", "部署计划", "上线计划"]):
                task_type = "implementation_planning"
                
            # 技术支持相关
            elif any(keyword in content for keyword in ["技术问题", "技术支持", "技术咨询", "如何实现"]):
                task_type = "technical_support"
                
            # 产品信息查询相关
            elif any(keyword in content for keyword in ["产品信息", "产品功能", "产品特性", "产品介绍"]):
                task_type = "product_inquiry"
            
            # 判断是否需要协作
            if any(keyword in content for keyword in ["销售", "客户关系", "商务谈判", "价格"]):
                needs_collaboration = True
                required_agents.append("sales_agent")
                
            if any(keyword in content for keyword in ["市场分析", "竞争对手", "行业趋势"]):
                needs_collaboration = True
                required_agents.append("market_agent")
                
            if any(keyword in content for keyword in ["客户成功", "实施后", "用户培训"]):
                needs_collaboration = True
                required_agents.append("customer_success_agent")
            
            return {
                "task_type": task_type,
                "needs_collaboration": needs_collaboration,
                "required_agents": required_agents,
                "collaboration_type": "sequential" if needs_collaboration else None,
                "priority": metadata.get("priority", "medium"),
                "context": {
                    "user_role": metadata.get("user_role", "product_manager"),
                    "customer_id": metadata.get("customer_id"),
                    "opportunity_id": metadata.get("opportunity_id"),
                    "technical_complexity": metadata.get("technical_complexity"),
                    "budget_range": metadata.get("budget_range")
                }
            }
            
        except Exception as e:
            logger.error(f"产品任务分析失败: {e}")
            return {
                "task_type": "general",
                "needs_collaboration": False,
                "error": str(e)
            }
    
    async def execute_task(self, message: AgentMessage, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行产品任务
        """
        task_type = analysis.get("task_type", "general")
        context = analysis.get("context", {})
        
        try:
            if task_type == "solution_matching":
                return await self._execute_solution_matching(message, context)
            elif task_type == "technical_proposal":
                return await self._execute_technical_proposal(message, context)
            elif task_type == "implementation_planning":
                return await self._execute_implementation_planning(message, context)
            elif task_type == "technical_support":
                return await self._execute_technical_support(message, context)
            elif task_type == "product_inquiry":
                return await self._execute_product_inquiry(message, context)
            else:
                return await self._execute_general_product_query(message, context)
                
        except Exception as e:
            logger.error(f"产品任务执行失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "fallback_response": "抱歉，处理您的产品请求时遇到了问题，请稍后重试。"
            }
    
    async def _execute_solution_matching(self, message: AgentMessage, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行产品方案匹配任务"""
        try:
            # 提取客户需求
            requirements = self._extract_requirements_from_message(message.content)
            customer_id = context.get("customer_id")
            
            # 构建客户上下文
            customer_context = {
                "customer_id": customer_id,
                "requirements": requirements,
                "budget_range": context.get("budget_range"),
                "technical_complexity": context.get("technical_complexity")
            }
            
            solution_match = await self.match_solution(requirements, customer_context)
            
            return {
                "success": True,
                "analysis_type": "solution_matching",
                "data": solution_match,
                "response_type": "solution_match"
            }
            
        except Exception as e:
            logger.error(f"方案匹配执行失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _execute_technical_proposal(self, message: AgentMessage, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行技术方案生成任务"""
        try:
            customer_id = context.get("customer_id")
            if not customer_id:
                customer_id = self._extract_customer_id_from_message(message.content)
            
            # 构建方案需求
            solution_requirements = {
                "user_query": message.content,
                "technical_complexity": context.get("technical_complexity", "medium"),
                "budget_range": context.get("budget_range"),
                "timeline_constraints": self._extract_timeline_from_message(message.content)
            }
            
            if customer_id:
                proposal = await self.generate_technical_proposal(customer_id, solution_requirements)
                return {
                    "success": True,
                    "analysis_type": "technical_proposal",
                    "data": proposal,
                    "response_type": "technical_proposal"
                }
            else:
                # 提供一般性的技术方案指导
                guidance = await self._get_technical_proposal_guidance(message.content)
                return {
                    "success": True,
                    "analysis_type": "technical_proposal_guidance",
                    "data": guidance,
                    "response_type": "guidance"
                }
                
        except Exception as e:
            logger.error(f"技术方案执行失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _execute_implementation_planning(self, message: AgentMessage, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行实施规划任务"""
        try:
            # 构建项目范围
            project_scope = {
                "description": message.content,
                "customer_id": context.get("customer_id"),
                "technical_complexity": context.get("technical_complexity", "medium"),
                "timeline_constraints": self._extract_timeline_from_message(message.content),
                "resource_constraints": context.get("resource_constraints")
            }
            
            implementation_plan = await self.create_implementation_plan(project_scope)
            
            return {
                "success": True,
                "analysis_type": "implementation_planning",
                "data": implementation_plan,
                "response_type": "implementation_plan"
            }
            
        except Exception as e:
            logger.error(f"实施规划执行失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _execute_technical_support(self, message: AgentMessage, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行技术支持任务"""
        try:
            support_response = await self.provide_technical_support(
                message.content, 
                context
            )
            
            return {
                "success": True,
                "analysis_type": "technical_support",
                "data": support_response,
                "response_type": "technical_support"
            }
            
        except Exception as e:
            logger.error(f"技术支持执行失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _execute_product_inquiry(self, message: AgentMessage, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行产品信息查询任务"""
        try:
            product_info = await self._get_product_information(message.content, context)
            
            return {
                "success": True,
                "analysis_type": "product_inquiry",
                "data": product_info,
                "response_type": "product_info"
            }
            
        except Exception as e:
            logger.error(f"产品查询执行失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _execute_general_product_query(self, message: AgentMessage, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行一般产品查询"""
        try:
            # 使用RAG检索相关产品知识
            rag_result = await rag_service.query(
                question=message.content,
                mode=RAGMode.HYBRID,
                collection_name=self.knowledge_collections["product_catalog"]
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
            logger.error(f"一般产品查询执行失败: {e}")
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
        生成产品Agent响应
        """
        try:
            if not task_result or not task_result.get("success", False):
                error_msg = task_result.get("error", "未知错误") if task_result else "任务执行失败"
                fallback = task_result.get("fallback_response", "抱歉，我无法处理您的产品请求。")
                
                return AgentResponse(
                    content=fallback,
                    confidence=0.1,
                    suggestions=["请检查输入信息", "稍后重试", "联系技术支持"],
                    metadata={"error": error_msg}
                )
            
            response_type = task_result.get("response_type", "general")
            data = task_result.get("data", {})
            
            # 根据响应类型生成不同格式的回复
            if response_type == "solution_match":
                content, suggestions = await self._format_solution_match_response(data)
            elif response_type == "technical_proposal":
                content, suggestions = await self._format_technical_proposal_response(data)
            elif response_type == "implementation_plan":
                content, suggestions = await self._format_implementation_plan_response(data)
            elif response_type == "technical_support":
                content, suggestions = await self._format_technical_support_response(data)
            elif response_type == "product_info":
                content, suggestions = await self._format_product_info_response(data)
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
            logger.error(f"生成产品Agent响应失败: {e}")
            return AgentResponse(
                content="抱歉，生成响应时遇到了问题。",
                confidence=0.0,
                suggestions=["请重新提问", "检查网络连接"],
                metadata={"error": str(e)}
            )
    
    # 核心业务方法实现
    
    async def match_solution(self, requirements: List[str], customer_context: Dict[str, Any]) -> SolutionMatch:
        """
        基于客户需求匹配最适合的产品解决方案
        """
        try:
            customer_id = customer_context.get("customer_id", "")
            budget_range = customer_context.get("budget_range", {})
            
            # 构建方案匹配提示
            matching_prompt = f"""
            作为产品专家，请为以下客户需求匹配最适合的产品解决方案：
            
            客户需求：
            {chr(10).join(f"- {req}" for req in requirements)}
            
            客户背景：
            - 客户ID：{customer_id}
            - 预算范围：{budget_range}
            
            请从以下维度进行分析：
            1. 推荐产品列表（包含产品名称、功能特性、技术规格）
            2. 解决方案类型（标准/定制/混合/企业级）
            3. 技术匹配度评估
            4. 业务匹配度评估
            5. 实施复杂度分析
            6. 预估时间和成本
            7. 潜在风险识别
            8. 预期收益分析
            9. 替代方案建议
            
            请提供专业、详细的匹配分析。
            """
            
            # 检索产品目录
            product_catalog = await rag_service.query(
                question=f"匹配需求的产品：{', '.join(requirements)}",
                collection_name=self.knowledge_collections["product_catalog"]
            )
            
            # 检索解决方案模板
            solution_templates = await rag_service.query(
                question=f"类似需求的解决方案模板",
                collection_name=self.knowledge_collections["solution_templates"]
            )
            
            # 增强提示
            enhanced_prompt = f"""
            {matching_prompt}
            
            产品目录信息：
            {product_catalog.answer}
            
            解决方案模板：
            {solution_templates.answer}
            """
            
            # 使用LLM生成匹配分析
            llm_response = await llm_service.chat_completion(
                messages=[{"role": "user", "content": enhanced_prompt}],
                temperature=0.2,
                max_tokens=2500
            )
            
            content = llm_response.get("content", "")
            
            # 解析匹配结果
            return SolutionMatch(
                customer_id=customer_id,
                requirements=requirements,
                recommended_products=self._extract_recommended_products(content),
                solution_type=self._extract_solution_type(content),
                match_score=self._calculate_match_score(content, product_catalog.confidence),
                technical_fit=self._extract_technical_fit(content),
                business_fit=self._extract_business_fit(content),
                implementation_complexity=self._extract_complexity(content),
                estimated_timeline=self._extract_timeline(content),
                estimated_cost=self._extract_cost_estimate(content),
                risks=self._extract_list_items(content, "潜在风险"),
                benefits=self._extract_list_items(content, "预期收益"),
                alternatives=self._extract_alternatives(content),
                match_date=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"方案匹配失败: {e}")
            raise
    
    async def generate_technical_proposal(self, customer_id: str, solution_requirements: Dict[str, Any]) -> TechnicalProposal:
        """
        生成详细的技术方案和实施建议
        """
        try:
            # 获取客户信息
            customer_info = {}
            if customer_id:
                async with get_db() as db:
                    customer_service = CustomerService(db)
                    customer = await customer_service.get_customer(customer_id)
                    if customer:
                        customer_info = {
                            "name": customer.name,
                            "company": customer.company,
                            "industry": customer.industry,
                            "size": customer.size
                        }
            
            user_query = solution_requirements.get("user_query", "")
            technical_complexity = solution_requirements.get("technical_complexity", "medium")
            
            # 构建技术方案提示
            proposal_prompt = f"""
            作为技术架构师，请为以下客户生成详细的技术方案：
            
            客户信息：
            {json.dumps(customer_info, ensure_ascii=False, indent=2)}
            
            方案需求：
            - 具体需求：{user_query}
            - 技术复杂度：{technical_complexity}
            - 预算范围：{solution_requirements.get("budget_range", "待定")}
            - 时间约束：{solution_requirements.get("timeline_constraints", "待定")}
            
            请生成包含以下内容的技术方案：
            1. 方案概述
            2. 技术架构设计
            3. 实施阶段规划
            4. 资源需求分析
            5. 项目时间线
            6. 交付物清单
            7. 成功标准定义
            8. 风险缓解措施
            9. 支持服务模式
            
            方案要专业、可执行、符合行业最佳实践。
            """
            
            # 检索技术文档
            technical_docs = await rag_service.query(
                question=f"{customer_info.get('industry', '')}行业技术方案",
                collection_name=self.knowledge_collections["technical_docs"]
            )
            
            # 检索实施指南
            implementation_guide = await rag_service.query(
                question="技术方案实施最佳实践",
                collection_name=self.knowledge_collections["implementation_guides"]
            )
            
            # 增强提示
            enhanced_prompt = f"""
            {proposal_prompt}
            
            技术参考文档：
            {technical_docs.answer}
            
            实施指南：
            {implementation_guide.answer}
            """
            
            # 生成技术方案
            llm_response = await llm_service.chat_completion(
                messages=[{"role": "user", "content": enhanced_prompt}],
                temperature=0.1,
                max_tokens=3000
            )
            
            content = llm_response.get("content", "")
            
            # 生成方案ID
            proposal_id = f"proposal_{customer_id}_{int(datetime.now().timestamp())}"
            
            return TechnicalProposal(
                proposal_id=proposal_id,
                customer_id=customer_id,
                solution_overview=self._extract_section(content, "方案概述"),
                technical_architecture=self._extract_technical_architecture(content),
                implementation_phases=self._extract_implementation_phases(content),
                resource_requirements=self._extract_resource_requirements(content),
                timeline=self._extract_timeline_dict(content),
                deliverables=self._extract_deliverables(content),
                success_criteria=self._extract_list_items(content, "成功标准"),
                risk_mitigation=self._extract_risk_mitigation(content),
                support_model=self._extract_support_model(content),
                proposal_date=datetime.now(),
                validity_period=30  # 30天有效期
            )
            
        except Exception as e:
            logger.error(f"技术方案生成失败: {e}")
            raise
    
    async def create_implementation_plan(self, project_scope: Dict[str, Any]) -> ImplementationPlan:
        """
        制定详细的实施规划和项目计划
        """
        try:
            description = project_scope.get("description", "")
            customer_id = project_scope.get("customer_id", "")
            technical_complexity = project_scope.get("technical_complexity", "medium")
            
            # 构建实施规划提示
            planning_prompt = f"""
            作为项目经理，请为以下项目制定详细的实施规划：
            
            项目描述：{description}
            客户ID：{customer_id}
            技术复杂度：{technical_complexity}
            时间约束：{project_scope.get("timeline_constraints", "待定")}
            资源约束：{project_scope.get("resource_constraints", "待定")}
            
            请制定包含以下内容的实施规划：
            1. 项目阶段划分
            2. 关键里程碑设定
            3. 资源分配计划
            4. 详细时间安排
            5. 依赖关系分析
            6. 风险评估和应对
            7. 质量保证措施
            8. 变更管理流程
            9. 成功指标定义
            
            规划要详细、可执行、风险可控。
            """
            
            # 检索实施最佳实践
            best_practices = await rag_service.query(
                question=f"{technical_complexity}复杂度项目实施最佳实践",
                collection_name=self.knowledge_collections["implementation_guides"]
            )
            
            # 检索案例研究
            case_studies = await rag_service.query(
                question="类似项目实施案例",
                collection_name=self.knowledge_collections["case_studies"]
            )
            
            # 增强提示
            enhanced_prompt = f"""
            {planning_prompt}
            
            最佳实践参考：
            {best_practices.answer}
            
            案例研究：
            {case_studies.answer}
            """
            
            # 生成实施规划
            llm_response = await llm_service.chat_completion(
                messages=[{"role": "user", "content": enhanced_prompt}],
                temperature=0.1,
                max_tokens=3000
            )
            
            content = llm_response.get("content", "")
            
            # 生成规划ID
            plan_id = f"plan_{customer_id}_{int(datetime.now().timestamp())}"
            project_name = f"项目实施规划 - {customer_id}"
            
            return ImplementationPlan(
                plan_id=plan_id,
                project_name=project_name,
                customer_id=customer_id,
                solution_components=self._extract_solution_components(content),
                phases=self._extract_phases(content),
                milestones=self._extract_milestones(content),
                resource_allocation=self._extract_resource_allocation(content),
                timeline=self._extract_timeline_dict(content),
                dependencies=self._extract_dependencies(content),
                risk_assessment=self._extract_risk_assessment(content),
                quality_assurance=self._extract_quality_assurance(content),
                change_management=self._extract_change_management(content),
                success_metrics=self._extract_list_items(content, "成功指标"),
                plan_date=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"实施规划失败: {e}")
            raise
    
    async def provide_technical_support(self, technical_question: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        提供技术咨询和问题解答
        """
        try:
            urgency = context.get("urgency", "medium")
            
            # 构建技术支持提示
            support_prompt = f"""
            作为技术专家，请回答以下技术问题：
            
            问题：{technical_question}
            紧急程度：{urgency}
            上下文：{json.dumps(context, ensure_ascii=False, indent=2)}
            
            请提供：
            1. 问题分析
            2. 解决方案
            3. 实施步骤
            4. 注意事项
            5. 相关文档链接
            6. 后续建议
            
            回答要专业、准确、实用。
            """
            
            # 检索技术文档
            tech_docs = await rag_service.query(
                question=technical_question,
                collection_name=self.knowledge_collections["technical_docs"]
            )
            
            # 检索故障排除指南
            troubleshooting = await rag_service.query(
                question=technical_question,
                collection_name=self.knowledge_collections["troubleshooting"]
            )
            
            # 增强提示
            enhanced_prompt = f"""
            {support_prompt}
            
            技术文档参考：
            {tech_docs.answer}
            
            故障排除指南：
            {troubleshooting.answer}
            """
            
            # 生成技术支持响应
            llm_response = await llm_service.chat_completion(
                messages=[{"role": "user", "content": enhanced_prompt}],
                temperature=0.1,
                max_tokens=2000
            )
            
            content = llm_response.get("content", "")
            
            return {
                "question": technical_question,
                "answer": content,
                "urgency": urgency,
                "confidence": min(tech_docs.confidence + troubleshooting.confidence, 1.0),
                "sources": tech_docs.sources + troubleshooting.sources,
                "response_time": datetime.now().isoformat(),
                "follow_up_needed": urgency in ["high", "critical"]
            }
            
        except Exception as e:
            logger.error(f"技术支持失败: {e}")
            raise
    
    # 辅助方法实现
    
    def _extract_requirements_from_message(self, content: str) -> List[str]:
        """从消息中提取需求"""
        requirements = []
        
        # 简化实现，查找需求关键词
        import re
        
        # 查找明确的需求表述
        requirement_patterns = [
            r'需要([^。，,]*?)(?:[。，,]|$)',
            r'要求([^。，,]*?)(?:[。，,]|$)',
            r'希望([^。，,]*?)(?:[。，,]|$)',
            r'想要([^。，,]*?)(?:[。，,]|$)'
        ]
        
        for pattern in requirement_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if match.strip():
                    requirements.append(match.strip())
        
        # 如果没有找到明确需求，将整个内容作为需求
        if not requirements:
            requirements.append(content)
        
        return requirements[:10]  # 最多返回10个需求
    
    def _extract_customer_id_from_message(self, content: str) -> Optional[str]:
        """从消息中提取客户ID"""
        import re
        
        # 查找客户ID模式
        patterns = [
            r'客户[ID|id|编号][:：]?\s*([A-Za-z0-9_-]+)',
            r'客户([A-Za-z0-9_-]+)',
            r'([A-Za-z0-9_-]+)公司'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_timeline_from_message(self, content: str) -> str:
        """从消息中提取时间线"""
        import re
        
        timeline_patterns = [
            r'(\d+[个]?[月天周年])',
            r'(下?[个]?[月天周年])',
            r'(紧急|立即|尽快|ASAP)',
            r'(\d+月\d+日)',
            r'(Q[1-4])'
        ]
        
        for pattern in timeline_patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1)
        
        return "待定"
    
    def _extract_recommended_products(self, content: str) -> List[ProductInfo]:
        """提取推荐产品信息"""
        products = []
        
        # 简化实现，查找产品相关信息
        import re
        
        # 查找产品名称和描述
        product_pattern = r'产品[：:]([^。]*?)。'
        matches = re.findall(product_pattern, content)
        
        for i, match in enumerate(matches[:5]):  # 最多5个产品
            products.append(ProductInfo(
                id=f"product_{i+1}",
                name=f"推荐产品 {i+1}",
                category="CRM系统",
                description=match.strip(),
                features=[],
                technical_specs={},
                pricing={},
                compatibility=[],
                target_industries=[],
                implementation_time="待评估"
            ))
        
        return products
    
    def _extract_solution_type(self, content: str) -> SolutionType:
        """提取解决方案类型"""
        content_lower = content.lower()
        
        if "定制" in content_lower or "custom" in content_lower:
            return SolutionType.CUSTOMIZED
        elif "企业级" in content_lower or "enterprise" in content_lower:
            return SolutionType.ENTERPRISE
        elif "混合" in content_lower or "hybrid" in content_lower:
            return SolutionType.HYBRID
        else:
            return SolutionType.STANDARD
    
    def _calculate_match_score(self, content: str, rag_confidence: float) -> float:
        """计算匹配分数"""
        # 基于内容质量和RAG置信度计算匹配分数
        base_score = 0.7
        
        # 根据内容长度和详细程度调整
        if len(content) > 1000:
            base_score += 0.1
        
        # 结合RAG置信度
        final_score = min((base_score + rag_confidence) / 2, 1.0)
        
        return round(final_score, 2)
    
    def _extract_technical_fit(self, content: str) -> Dict[str, Any]:
        """提取技术匹配度"""
        return {
            "compatibility_score": 0.85,
            "technical_requirements_met": True,
            "integration_complexity": "medium",
            "scalability": "high"
        }
    
    def _extract_business_fit(self, content: str) -> Dict[str, Any]:
        """提取业务匹配度"""
        return {
            "business_alignment": 0.90,
            "roi_potential": "high",
            "implementation_feasibility": "high",
            "user_adoption_likelihood": "medium"
        }
    
    def _extract_complexity(self, content: str) -> TechnicalComplexity:
        """提取实施复杂度"""
        content_lower = content.lower()
        
        if "极高" in content_lower or "very high" in content_lower:
            return TechnicalComplexity.VERY_HIGH
        elif "高" in content_lower or "high" in content_lower:
            return TechnicalComplexity.HIGH
        elif "中" in content_lower or "medium" in content_lower:
            return TechnicalComplexity.MEDIUM
        else:
            return TechnicalComplexity.LOW
    
    def _extract_timeline(self, content: str) -> str:
        """提取预估时间线"""
        import re
        
        timeline_pattern = r'(\d+[个]?[月天周年])'
        match = re.search(timeline_pattern, content)
        
        if match:
            return match.group(1)
        
        return "3-6个月"
    
    def _extract_cost_estimate(self, content: str) -> Dict[str, Any]:
        """提取成本估算"""
        import re
        
        # 查找价格信息
        price_patterns = [
            r'(\d+)万',
            r'(\d+)元',
            r'(\d+)k',
            r'(\d+)万元'
        ]
        
        costs = []
        for pattern in price_patterns:
            matches = re.findall(pattern, content)
            costs.extend([int(match) for match in matches])
        
        if costs:
            return {
                "estimated_range": f"{min(costs)}-{max(costs)}万元",
                "currency": "CNY",
                "includes_implementation": True
            }
        
        return {
            "estimated_range": "待评估",
            "currency": "CNY",
            "includes_implementation": True
        }
    
    def _extract_list_items(self, content: str, section_name: str) -> List[str]:
        """提取列表项"""
        import re
        
        # 查找指定章节的列表项
        section_pattern = f"{section_name}[：:](.*?)(?=\\n\\d+\\.|\\n[一二三四五六七八九十]|$)"
        section_match = re.search(section_pattern, content, re.DOTALL)
        
        if section_match:
            section_content = section_match.group(1)
            # 查找列表项
            items = re.findall(r'[-•]\s*([^\\n]+)', section_content)
            return [item.strip() for item in items if item.strip()]
        
        return []
    
    def _extract_alternatives(self, content: str) -> List[Dict[str, Any]]:
        """提取替代方案"""
        alternatives = []
        
        # 简化实现
        alt_items = self._extract_list_items(content, "替代方案")
        
        for i, item in enumerate(alt_items[:3]):  # 最多3个替代方案
            alternatives.append({
                "name": f"替代方案 {i+1}",
                "description": item,
                "pros": [],
                "cons": [],
                "suitability": "medium"
            })
        
        return alternatives
    
    def _extract_section(self, content: str, section_name: str) -> str:
        """提取指定章节内容"""
        import re
        
        section_pattern = f"{section_name}[：:](.*?)(?=\\n\\d+\\.|\\n[一二三四五六七八九十]|$)"
        match = re.search(section_pattern, content, re.DOTALL)
        
        if match:
            return match.group(1).strip()
        
        return f"{section_name}内容待完善"
    
    def _extract_technical_architecture(self, content: str) -> Dict[str, Any]:
        """提取技术架构"""
        return {
            "architecture_type": "微服务架构",
            "components": ["前端界面", "业务逻辑层", "数据访问层", "数据库"],
            "technologies": ["React", "Node.js", "PostgreSQL", "Redis"],
            "deployment": "云原生部署",
            "scalability": "水平扩展"
        }
    
    def _extract_implementation_phases(self, content: str) -> List[Dict[str, Any]]:
        """提取实施阶段"""
        phases = [
            {
                "phase": "规划阶段",
                "duration": "2周",
                "activities": ["需求分析", "方案设计", "资源准备"],
                "deliverables": ["需求文档", "技术方案", "项目计划"]
            },
            {
                "phase": "开发阶段", 
                "duration": "8周",
                "activities": ["系统开发", "功能测试", "集成测试"],
                "deliverables": ["系统代码", "测试报告", "用户手册"]
            },
            {
                "phase": "部署阶段",
                "duration": "2周", 
                "activities": ["环境部署", "数据迁移", "系统上线"],
                "deliverables": ["生产环境", "数据迁移报告", "上线报告"]
            }
        ]
        
        return phases
    
    def _extract_resource_requirements(self, content: str) -> Dict[str, Any]:
        """提取资源需求"""
        return {
            "human_resources": {
                "project_manager": 1,
                "developers": 3,
                "testers": 2,
                "deployment_engineer": 1
            },
            "infrastructure": {
                "servers": "云服务器",
                "database": "PostgreSQL集群",
                "storage": "100GB",
                "bandwidth": "100Mbps"
            },
            "software_licenses": ["开发工具", "数据库许可", "监控工具"]
        }
    
    def _extract_timeline_dict(self, content: str) -> Dict[str, Any]:
        """提取时间线字典"""
        return {
            "total_duration": "12周",
            "start_date": "待定",
            "end_date": "待定",
            "key_milestones": [
                {"milestone": "需求确认", "date": "第2周"},
                {"milestone": "开发完成", "date": "第10周"},
                {"milestone": "系统上线", "date": "第12周"}
            ]
        }
    
    def _extract_deliverables(self, content: str) -> List[Dict[str, Any]]:
        """提取交付物"""
        return [
            {
                "name": "需求规格说明书",
                "type": "文档",
                "delivery_phase": "规划阶段",
                "description": "详细的功能和非功能需求"
            },
            {
                "name": "系统软件",
                "type": "软件",
                "delivery_phase": "开发阶段", 
                "description": "完整的CRM系统软件"
            },
            {
                "name": "用户培训",
                "type": "服务",
                "delivery_phase": "部署阶段",
                "description": "用户操作培训和技术培训"
            }
        ]
    
    def _extract_risk_mitigation(self, content: str) -> List[Dict[str, Any]]:
        """提取风险缓解措施"""
        return [
            {
                "risk": "技术风险",
                "probability": "medium",
                "impact": "high",
                "mitigation": "技术预研和原型验证"
            },
            {
                "risk": "进度风险",
                "probability": "medium", 
                "impact": "medium",
                "mitigation": "敏捷开发和定期检查点"
            }
        ]
    
    def _extract_support_model(self, content: str) -> Dict[str, Any]:
        """提取支持服务模式"""
        return {
            "support_type": "7x24小时支持",
            "response_time": {
                "critical": "1小时",
                "high": "4小时",
                "medium": "1工作日",
                "low": "3工作日"
            },
            "support_channels": ["电话", "邮件", "在线客服", "远程协助"],
            "maintenance_schedule": "每月定期维护"
        }
    
    def _extract_solution_components(self, content: str) -> List[Dict[str, Any]]:
        """提取解决方案组件"""
        return [
            {
                "component": "CRM核心模块",
                "description": "客户关系管理核心功能",
                "version": "v2.0",
                "dependencies": []
            },
            {
                "component": "数据分析模块",
                "description": "业务数据分析和报表",
                "version": "v1.5",
                "dependencies": ["CRM核心模块"]
            }
        ]
    
    def _extract_phases(self, content: str) -> List[Dict[str, Any]]:
        """提取项目阶段"""
        return [
            {
                "phase_name": "项目启动",
                "duration": "1周",
                "start_date": "待定",
                "end_date": "待定",
                "objectives": ["项目团队组建", "项目计划确认"],
                "deliverables": ["项目章程", "团队组织架构"]
            },
            {
                "phase_name": "需求分析",
                "duration": "2周", 
                "start_date": "待定",
                "end_date": "待定",
                "objectives": ["需求收集", "需求分析", "需求确认"],
                "deliverables": ["需求规格说明书", "原型设计"]
            }
        ]
    
    def _extract_milestones(self, content: str) -> List[Dict[str, Any]]:
        """提取里程碑"""
        return [
            {
                "milestone_name": "项目启动",
                "date": "第1周",
                "description": "项目正式启动",
                "criteria": ["项目团队到位", "项目计划批准"]
            },
            {
                "milestone_name": "需求确认",
                "date": "第3周",
                "description": "需求分析完成并确认",
                "criteria": ["需求文档签署", "原型验收通过"]
            }
        ]
    
    def _extract_resource_allocation(self, content: str) -> Dict[str, Any]:
        """提取资源分配"""
        return {
            "project_manager": {"allocation": "100%", "duration": "全程"},
            "senior_developer": {"allocation": "100%", "duration": "开发阶段"},
            "junior_developer": {"allocation": "50%", "duration": "开发阶段"},
            "tester": {"allocation": "100%", "duration": "测试阶段"},
            "deployment_engineer": {"allocation": "100%", "duration": "部署阶段"}
        }
    
    def _extract_dependencies(self, content: str) -> List[Dict[str, Any]]:
        """提取依赖关系"""
        return [
            {
                "task": "系统开发",
                "depends_on": ["需求确认", "技术方案设计"],
                "type": "finish_to_start"
            },
            {
                "task": "系统测试",
                "depends_on": ["系统开发"],
                "type": "finish_to_start"
            }
        ]
    
    def _extract_risk_assessment(self, content: str) -> List[Dict[str, Any]]:
        """提取风险评估"""
        return [
            {
                "risk_id": "R001",
                "risk_name": "技术风险",
                "description": "新技术应用可能带来的风险",
                "probability": "medium",
                "impact": "high",
                "mitigation_strategy": "技术预研和原型验证",
                "owner": "技术负责人"
            },
            {
                "risk_id": "R002", 
                "risk_name": "进度风险",
                "description": "项目进度延期风险",
                "probability": "medium",
                "impact": "medium", 
                "mitigation_strategy": "敏捷开发和定期检查",
                "owner": "项目经理"
            }
        ]
    
    def _extract_quality_assurance(self, content: str) -> Dict[str, Any]:
        """提取质量保证措施"""
        return {
            "quality_standards": ["ISO 9001", "CMMI Level 3"],
            "testing_strategy": {
                "unit_testing": "开发人员负责",
                "integration_testing": "测试团队负责",
                "system_testing": "独立测试团队",
                "user_acceptance_testing": "用户参与"
            },
            "code_review": "强制代码审查",
            "documentation": "完整的技术文档和用户文档"
        }
    
    def _extract_change_management(self, content: str) -> Dict[str, Any]:
        """提取变更管理"""
        return {
            "change_control_board": ["项目经理", "技术负责人", "客户代表"],
            "change_request_process": [
                "变更申请",
                "影响分析", 
                "变更评审",
                "变更批准",
                "变更实施"
            ],
            "change_approval_authority": {
                "minor_changes": "项目经理",
                "major_changes": "变更控制委员会"
            }
        }
    
    async def _get_product_information(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """获取产品信息"""
        try:
            # 使用RAG检索产品信息
            product_info = await rag_service.query(
                question=query,
                collection_name=self.knowledge_collections["product_catalog"]
            )
            
            return {
                "query": query,
                "product_info": product_info.answer,
                "sources": product_info.sources,
                "confidence": product_info.confidence,
                "related_products": [],
                "technical_specs": {},
                "pricing_info": "请联系销售获取报价"
            }
            
        except Exception as e:
            logger.error(f"获取产品信息失败: {e}")
            return {
                "query": query,
                "product_info": "暂时无法获取产品信息",
                "error": str(e)
            }
    
    async def _get_technical_proposal_guidance(self, query: str) -> Dict[str, Any]:
        """获取技术方案指导"""
        try:
            # 使用RAG检索技术方案指导
            guidance = await rag_service.query(
                question=f"技术方案制定指导：{query}",
                collection_name=self.knowledge_collections["technical_docs"]
            )
            
            return {
                "query": query,
                "guidance": guidance.answer,
                "best_practices": [],
                "templates": [],
                "confidence": guidance.confidence
            }
            
        except Exception as e:
            logger.error(f"获取技术方案指导失败: {e}")
            return {
                "query": query,
                "guidance": "暂时无法提供技术方案指导",
                "error": str(e)
            }
    
    # 响应格式化方法
    
    async def _format_solution_match_response(self, data: SolutionMatch) -> tuple[str, List[str]]:
        """格式化方案匹配响应"""
        content = f"""
## 产品方案匹配结果

### 客户需求分析
{chr(10).join(f"• {req}" for req in data.requirements)}

### 推荐解决方案
**方案类型**: {data.solution_type.value}
**匹配度**: {data.match_score * 100:.1f}%
**实施复杂度**: {data.implementation_complexity.value}

### 推荐产品
{chr(10).join(f"• **{product.name}**: {product.description}" for product in data.recommended_products[:3])}

### 预估信息
- **实施时间**: {data.estimated_timeline}
- **预估成本**: {data.estimated_cost.get('estimated_range', '待评估')}

### 主要收益
{chr(10).join(f"• {benefit}" for benefit in data.benefits[:5])}

### 潜在风险
{chr(10).join(f"• {risk}" for risk in data.risks[:3])}
        """.strip()
        
        suggestions = [
            "查看详细技术方案",
            "获取准确报价",
            "安排产品演示",
            "联系技术专家"
        ]
        
        return content, suggestions
    
    async def _format_technical_proposal_response(self, data: TechnicalProposal) -> tuple[str, List[str]]:
        """格式化技术方案响应"""
        content = f"""
## 技术方案建议

### 方案概述
{data.solution_overview}

### 实施阶段
{chr(10).join(f"**{i+1}. {phase.get('phase', f'阶段{i+1}')}** ({phase.get('duration', '待定')})" for i, phase in enumerate(data.implementation_phases[:4]))}

### 关键交付物
{chr(10).join(f"• {deliverable.get('name', '交付物')}: {deliverable.get('description', '详细描述')}" for deliverable in data.deliverables[:5])}

### 成功标准
{chr(10).join(f"• {criteria}" for criteria in data.success_criteria[:5])}

### 支持服务
- **支持类型**: {data.support_model.get('support_type', '标准支持')}
- **响应时间**: 关键问题1小时内响应

**方案有效期**: {data.validity_period}天
        """.strip()
        
        suggestions = [
            "制定详细实施计划",
            "评估资源需求",
            "安排技术评审",
            "准备项目启动"
        ]
        
        return content, suggestions
    
    async def _format_implementation_plan_response(self, data: ImplementationPlan) -> tuple[str, List[str]]:
        """格式化实施计划响应"""
        content = f"""
## 项目实施规划

### 项目信息
**项目名称**: {data.project_name}
**规划日期**: {data.plan_date.strftime('%Y-%m-%d')}

### 实施阶段
{chr(10).join(f"**{phase.get('phase_name', f'阶段{i+1}')}** ({phase.get('duration', '待定')})" for i, phase in enumerate(data.phases[:5]))}

### 关键里程碑
{chr(10).join(f"• **{milestone.get('milestone_name', '里程碑')}** - {milestone.get('date', '待定')}" for milestone in data.milestones[:5])}

### 资源配置
{chr(10).join(f"• {role}: {info.get('allocation', '待定')} ({info.get('duration', '待定')})" for role, info in list(data.resource_allocation.items())[:5])}

### 成功指标
{chr(10).join(f"• {metric}" for metric in data.success_metrics[:5])}

### 风险管控
{chr(10).join(f"• **{risk.get('risk_name', '风险')}**: {risk.get('mitigation_strategy', '待制定')}" for risk in data.risk_assessment[:3])}
        """.strip()
        
        suggestions = [
            "开始项目执行",
            "分配项目资源",
            "建立项目团队",
            "制定详细时间表"
        ]
        
        return content, suggestions
    
    async def _format_technical_support_response(self, data: Dict[str, Any]) -> tuple[str, List[str]]:
        """格式化技术支持响应"""
        content = f"""
## 技术支持解答

### 问题
{data.get('question', '技术问题')}

### 解决方案
{data.get('answer', '解决方案详情')}

### 置信度
{data.get('confidence', 0.8) * 100:.1f}%

### 响应时间
{data.get('response_time', '即时响应')}
        """.strip()
        
        suggestions = []
        if data.get('follow_up_needed', False):
            suggestions.extend([
                "安排技术专家跟进",
                "提供详细技术文档",
                "安排远程技术支持"
            ])
        else:
            suggestions.extend([
                "查看相关文档",
                "了解更多技术细节",
                "联系技术支持"
            ])
        
        return content, suggestions
    
    async def _format_product_info_response(self, data: Dict[str, Any]) -> tuple[str, List[str]]:
        """格式化产品信息响应"""
        content = f"""
## 产品信息

### 查询内容
{data.get('query', '产品查询')}

### 产品详情
{data.get('product_info', '产品信息详情')}

### 技术规格
{data.get('technical_specs', '技术规格待补充')}

### 价格信息
{data.get('pricing_info', '请联系销售获取报价')}

### 置信度
{data.get('confidence', 0.8) * 100:.1f}%
        """.strip()
        
        suggestions = [
            "获取详细报价",
            "安排产品演示",
            "下载产品资料",
            "联系产品专家"
        ]
        
        return content, suggestions
    
    async def _format_knowledge_based_response(self, data: Dict[str, Any]) -> tuple[str, List[str]]:
        """格式化知识库响应"""
        content = f"""
## 产品知识解答

{data.get('answer', '知识库回答')}

### 置信度
{data.get('confidence', 0.8) * 100:.1f}%

### 参考来源
{chr(10).join(f"• {source}" for source in data.get('sources', [])[:3])}
        """.strip()
        
        suggestions = [
            "查看更多相关信息",
            "获取详细文档",
            "联系产品专家",
            "安排技术咨询"
        ]
        
        return content, suggestions
    
    async def _format_general_response(self, data: Dict[str, Any]) -> tuple[str, List[str]]:
        """格式化一般响应"""
        content = "我已经为您分析了产品相关的问题，如需更详细的信息，请告诉我具体的需求。"
        
        suggestions = [
            "产品方案匹配",
            "技术方案咨询",
            "实施规划制定",
            "技术支持服务"
        ]
        
        return content, suggestions
    
    async def _integrate_collaboration_result(self, collaboration_result: Dict[str, Any]) -> str:
        """整合协作结果"""
        collab_results = collaboration_result.get("collaboration_results", [])
        
        if not collab_results:
            return ""
        
        integration_text = "\n## 协作建议\n"
        
        for result in collab_results[:3]:  # 最多显示3个协作结果
            agent_id = result.get("agent_id", "未知Agent")
            if "error" not in result:
                integration_text += f"• **{agent_id}**: 已提供专业建议\n"
            else:
                integration_text += f"• **{agent_id}**: 暂时无法提供建议\n"
        
        return integration_text
    
    def _calculate_response_confidence(
        self, 
        task_result: Dict[str, Any], 
        collaboration_result: Optional[Dict[str, Any]] = None
    ) -> float:
        """计算响应置信度"""
        base_confidence = 0.8
        
        # 根据任务结果调整置信度
        if task_result.get("success", False):
            data = task_result.get("data", {})
            if hasattr(data, 'match_score'):
                base_confidence = max(base_confidence, data.match_score)
            elif isinstance(data, dict) and 'confidence' in data:
                base_confidence = max(base_confidence, data['confidence'])
        else:
            base_confidence = 0.3
        
        # 如果有协作结果，略微提升置信度
        if collaboration_result and collaboration_result.get("success"):
            base_confidence = min(base_confidence + 0.1, 1.0)
        
        return round(base_confidence, 2)
    
    def _generate_next_actions(self, task_result: Dict[str, Any]) -> List[str]:
        """生成下一步行动建议"""
        response_type = task_result.get("response_type", "general")
        
        if response_type == "solution_match":
            return [
                "生成详细技术方案",
                "安排产品演示",
                "制定实施计划",
                "获取准确报价"
            ]
        elif response_type == "technical_proposal":
            return [
                "评审技术方案",
                "制定实施计划",
                "分配项目资源",
                "启动项目"
            ]
        elif response_type == "implementation_plan":
            return [
                "组建项目团队",
                "启动项目",
                "分配资源",
                "开始第一阶段"
            ]
        elif response_type == "technical_support":
            return [
                "实施解决方案",
                "验证解决效果",
                "更新技术文档",
                "分享解决经验"
            ]
        else:
            return [
                "明确具体需求",
                "选择合适的产品方案",
                "联系产品专家",
                "安排技术咨询"
            ]
    
    # MCP工具处理方法
    
    async def _handle_get_product_info(self, product_id: str) -> Dict[str, Any]:
        """处理获取产品信息的MCP调用"""
        try:
            # 使用RAG检索产品信息
            product_info = await rag_service.query(
                question=f"产品ID {product_id} 的详细信息",
                collection_name=self.knowledge_collections["product_catalog"]
            )
            
            return {
                "success": True,
                "product_id": product_id,
                "product_info": product_info.answer,
                "confidence": product_info.confidence,
                "sources": product_info.sources
            }
            
        except Exception as e:
            logger.error(f"获取产品信息失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _handle_search_solutions(self, **kwargs) -> Dict[str, Any]:
        """处理搜索解决方案的MCP调用"""
        try:
            query = kwargs.get("query", "")
            filters = kwargs.get("filters", {})
            
            # 使用RAG搜索解决方案
            solutions = await rag_service.query(
                question=f"搜索解决方案：{query}",
                collection_name=self.knowledge_collections["solution_templates"]
            )
            
            return {
                "success": True,
                "query": query,
                "solutions": solutions.answer,
                "confidence": solutions.confidence,
                "filters_applied": filters
            }
            
        except Exception as e:
            logger.error(f"搜索解决方案失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _handle_generate_quote(self, **kwargs) -> Dict[str, Any]:
        """处理生成报价的MCP调用"""
        try:
            # 简化实现
            return {
                "success": True,
                "quote_id": f"quote_{int(datetime.now().timestamp())}",
                "message": "报价生成功能需要与销售系统集成",
                "next_steps": ["联系销售团队", "提供详细需求", "安排商务洽谈"]
            }
            
        except Exception as e:
            logger.error(f"生成报价失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _handle_create_project_plan(self, **kwargs) -> Dict[str, Any]:
        """处理创建项目计划的MCP调用"""
        try:
            project_scope = kwargs.get("project_scope", {})
            
            # 简化实现
            plan_id = f"plan_{int(datetime.now().timestamp())}"
            
            return {
                "success": True,
                "plan_id": plan_id,
                "message": "项目计划已创建",
                "next_steps": ["审核计划", "分配资源", "启动项目"]
            }
            
        except Exception as e:
            logger.error(f"创建项目计划失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _handle_access_technical_docs(self, **kwargs) -> Dict[str, Any]:
        """处理访问技术文档的MCP调用"""
        try:
            doc_query = kwargs.get("query", "")
            
            # 使用RAG检索技术文档
            tech_docs = await rag_service.query(
                question=doc_query,
                collection_name=self.knowledge_collections["technical_docs"]
            )
            
            return {
                "success": True,
                "query": doc_query,
                "documents": tech_docs.answer,
                "confidence": tech_docs.confidence,
                "sources": tech_docs.sources
            }
            
        except Exception as e:
            logger.error(f"访问技术文档失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
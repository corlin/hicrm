"""
客户成功Agent - 专业化客户成功管理Agent

提供客户健康度监控、续约策略、价值挖掘等客户成功功能
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


class HealthStatus(str, Enum):
    """客户健康状态枚举"""
    HEALTHY = "healthy"  # 健康
    AT_RISK = "at_risk"  # 有风险
    CRITICAL = "critical"  # 危险
    CHURNED = "churned"  # 已流失


class RenewalStage(str, Enum):
    """续约阶段枚举"""
    EARLY_ENGAGEMENT = "early_engagement"  # 早期接触
    NEEDS_ASSESSMENT = "needs_assessment"  # 需求评估
    PROPOSAL = "proposal"  # 方案提议
    NEGOTIATION = "negotiation"  # 商务谈判
    CONTRACT_RENEWAL = "contract_renewal"  # 合同续约


class ExpansionType(str, Enum):
    """扩展类型枚举"""
    UPSELL = "upsell"  # 升级销售
    CROSS_SELL = "cross_sell"  # 交叉销售
    SEAT_EXPANSION = "seat_expansion"  # 席位扩展
    FEATURE_UPGRADE = "feature_upgrade"  # 功能升级


@dataclass
class HealthScore:
    """客户健康度评分"""
    customer_id: str
    overall_score: float  # 0-100
    status: HealthStatus
    factors: Dict[str, float]  # 各维度评分
    risk_indicators: List[str]
    positive_signals: List[str]
    recommendations: List[str]
    last_updated: datetime
    trend: str  # improving, stable, declining


@dataclass
class RenewalStrategy:
    """续约策略"""
    customer_id: str
    contract_end_date: datetime
    renewal_probability: float
    current_stage: RenewalStage
    key_stakeholders: List[Dict[str, Any]]
    value_proposition: str
    pricing_strategy: str
    timeline: Dict[str, datetime]
    success_factors: List[str]
    risks: List[str]
    action_plan: List[Dict[str, Any]]


@dataclass
class ExpansionOpportunity:
    """扩展机会"""
    customer_id: str
    opportunity_type: ExpansionType
    potential_value: float
    probability: float
    timeline: str
    requirements: List[str]
    business_case: str
    stakeholders: List[str]
    implementation_plan: str
    success_metrics: List[str]
    identified_date: datetime


@dataclass
class ValueRealization:
    """价值实现分析"""
    customer_id: str
    realized_value: float
    potential_value: float
    value_gap: float
    value_drivers: List[str]
    barriers: List[str]
    improvement_opportunities: List[str]
    roi_metrics: Dict[str, float]
    success_stories: List[str]


class CustomerSuccessAgent(BaseAgent):
    """
    客户成功专业Agent
    
    专注于客户成功管理的各个环节：
    - 客户健康度监控和预警
    - 续约策略制定和执行
    - 扩展机会识别和推进
    - 客户价值实现分析
    - 客户满意度管理
    - 客户使用数据分析
    """
    
    def __init__(
        self,
        agent_id: str = "customer_success_agent",
        name: str = "客户成功专家",
        state_manager=None,
        communicator=None
    ):
        # 定义客户成功Agent的专业能力
        capabilities = [
            AgentCapability(
                name="health_monitoring",
                description="监控客户健康度并提供预警",
                parameters={
                    "customer_id": {"type": "string", "required": True},
                    "monitoring_period": {"type": "string", "default": "last_30_days"},
                    "include_predictions": {"type": "boolean", "default": True}
                }
            ),
            AgentCapability(
                name="renewal_strategy",
                description="制定客户续约策略",
                parameters={
                    "customer_id": {"type": "string", "required": True},
                    "contract_end_date": {"type": "string", "required": True},
                    "strategy_type": {"type": "string", "enum": ["proactive", "reactive", "retention"]}
                }
            ),
            AgentCapability(
                name="expansion_identification",
                description="识别客户扩展机会",
                parameters={
                    "customer_id": {"type": "string", "required": True},
                    "expansion_types": {"type": "array", "items": {"type": "string"}},
                    "minimum_value": {"type": "number", "default": 10000}
                }
            ),
            AgentCapability(
                name="value_analysis",
                description="分析客户价值实现情况",
                parameters={
                    "customer_id": {"type": "string", "required": True},
                    "analysis_period": {"type": "string", "default": "last_quarter"},
                    "include_benchmarks": {"type": "boolean", "default": True}
                }
            ),
            AgentCapability(
                name="customer_data_access",
                description="访问客户使用数据和行为分析",
                parameters={
                    "customer_id": {"type": "string", "required": True},
                    "data_types": {"type": "array", "items": {"type": "string"}},
                    "time_range": {"type": "string", "default": "last_month"}
                }
            )
        ]
        
        super().__init__(
            agent_id=agent_id,
            name=name,
            specialty="客户成功管理",
            capabilities=capabilities,
            state_manager=state_manager,
            communicator=communicator
        ) 
       
        # 客户成功知识库集合名称
        self.knowledge_collections = {
            "success_methodology": "customer_success_methodology",
            "renewal_strategies": "renewal_best_practices", 
            "expansion_playbooks": "expansion_opportunity_playbooks",
            "value_frameworks": "customer_value_frameworks",
            "case_studies": "customer_success_cases"
        }
        
        # MCP工具配置
        self.mcp_tools = {
            "get_usage_data": self._handle_get_usage_data,
            "get_support_tickets": self._handle_get_support_tickets,
            "get_satisfaction_scores": self._handle_get_satisfaction_scores,
            "create_health_alert": self._handle_create_health_alert,
            "schedule_check_in": self._handle_schedule_check_in,
            "update_renewal_status": self._handle_update_renewal_status,
            "track_expansion_opportunity": self._handle_track_expansion_opportunity
        }
        
        logger.info(f"客户成功Agent {self.name} 初始化完成")
    
    async def analyze_task(self, message: AgentMessage) -> Dict[str, Any]:
        """
        分析客户成功相关任务
        """
        try:
            content = message.content.lower()
            metadata = message.metadata or {}
            
            # 识别任务类型
            task_type = "general"
            needs_collaboration = False
            required_agents = []
            
            # 健康度监控相关
            if any(keyword in content for keyword in ["健康度", "客户状态", "风险预警", "流失预警"]):
                task_type = "health_monitoring"
                
            # 续约策略相关
            elif any(keyword in content for keyword in ["续约", "续费", "合同续签", "续约策略"]):
                task_type = "renewal_strategy"
                
            # 扩展机会相关
            elif any(keyword in content for keyword in ["扩展", "增购", "升级", "交叉销售"]):
                task_type = "expansion_identification"
                
            # 价值分析相关
            elif any(keyword in content for keyword in ["价值分析", "roi", "投资回报", "价值实现"]):
                task_type = "value_analysis"
                
            # 客户数据访问相关
            elif any(keyword in content for keyword in ["使用数据", "行为分析", "使用情况", "活跃度"]):
                task_type = "customer_data_access"
            
            # 判断是否需要协作
            if any(keyword in content for keyword in ["销售", "商务谈判", "价格"]):
                needs_collaboration = True
                required_agents.append("sales_agent")
                
            if any(keyword in content for keyword in ["产品", "功能", "技术", "实施"]):
                needs_collaboration = True
                required_agents.append("product_agent")
                
            if any(keyword in content for keyword in ["市场", "竞争", "行业"]):
                needs_collaboration = True
                required_agents.append("market_agent")
            
            return {
                "task_type": task_type,
                "needs_collaboration": needs_collaboration,
                "required_agents": required_agents,
                "collaboration_type": "sequential" if needs_collaboration else None,
                "priority": metadata.get("priority", "medium"),
                "context": {
                    "user_role": metadata.get("user_role", "customer_success_manager"),
                    "customer_id": metadata.get("customer_id"),
                    "time_period": metadata.get("time_period", "current_month"),
                    "urgency": metadata.get("urgency", "normal")
                }
            }
            
        except Exception as e:
            logger.error(f"客户成功任务分析失败: {e}")
            return {
                "task_type": "general",
                "needs_collaboration": False,
                "error": str(e)
            }
    
    async def execute_task(self, message: AgentMessage, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行客户成功任务
        """
        task_type = analysis.get("task_type", "general")
        context = analysis.get("context", {})
        
        try:
            if task_type == "health_monitoring":
                return await self._execute_health_monitoring(message, context)
            elif task_type == "renewal_strategy":
                return await self._execute_renewal_strategy(message, context)
            elif task_type == "expansion_identification":
                return await self._execute_expansion_identification(message, context)
            elif task_type == "value_analysis":
                return await self._execute_value_analysis(message, context)
            elif task_type == "customer_data_access":
                return await self._execute_customer_data_access(message, context)
            else:
                return await self._execute_general_success_query(message, context)
                
        except Exception as e:
            logger.error(f"客户成功任务执行失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "fallback_response": "抱歉，处理您的客户成功请求时遇到了问题，请稍后重试。"
            }
    
    async def _execute_health_monitoring(self, message: AgentMessage, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行健康度监控任务"""
        try:
            customer_id = context.get("customer_id")
            if not customer_id:
                customer_id = self._extract_customer_id_from_message(message.content)
            
            monitoring_period = context.get("time_period", "last_30_days")
            
            if customer_id:
                health_score = await self.monitor_health_score(customer_id, monitoring_period)
                return {
                    "success": True,
                    "analysis_type": "health_monitoring",
                    "data": health_score,
                    "response_type": "health_monitoring"
                }
            else:
                # 提供一般性的健康度监控指导
                guidance = await self._get_health_monitoring_guidance(message.content)
                return {
                    "success": True,
                    "analysis_type": "health_monitoring_guidance",
                    "data": guidance,
                    "response_type": "guidance"
                }
                
        except Exception as e:
            logger.error(f"健康度监控执行失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _execute_renewal_strategy(self, message: AgentMessage, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行续约策略任务"""
        try:
            customer_id = context.get("customer_id")
            if not customer_id:
                customer_id = self._extract_customer_id_from_message(message.content)
            
            if customer_id:
                strategy = await self.develop_renewal_strategy(customer_id)
                return {
                    "success": True,
                    "analysis_type": "renewal_strategy",
                    "data": strategy,
                    "response_type": "renewal_strategy"
                }
            else:
                # 提供一般性的续约策略指导
                guidance = await self._get_renewal_strategy_guidance(message.content)
                return {
                    "success": True,
                    "analysis_type": "renewal_strategy_guidance",
                    "data": guidance,
                    "response_type": "guidance"
                }
                
        except Exception as e:
            logger.error(f"续约策略执行失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _execute_expansion_identification(self, message: AgentMessage, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行扩展机会识别任务"""
        try:
            customer_id = context.get("customer_id")
            if not customer_id:
                customer_id = self._extract_customer_id_from_message(message.content)
            
            if customer_id:
                opportunities = await self.identify_expansion_opportunities(customer_id)
                return {
                    "success": True,
                    "analysis_type": "expansion_identification",
                    "data": opportunities,
                    "response_type": "expansion_opportunities"
                }
            else:
                # 提供一般性的扩展机会识别指导
                guidance = await self._get_expansion_identification_guidance(message.content)
                return {
                    "success": True,
                    "analysis_type": "expansion_identification_guidance",
                    "data": guidance,
                    "response_type": "guidance"
                }
                
        except Exception as e:
            logger.error(f"扩展机会识别执行失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _execute_value_analysis(self, message: AgentMessage, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行价值分析任务"""
        try:
            customer_id = context.get("customer_id")
            if not customer_id:
                customer_id = self._extract_customer_id_from_message(message.content)
            
            analysis_period = context.get("time_period", "last_quarter")
            
            if customer_id:
                value_analysis = await self.analyze_value_realization(customer_id, analysis_period)
                return {
                    "success": True,
                    "analysis_type": "value_analysis",
                    "data": value_analysis,
                    "response_type": "value_analysis"
                }
            else:
                # 提供一般性的价值分析指导
                guidance = await self._get_value_analysis_guidance(message.content)
                return {
                    "success": True,
                    "analysis_type": "value_analysis_guidance",
                    "data": guidance,
                    "response_type": "guidance"
                }
                
        except Exception as e:
            logger.error(f"价值分析执行失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _execute_customer_data_access(self, message: AgentMessage, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行客户数据访问任务"""
        try:
            customer_id = context.get("customer_id")
            if not customer_id:
                customer_id = self._extract_customer_id_from_message(message.content)
            
            time_range = context.get("time_period", "last_month")
            data_types = self._extract_data_types_from_message(message.content)
            
            if customer_id:
                customer_data = await self._get_customer_usage_data(customer_id, time_range, data_types)
                return {
                    "success": True,
                    "analysis_type": "customer_data_access",
                    "data": customer_data,
                    "response_type": "customer_data"
                }
            else:
                return {
                    "success": False,
                    "error": "无法识别客户ID"
                }
                
        except Exception as e:
            logger.error(f"客户数据访问执行失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _execute_general_success_query(self, message: AgentMessage, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行一般客户成功查询"""
        try:
            # 使用RAG检索相关客户成功知识
            rag_result = await rag_service.query(
                question=message.content,
                mode=RAGMode.HYBRID,
                collection_name=self.knowledge_collections["success_methodology"]
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
            logger.error(f"一般客户成功查询执行失败: {e}")
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
        生成客户成功Agent响应
        """
        try:
            if not task_result or not task_result.get("success", False):
                error_msg = task_result.get("error", "未知错误") if task_result else "任务执行失败"
                fallback = task_result.get("fallback_response", "抱歉，我无法处理您的客户成功请求。")
                
                return AgentResponse(
                    content=fallback,
                    confidence=0.1,
                    suggestions=["请检查输入信息", "稍后重试", "联系技术支持"],
                    metadata={"error": error_msg}
                )
            
            response_type = task_result.get("response_type", "general")
            data = task_result.get("data", {})
            
            # 根据响应类型生成不同格式的回复
            if response_type == "health_monitoring":
                content, suggestions = await self._format_health_monitoring_response(data)
            elif response_type == "renewal_strategy":
                content, suggestions = await self._format_renewal_strategy_response(data)
            elif response_type == "expansion_opportunities":
                content, suggestions = await self._format_expansion_opportunities_response(data)
            elif response_type == "value_analysis":
                content, suggestions = await self._format_value_analysis_response(data)
            elif response_type == "customer_data":
                content, suggestions = await self._format_customer_data_response(data)
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
            logger.error(f"生成客户成功Agent响应失败: {e}")
            return AgentResponse(
                content="抱歉，生成响应时遇到了问题。",
                confidence=0.0,
                suggestions=["请重新提问", "检查网络连接"],
                metadata={"error": str(e)}
            )
    
    # 核心业务方法实现
    
    async def monitor_health_score(self, customer_id: str, monitoring_period: str = "last_30_days") -> HealthScore:
        """
        监控客户健康度
        """
        try:
            # 获取客户基础信息
            async with get_db() as db:
                customer_service = CustomerService(db)
                customer = await customer_service.get_customer(customer_id)
                
                if not customer:
                    raise ValueError(f"客户不存在: {customer_id}")
            
            # 获取客户使用数据和行为数据
            usage_data = await self._get_customer_usage_data(customer_id, monitoring_period)
            support_data = await self._get_customer_support_data(customer_id, monitoring_period)
            satisfaction_data = await self._get_customer_satisfaction_data(customer_id, monitoring_period)
            
            # 构建健康度分析提示
            health_prompt = f"""
            作为客户成功专家，请分析以下客户的健康度：
            
            客户信息：
            - 客户ID：{customer_id}
            - 公司：{customer.company}
            - 行业：{customer.industry}
            - 规模：{customer.size}
            
            使用数据：{json.dumps(usage_data, ensure_ascii=False, indent=2)}
            支持数据：{json.dumps(support_data, ensure_ascii=False, indent=2)}
            满意度数据：{json.dumps(satisfaction_data, ensure_ascii=False, indent=2)}
            
            请从以下维度评估客户健康度（0-100分）：
            1. 产品使用活跃度
            2. 功能采用深度
            3. 支持请求频率和类型
            4. 客户满意度趋势
            5. 商业价值实现
            6. 续约意向信号
            
            请提供：
            - 总体健康度评分
            - 各维度详细评分
            - 风险指标识别
            - 积极信号识别
            - 改进建议
            """
            
            # 检索健康度评估方法
            rag_result = await rag_service.query(
                question="客户健康度评估方法和指标体系",
                collection_name=self.knowledge_collections["success_methodology"]
            )
            
            enhanced_prompt = f"{health_prompt}\n\n评估方法：\n{rag_result.answer}"
            
            # 使用LLM生成健康度分析
            llm_response = await llm_service.chat_completion(
                messages=[{"role": "user", "content": enhanced_prompt}],
                temperature=0.2,
                max_tokens=2000
            )
            
            analysis_content = llm_response.get("content", "")
            
            # 解析分析结果
            overall_score = self._extract_overall_score(analysis_content)
            status = self._determine_health_status(overall_score)
            
            return HealthScore(
                customer_id=customer_id,
                overall_score=overall_score,
                status=status,
                factors=self._extract_factor_scores(analysis_content),
                risk_indicators=self._extract_list_items(analysis_content, "风险指标"),
                positive_signals=self._extract_list_items(analysis_content, "积极信号"),
                recommendations=self._extract_list_items(analysis_content, "改进建议"),
                last_updated=datetime.now(),
                trend=self._determine_trend(usage_data)
            )
            
        except Exception as e:
            logger.error(f"客户健康度监控失败: {e}")
            raise
    
    async def develop_renewal_strategy(self, customer_id: str) -> RenewalStrategy:
        """
        制定续约策略
        """
        try:
            # 获取客户信息和合同信息
            async with get_db() as db:
                customer_service = CustomerService(db)
                customer = await customer_service.get_customer(customer_id)
                
                if not customer:
                    raise ValueError(f"客户不存在: {customer_id}")
            
            # 获取健康度评分
            health_score = await self.monitor_health_score(customer_id)
            
            # 获取历史续约数据
            renewal_history = await self._get_renewal_history(customer_id)
            
            # 构建续约策略提示
            strategy_prompt = f"""
            作为客户成功专家，请为以下客户制定续约策略：
            
            客户信息：
            - 客户ID：{customer_id}
            - 公司：{customer.company}
            - 行业：{customer.industry}
            - 当前健康度：{health_score.overall_score}分（{health_score.status.value}）
            
            健康度分析：
            - 风险指标：{health_score.risk_indicators}
            - 积极信号：{health_score.positive_signals}
            
            续约历史：{json.dumps(renewal_history, ensure_ascii=False, indent=2)}
            
            请制定包含以下内容的续约策略：
            1. 续约概率评估
            2. 当前续约阶段判断
            3. 关键利益相关者识别
            4. 价值主张设计
            5. 定价策略建议
            6. 时间节点规划
            7. 成功因素分析
            8. 风险因素识别
            9. 具体行动计划
            """
            
            # 检索续约最佳实践
            rag_result = await rag_service.query(
                question=f"{customer.industry}行业客户续约策略和最佳实践",
                collection_name=self.knowledge_collections["renewal_strategies"]
            )
            
            enhanced_prompt = f"{strategy_prompt}\n\n最佳实践：\n{rag_result.answer}"
            
            # 生成续约策略
            llm_response = await llm_service.chat_completion(
                messages=[{"role": "user", "content": enhanced_prompt}],
                temperature=0.3,
                max_tokens=2000
            )
            
            content = llm_response.get("content", "")
            
            return RenewalStrategy(
                customer_id=customer_id,
                contract_end_date=self._get_contract_end_date(customer_id),
                renewal_probability=self._extract_renewal_probability(content),
                current_stage=self._extract_renewal_stage(content),
                key_stakeholders=self._extract_stakeholders(content),
                value_proposition=self._extract_section(content, "价值主张"),
                pricing_strategy=self._extract_section(content, "定价策略"),
                timeline=self._extract_timeline(content),
                success_factors=self._extract_list_items(content, "成功因素"),
                risks=self._extract_list_items(content, "风险因素"),
                action_plan=self._extract_action_plan(content)
            )
            
        except Exception as e:
            logger.error(f"续约策略制定失败: {e}")
            raise
    
    async def identify_expansion_opportunities(self, customer_id: str) -> List[ExpansionOpportunity]:
        """
        识别扩展机会
        """
        try:
            # 获取客户信息
            async with get_db() as db:
                customer_service = CustomerService(db)
                customer = await customer_service.get_customer(customer_id)
                
                if not customer:
                    raise ValueError(f"客户不存在: {customer_id}")
            
            # 获取客户使用数据和需求分析
            usage_data = await self._get_customer_usage_data(customer_id)
            feature_adoption = await self._get_feature_adoption_data(customer_id)
            business_growth = await self._get_business_growth_data(customer_id)
            
            # 构建扩展机会识别提示
            expansion_prompt = f"""
            作为客户成功专家，请识别以下客户的扩展机会：
            
            客户信息：
            - 客户ID：{customer_id}
            - 公司：{customer.company}
            - 行业：{customer.industry}
            - 规模：{customer.size}
            
            使用数据：{json.dumps(usage_data, ensure_ascii=False, indent=2)}
            功能采用：{json.dumps(feature_adoption, ensure_ascii=False, indent=2)}
            业务增长：{json.dumps(business_growth, ensure_ascii=False, indent=2)}
            
            请识别以下类型的扩展机会：
            1. 升级销售（Upsell）- 更高版本或更多功能
            2. 交叉销售（Cross-sell）- 相关产品或服务
            3. 席位扩展（Seat Expansion）- 更多用户许可
            4. 功能升级（Feature Upgrade）- 高级功能模块
            
            对每个机会请提供：
            - 机会类型和描述
            - 潜在价值评估
            - 成功概率
            - 实施时间线
            - 业务需求分析
            - 关键利益相关者
            - 实施计划
            - 成功指标
            """
            
            # 检索扩展机会识别方法
            rag_result = await rag_service.query(
                question="客户扩展机会识别和评估方法",
                collection_name=self.knowledge_collections["expansion_playbooks"]
            )
            
            enhanced_prompt = f"{expansion_prompt}\n\n识别方法：\n{rag_result.answer}"
            
            # 生成扩展机会分析
            llm_response = await llm_service.chat_completion(
                messages=[{"role": "user", "content": enhanced_prompt}],
                temperature=0.3,
                max_tokens=2000
            )
            
            content = llm_response.get("content", "")
            
            # 解析扩展机会
            opportunities = self._parse_expansion_opportunities(content, customer_id)
            
            return opportunities
            
        except Exception as e:
            logger.error(f"扩展机会识别失败: {e}")
            raise
    
    async def analyze_value_realization(self, customer_id: str, analysis_period: str = "last_quarter") -> ValueRealization:
        """
        分析客户价值实现
        """
        try:
            # 获取客户信息
            async with get_db() as db:
                customer_service = CustomerService(db)
                customer = await customer_service.get_customer(customer_id)
                
                if not customer:
                    raise ValueError(f"客户不存在: {customer_id}")
            
            # 获取价值相关数据
            usage_metrics = await self._get_customer_usage_metrics(customer_id, analysis_period)
            business_outcomes = await self._get_business_outcomes(customer_id, analysis_period)
            roi_data = await self._get_roi_data(customer_id, analysis_period)
            
            # 构建价值分析提示
            value_prompt = f"""
            作为客户成功专家，请分析以下客户的价值实现情况：
            
            客户信息：
            - 客户ID：{customer_id}
            - 公司：{customer.company}
            - 行业：{customer.industry}
            - 分析周期：{analysis_period}
            
            使用指标：{json.dumps(usage_metrics, ensure_ascii=False, indent=2)}
            业务成果：{json.dumps(business_outcomes, ensure_ascii=False, indent=2)}
            ROI数据：{json.dumps(roi_data, ensure_ascii=False, indent=2)}
            
            请分析：
            1. 已实现价值评估
            2. 潜在价值识别
            3. 价值差距分析
            4. 价值驱动因素
            5. 实现障碍识别
            6. 改进机会
            7. ROI指标计算
            8. 成功案例总结
            
            请提供量化的价值分析和具体的改进建议。
            """
            
            # 检索价值框架
            rag_result = await rag_service.query(
                question="客户价值实现分析框架和方法",
                collection_name=self.knowledge_collections["value_frameworks"]
            )
            
            enhanced_prompt = f"{value_prompt}\n\n价值框架：\n{rag_result.answer}"
            
            # 生成价值分析
            llm_response = await llm_service.chat_completion(
                messages=[{"role": "user", "content": enhanced_prompt}],
                temperature=0.2,
                max_tokens=2000
            )
            
            content = llm_response.get("content", "")
            
            return ValueRealization(
                customer_id=customer_id,
                realized_value=self._extract_realized_value(content),
                potential_value=self._extract_potential_value(content),
                value_gap=self._calculate_value_gap(content),
                value_drivers=self._extract_list_items(content, "价值驱动因素"),
                barriers=self._extract_list_items(content, "实现障碍"),
                improvement_opportunities=self._extract_list_items(content, "改进机会"),
                roi_metrics=self._extract_roi_metrics(content),
                success_stories=self._extract_list_items(content, "成功案例")
            )
            
        except Exception as e:
            logger.error(f"价值实现分析失败: {e}")
            raise  
  
    # MCP工具处理方法
    
    async def _handle_get_usage_data(self, customer_id: str, time_range: str = "last_month") -> Dict[str, Any]:
        """处理获取使用数据的MCP调用"""
        try:
            usage_data = await self._get_customer_usage_data(customer_id, time_range)
            return {
                "success": True,
                "customer_id": customer_id,
                "time_range": time_range,
                "usage_data": usage_data
            }
                    
        except Exception as e:
            logger.error(f"获取使用数据失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _handle_get_support_tickets(self, customer_id: str, time_range: str = "last_month") -> Dict[str, Any]:
        """处理获取支持工单的MCP调用"""
        try:
            support_data = await self._get_customer_support_data(customer_id, time_range)
            return {
                "success": True,
                "customer_id": customer_id,
                "support_tickets": support_data
            }
                    
        except Exception as e:
            logger.error(f"获取支持工单失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _handle_get_satisfaction_scores(self, customer_id: str, time_range: str = "last_quarter") -> Dict[str, Any]:
        """处理获取满意度评分的MCP调用"""
        try:
            satisfaction_data = await self._get_customer_satisfaction_data(customer_id, time_range)
            return {
                "success": True,
                "customer_id": customer_id,
                "satisfaction_scores": satisfaction_data
            }
                    
        except Exception as e:
            logger.error(f"获取满意度评分失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _handle_create_health_alert(self, customer_id: str, alert_type: str, message: str) -> Dict[str, Any]:
        """处理创建健康度预警的MCP调用"""
        try:
            alert_id = f"alert_{int(datetime.now().timestamp())}"
            return {
                "success": True,
                "alert_id": alert_id,
                "customer_id": customer_id,
                "alert_type": alert_type,
                "message": f"健康度预警已创建：{message}"
            }
                    
        except Exception as e:
            logger.error(f"创建健康度预警失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _handle_schedule_check_in(self, customer_id: str, check_in_type: str, schedule: str) -> Dict[str, Any]:
        """处理安排客户检查的MCP调用"""
        try:
            return {
                "success": True,
                "customer_id": customer_id,
                "check_in_type": check_in_type,
                "schedule": schedule,
                "message": f"已安排{check_in_type}检查，时间：{schedule}"
            }
                    
        except Exception as e:
            logger.error(f"安排客户检查失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _handle_update_renewal_status(self, customer_id: str, status: str, notes: str = "") -> Dict[str, Any]:
        """处理更新续约状态的MCP调用"""
        try:
            return {
                "success": True,
                "customer_id": customer_id,
                "renewal_status": status,
                "notes": notes,
                "updated_at": datetime.now().isoformat(),
                "message": f"续约状态已更新为：{status}"
            }
                    
        except Exception as e:
            logger.error(f"更新续约状态失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _handle_track_expansion_opportunity(self, customer_id: str, opportunity_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理跟踪扩展机会的MCP调用"""
        try:
            opportunity_id = f"expansion_{int(datetime.now().timestamp())}"
            return {
                "success": True,
                "opportunity_id": opportunity_id,
                "customer_id": customer_id,
                "opportunity_data": opportunity_data,
                "message": "扩展机会跟踪已创建"
            }
                    
        except Exception as e:
            logger.error(f"跟踪扩展机会失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    # 辅助方法
    
    def _extract_customer_id_from_message(self, content: str) -> Optional[str]:
        """从消息中提取客户ID"""
        import re
        patterns = [
            r'客户\s*(\w+)',
            r'客户ID\s*[：:]\s*(\w+)',
            r'ID\s*[：:]\s*(\w+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_data_types_from_message(self, content: str) -> List[str]:
        """从消息中提取数据类型"""
        data_types = []
        content_lower = content.lower()
        
        if any(keyword in content_lower for keyword in ["使用", "活跃", "登录"]):
            data_types.append("usage")
        if any(keyword in content_lower for keyword in ["功能", "特性", "模块"]):
            data_types.append("features")
        if any(keyword in content_lower for keyword in ["支持", "工单", "问题"]):
            data_types.append("support")
        if any(keyword in content_lower for keyword in ["满意度", "评分", "反馈"]):
            data_types.append("satisfaction")
        
        return data_types if data_types else ["usage", "features", "support"]
    
    async def _get_customer_usage_data(self, customer_id: str, time_range: str = "last_month", data_types: List[str] = None) -> Dict[str, Any]:
        """获取客户使用数据"""
        # 简化实现，返回模拟数据
        return {
            "customer_id": customer_id,
            "time_range": time_range,
            "login_frequency": 25,  # 每月登录次数
            "session_duration": 45,  # 平均会话时长（分钟）
            "feature_usage": {
                "core_features": 0.85,  # 核心功能使用率
                "advanced_features": 0.35,  # 高级功能使用率
                "new_features": 0.15  # 新功能采用率
            },
            "user_activity": {
                "active_users": 12,
                "total_users": 15,
                "activity_trend": "stable"
            }
        }
    
    async def _get_customer_support_data(self, customer_id: str, time_range: str = "last_month") -> Dict[str, Any]:
        """获取客户支持数据"""
        # 简化实现
        return {
            "customer_id": customer_id,
            "time_range": time_range,
            "ticket_count": 3,
            "avg_resolution_time": 24,  # 小时
            "ticket_types": {
                "technical": 2,
                "billing": 0,
                "feature_request": 1
            },
            "satisfaction_rating": 4.2
        }
    
    async def _get_customer_satisfaction_data(self, customer_id: str, time_range: str = "last_quarter") -> Dict[str, Any]:
        """获取客户满意度数据"""
        # 简化实现
        return {
            "customer_id": customer_id,
            "time_range": time_range,
            "overall_satisfaction": 4.3,
            "nps_score": 8,
            "csat_scores": [4.5, 4.2, 4.1, 4.3],
            "feedback_themes": ["产品稳定", "功能丰富", "支持及时"]
        }
    
    async def _get_renewal_history(self, customer_id: str) -> Dict[str, Any]:
        """获取续约历史"""
        # 简化实现
        return {
            "customer_id": customer_id,
            "renewal_count": 2,
            "last_renewal_date": "2023-12-01",
            "contract_value_trend": [100000, 120000, 150000],
            "renewal_success_rate": 1.0
        }
    
    async def _get_feature_adoption_data(self, customer_id: str) -> Dict[str, Any]:
        """获取功能采用数据"""
        # 简化实现
        return {
            "customer_id": customer_id,
            "adopted_features": ["基础CRM", "销售漏斗", "报表分析"],
            "available_features": ["基础CRM", "销售漏斗", "报表分析", "营销自动化", "客服集成"],
            "adoption_rate": 0.6,
            "time_to_adoption": {"基础CRM": 7, "销售漏斗": 14, "报表分析": 30}
        }
    
    async def _get_business_growth_data(self, customer_id: str) -> Dict[str, Any]:
        """获取业务增长数据"""
        # 简化实现
        return {
            "customer_id": customer_id,
            "revenue_growth": 0.25,
            "team_size_growth": 0.20,
            "market_expansion": ["华南地区"],
            "new_business_lines": ["电商业务"]
        }
    
    async def _get_customer_usage_metrics(self, customer_id: str, period: str) -> Dict[str, Any]:
        """获取客户使用指标"""
        # 简化实现
        return {
            "customer_id": customer_id,
            "period": period,
            "total_sessions": 180,
            "total_duration": 8100,  # 分钟
            "feature_utilization": 0.65,
            "data_volume": 50000  # 记录数
        }
    
    async def _get_business_outcomes(self, customer_id: str, period: str) -> Dict[str, Any]:
        """获取业务成果"""
        # 简化实现
        return {
            "customer_id": customer_id,
            "period": period,
            "efficiency_improvement": 0.30,
            "cost_savings": 50000,
            "revenue_increase": 200000,
            "process_optimization": ["销售流程", "客户服务"]
        }
    
    async def _get_roi_data(self, customer_id: str, period: str) -> Dict[str, Any]:
        """获取ROI数据"""
        # 简化实现
        return {
            "customer_id": customer_id,
            "period": period,
            "investment": 150000,
            "returns": 250000,
            "roi_percentage": 0.67,
            "payback_period": 8  # 月
        }
    
    def _get_contract_end_date(self, customer_id: str) -> datetime:
        """获取合同结束日期"""
        # 简化实现
        return datetime.now() + timedelta(days=90)
    
    # 数据提取方法
    
    def _extract_overall_score(self, content: str) -> float:
        """提取总体评分"""
        import re
        # 查找评分模式
        patterns = [
            r'总体.*?(\d+\.?\d*)分',
            r'整体.*?(\d+\.?\d*)分',
            r'健康度.*?(\d+\.?\d*)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                return float(match.group(1))
        
        return 75.0  # 默认值
    
    def _determine_health_status(self, score: float) -> HealthStatus:
        """确定健康状态"""
        if score >= 80:
            return HealthStatus.HEALTHY
        elif score >= 60:
            return HealthStatus.AT_RISK
        elif score >= 40:
            return HealthStatus.CRITICAL
        else:
            return HealthStatus.CHURNED
    
    def _extract_factor_scores(self, content: str) -> Dict[str, float]:
        """提取各因子评分"""
        # 简化实现
        return {
            "usage_activity": 78.0,
            "feature_adoption": 65.0,
            "support_health": 85.0,
            "satisfaction": 82.0,
            "business_value": 70.0
        }
    
    def _determine_trend(self, usage_data: Dict[str, Any]) -> str:
        """确定趋势"""
        activity_trend = usage_data.get("user_activity", {}).get("activity_trend", "stable")
        return activity_trend
    
    def _extract_renewal_probability(self, content: str) -> float:
        """提取续约概率"""
        import re
        patterns = [
            r'续约概率.*?(\d+\.?\d*)%',
            r'成功率.*?(\d+\.?\d*)%',
            r'概率.*?(\d+\.?\d*)%'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                return float(match.group(1)) / 100
        
        return 0.75  # 默认值
    
    def _extract_renewal_stage(self, content: str) -> RenewalStage:
        """提取续约阶段"""
        content_lower = content.lower()
        
        if any(keyword in content_lower for keyword in ["早期", "初期", "开始"]):
            return RenewalStage.EARLY_ENGAGEMENT
        elif any(keyword in content_lower for keyword in ["需求", "评估"]):
            return RenewalStage.NEEDS_ASSESSMENT
        elif any(keyword in content_lower for keyword in ["方案", "提议"]):
            return RenewalStage.PROPOSAL
        elif any(keyword in content_lower for keyword in ["谈判", "商务"]):
            return RenewalStage.NEGOTIATION
        else:
            return RenewalStage.CONTRACT_RENEWAL
    
    def _extract_stakeholders(self, content: str) -> List[Dict[str, Any]]:
        """提取利益相关者"""
        # 简化实现
        return [
            {"name": "张总", "role": "决策者", "influence": "high"},
            {"name": "李经理", "role": "使用者", "influence": "medium"},
            {"name": "王主管", "role": "技术负责人", "influence": "medium"}
        ]
    
    def _extract_timeline(self, content: str) -> Dict[str, datetime]:
        """提取时间线"""
        # 简化实现
        now = datetime.now()
        return {
            "initial_contact": now + timedelta(days=7),
            "needs_review": now + timedelta(days=21),
            "proposal_delivery": now + timedelta(days=35),
            "contract_signing": now + timedelta(days=60)
        }
    
    def _extract_action_plan(self, content: str) -> List[Dict[str, Any]]:
        """提取行动计划"""
        # 简化实现
        return [
            {
                "action": "安排高层会议",
                "timeline": "1周内",
                "owner": "客户成功经理",
                "priority": "high"
            },
            {
                "action": "准备价值展示材料",
                "timeline": "2周内",
                "owner": "产品专家",
                "priority": "medium"
            }
        ]
    
    def _parse_expansion_opportunities(self, content: str, customer_id: str) -> List[ExpansionOpportunity]:
        """解析扩展机会"""
        # 简化实现
        opportunities = []
        
        # 模拟解析结果
        opportunity_types = [ExpansionType.UPSELL, ExpansionType.CROSS_SELL, ExpansionType.SEAT_EXPANSION]
        
        for i, opp_type in enumerate(opportunity_types):
            opportunity = ExpansionOpportunity(
                customer_id=customer_id,
                opportunity_type=opp_type,
                potential_value=50000 + i * 20000,
                probability=0.6 + i * 0.1,
                timeline=f"{(i+1)*2}个月",
                requirements=[f"需求{i+1}", f"条件{i+1}"],
                business_case=f"{opp_type.value}业务案例",
                stakeholders=["张总", "李经理"],
                implementation_plan=f"{opp_type.value}实施计划",
                success_metrics=[f"指标{i+1}"],
                identified_date=datetime.now()
            )
            opportunities.append(opportunity)
        
        return opportunities
    
    def _extract_realized_value(self, content: str) -> float:
        """提取已实现价值"""
        import re
        patterns = [
            r'已实现.*?(\d+\.?\d*)万',
            r'实现价值.*?(\d+\.?\d*)万'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                return float(match.group(1)) * 10000
        
        return 200000.0  # 默认值
    
    def _extract_potential_value(self, content: str) -> float:
        """提取潜在价值"""
        import re
        patterns = [
            r'潜在.*?(\d+\.?\d*)万',
            r'可实现.*?(\d+\.?\d*)万'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                return float(match.group(1)) * 10000
        
        return 350000.0  # 默认值
    
    def _calculate_value_gap(self, content: str) -> float:
        """计算价值差距"""
        realized = self._extract_realized_value(content)
        potential = self._extract_potential_value(content)
        return potential - realized
    
    def _extract_roi_metrics(self, content: str) -> Dict[str, float]:
        """提取ROI指标"""
        # 简化实现
        return {
            "roi_percentage": 0.67,
            "payback_months": 8,
            "net_present_value": 100000,
            "internal_rate_of_return": 0.25
        }
    
    def _extract_list_items(self, content: str, section_name: str) -> List[str]:
        """从内容中提取列表项"""
        # 简化实现，实际应该用更复杂的文本解析
        items = []
        lines = content.split('\n')
        in_section = False
        
        for line in lines:
            if section_name in line:
                in_section = True
                continue
            elif in_section and line.strip().startswith('-'):
                items.append(line.strip()[1:].strip())
            elif in_section and line.strip() and not line.strip().startswith('-'):
                break
        
        return items[:5]  # 最多返回5个项目
    
    def _extract_section(self, content: str, section_name: str) -> str:
        """提取特定章节内容"""
        # 简化实现
        lines = content.split('\n')
        section_content = []
        in_section = False
        
        for line in lines:
            if section_name in line:
                in_section = True
                continue
            elif in_section:
                if line.strip() and not line.startswith('#'):
                    section_content.append(line.strip())
                elif line.startswith('#'):
                    break
        
        return '\n'.join(section_content[:3])  # 返回前3行    
 
   # 响应格式化方法
    
    async def _format_health_monitoring_response(self, data: HealthScore) -> tuple[str, List[str]]:
        """格式化健康度监控响应"""
        status_emoji = {
            HealthStatus.HEALTHY: "🟢",
            HealthStatus.AT_RISK: "🟡", 
            HealthStatus.CRITICAL: "🔴",
            HealthStatus.CHURNED: "⚫"
        }
        
        content = f"""## 客户健康度报告

**客户ID**: {data.customer_id}
**整体评分**: {data.overall_score:.1f}分
**健康状态**: {status_emoji.get(data.status, "🔵")} {data.status.value}
**趋势**: {data.trend}
**更新时间**: {data.last_updated.strftime('%Y-%m-%d %H:%M')}

### 各维度评分
"""
        
        for factor, score in data.factors.items():
            content += f"- **{factor}**: {score:.1f}分\n"
        
        content += f"""
### 风险指标 🚨
"""
        for risk in data.risk_indicators:
            content += f"- {risk}\n"
        
        content += f"""
### 积极信号 ✅
"""
        for signal in data.positive_signals:
            content += f"- {signal}\n"
        
        content += f"""
### 改进建议
"""
        for recommendation in data.recommendations:
            content += f"- {recommendation}\n"
        
        suggestions = [
            "创建健康度预警",
            "安排客户检查",
            "制定改进计划",
            "联系客户团队"
        ]
        
        return content, suggestions
    
    async def _format_renewal_strategy_response(self, data: RenewalStrategy) -> tuple[str, List[str]]:
        """格式化续约策略响应"""
        content = f"""## 续约策略方案

**客户ID**: {data.customer_id}
**合同到期**: {data.contract_end_date.strftime('%Y-%m-%d')}
**续约概率**: {data.renewal_probability:.1%}
**当前阶段**: {data.current_stage.value}

### 价值主张
{data.value_proposition}

### 定价策略
{data.pricing_strategy}

### 关键利益相关者
"""
        
        for stakeholder in data.key_stakeholders:
            content += f"- **{stakeholder.get('name', '未知')}** ({stakeholder.get('role', '未知角色')}) - 影响力: {stakeholder.get('influence', '未知')}\n"
        
        content += f"""
### 成功因素
"""
        for factor in data.success_factors:
            content += f"- {factor}\n"
        
        content += f"""
### 风险因素
"""
        for risk in data.risks:
            content += f"- {risk}\n"
        
        content += f"""
### 行动计划
"""
        for action in data.action_plan:
            content += f"- **{action.get('action', '未知行动')}** (时间: {action.get('timeline', '未定')}, 负责人: {action.get('owner', '未定')})\n"
        
        suggestions = [
            "开始执行行动计划",
            "安排利益相关者会议",
            "准备续约提案",
            "更新续约状态"
        ]
        
        return content, suggestions
    
    async def _format_expansion_opportunities_response(self, data: List[ExpansionOpportunity]) -> tuple[str, List[str]]:
        """格式化扩展机会响应"""
        content = f"""## 扩展机会分析

**识别时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}
**机会数量**: {len(data)}个

"""
        
        for i, opportunity in enumerate(data, 1):
            type_emoji = {
                ExpansionType.UPSELL: "⬆️",
                ExpansionType.CROSS_SELL: "↔️",
                ExpansionType.SEAT_EXPANSION: "👥",
                ExpansionType.FEATURE_UPGRADE: "🔧"
            }
            
            content += f"""### 机会 {i}: {type_emoji.get(opportunity.opportunity_type, "📈")} {opportunity.opportunity_type.value}

**潜在价值**: ¥{opportunity.potential_value:,.0f}
**成功概率**: {opportunity.probability:.1%}
**预计时间**: {opportunity.timeline}

**业务需求**:
{opportunity.business_case}

**关键利益相关者**: {', '.join(opportunity.stakeholders)}

**成功指标**:
"""
            for metric in opportunity.success_metrics:
                content += f"- {metric}\n"
            
            content += "\n"
        
        total_value = sum(opp.potential_value for opp in data)
        content += f"""
### 总结
**总潜在价值**: ¥{total_value:,.0f}
**平均成功概率**: {sum(opp.probability for opp in data) / len(data):.1%}
"""
        
        suggestions = [
            "优先推进高价值机会",
            "制定扩展销售计划",
            "联系相关利益相关者",
            "跟踪机会进展"
        ]
        
        return content, suggestions
    
    async def _format_value_analysis_response(self, data: ValueRealization) -> tuple[str, List[str]]:
        """格式化价值分析响应"""
        content = f"""## 客户价值实现分析

**客户ID**: {data.customer_id}
**已实现价值**: ¥{data.realized_value:,.0f}
**潜在价值**: ¥{data.potential_value:,.0f}
**价值差距**: ¥{data.value_gap:,.0f}

### ROI指标
"""
        
        for metric, value in data.roi_metrics.items():
            if isinstance(value, float) and value < 1:
                content += f"- **{metric}**: {value:.1%}\n"
            else:
                content += f"- **{metric}**: {value}\n"
        
        content += f"""
### 价值驱动因素
"""
        for driver in data.value_drivers:
            content += f"- {driver}\n"
        
        content += f"""
### 实现障碍
"""
        for barrier in data.barriers:
            content += f"- {barrier}\n"
        
        content += f"""
### 改进机会
"""
        for opportunity in data.improvement_opportunities:
            content += f"- {opportunity}\n"
        
        content += f"""
### 成功案例
"""
        for story in data.success_stories:
            content += f"- {story}\n"
        
        suggestions = [
            "制定价值提升计划",
            "消除实现障碍",
            "推广成功经验",
            "设置价值监控"
        ]
        
        return content, suggestions
    
    async def _format_customer_data_response(self, data: Dict[str, Any]) -> tuple[str, List[str]]:
        """格式化客户数据响应"""
        content = f"""## 客户使用数据分析

**客户ID**: {data.get('customer_id', '未知')}
**数据周期**: {data.get('time_range', '未知')}

### 使用活跃度
- **登录频率**: {data.get('login_frequency', 0)}次/月
- **平均会话时长**: {data.get('session_duration', 0)}分钟
- **活跃用户**: {data.get('user_activity', {}).get('active_users', 0)}/{data.get('user_activity', {}).get('total_users', 0)}

### 功能使用情况
"""
        
        feature_usage = data.get('feature_usage', {})
        for feature, usage_rate in feature_usage.items():
            content += f"- **{feature}**: {usage_rate:.1%}\n"
        
        content += f"""
### 活跃度趋势
**趋势**: {data.get('user_activity', {}).get('activity_trend', '未知')}
"""
        
        suggestions = [
            "分析使用模式",
            "提升功能采用率",
            "优化用户体验",
            "制定培训计划"
        ]
        
        return content, suggestions
    
    async def _format_knowledge_based_response(self, data: Dict[str, Any]) -> tuple[str, List[str]]:
        """格式化知识库响应"""
        content = f"""## 客户成功知识解答

{data.get('answer', '暂无相关信息')}

### 参考来源
"""
        
        sources = data.get('sources', [])
        for source in sources[:3]:  # 只显示前3个来源
            content += f"- {source.get('title', '未知来源')}\n"
        
        suggestions = [
            "查看更多相关资料",
            "咨询客户成功专家",
            "制定具体行动计划",
            "分享给团队成员"
        ]
        
        return content, suggestions
    
    async def _format_general_response(self, data: Dict[str, Any]) -> tuple[str, List[str]]:
        """格式化一般响应"""
        content = "我已经处理了您的客户成功请求。"
        
        if isinstance(data, dict) and data:
            content += f"\n\n处理结果：\n{json.dumps(data, ensure_ascii=False, indent=2)}"
        
        suggestions = [
            "查看详细分析",
            "制定行动计划",
            "安排客户会议",
            "设置跟进提醒"
        ]
        
        return content, suggestions
    
    async def _integrate_collaboration_result(self, collaboration_result: Dict[str, Any]) -> str:
        """整合协作结果"""
        results = collaboration_result.get("collaboration_results", [])
        if not results:
            return ""
        
        content = "### 协作分析结果\n"
        for result in results:
            agent_id = result.get("agent_id", "未知Agent")
            if "error" not in result:
                content += f"- **{agent_id}**: 提供了相关专业建议\n"
            else:
                content += f"- **{agent_id}**: 暂时无法提供建议\n"
        
        return content
    
    def _calculate_response_confidence(self, task_result: Dict[str, Any], collaboration_result: Optional[Dict[str, Any]]) -> float:
        """计算响应置信度"""
        base_confidence = 0.8
        
        # 根据任务执行结果调整
        if task_result.get("success"):
            base_confidence += 0.1
        
        # 根据协作结果调整
        if collaboration_result and collaboration_result.get("success"):
            base_confidence += 0.05
        
        return min(base_confidence, 1.0)
    
    def _generate_next_actions(self, task_result: Dict[str, Any]) -> List[str]:
        """生成下一步行动建议"""
        response_type = task_result.get("response_type", "general")
        
        if response_type == "health_monitoring":
            return ["创建预警提醒", "安排客户检查", "制定改进计划"]
        elif response_type == "renewal_strategy":
            return ["执行续约计划", "联系关键决策者", "准备续约材料"]
        elif response_type == "expansion_opportunities":
            return ["评估机会优先级", "制定销售计划", "联系相关团队"]
        elif response_type == "value_analysis":
            return ["制定价值提升计划", "消除实现障碍", "设置监控指标"]
        else:
            return ["制定行动计划", "安排跟进会议", "设置提醒"]
    
    # 指导方法
    
    async def _get_health_monitoring_guidance(self, content: str) -> Dict[str, Any]:
        """获取健康度监控指导"""
        rag_result = await rag_service.query(
            question=f"客户健康度监控方法和指标：{content}",
            collection_name=self.knowledge_collections["success_methodology"]
        )
        
        return {
            "guidance": rag_result.answer,
            "sources": rag_result.sources,
            "confidence": rag_result.confidence
        }
    
    async def _get_renewal_strategy_guidance(self, content: str) -> Dict[str, Any]:
        """获取续约策略指导"""
        rag_result = await rag_service.query(
            question=f"客户续约策略制定方法：{content}",
            collection_name=self.knowledge_collections["renewal_strategies"]
        )
        
        return {
            "guidance": rag_result.answer,
            "sources": rag_result.sources,
            "confidence": rag_result.confidence
        }
    
    async def _get_expansion_identification_guidance(self, content: str) -> Dict[str, Any]:
        """获取扩展机会识别指导"""
        rag_result = await rag_service.query(
            question=f"客户扩展机会识别方法：{content}",
            collection_name=self.knowledge_collections["expansion_playbooks"]
        )
        
        return {
            "guidance": rag_result.answer,
            "sources": rag_result.sources,
            "confidence": rag_result.confidence
        }
    
    async def _get_value_analysis_guidance(self, content: str) -> Dict[str, Any]:
        """获取价值分析指导"""
        rag_result = await rag_service.query(
            question=f"客户价值实现分析方法：{content}",
            collection_name=self.knowledge_collections["value_frameworks"]
        )
        
        return {
            "guidance": rag_result.answer,
            "sources": rag_result.sources,
            "confidence": rag_result.confidence
        }
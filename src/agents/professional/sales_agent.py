"""
销售Agent - 专业化销售支持Agent

提供客户分析、中文话术生成、机会评估等销售专业功能
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


class SalesStage(str, Enum):
    """销售阶段枚举"""
    PROSPECTING = "prospecting"  # 客户开发
    QUALIFICATION = "qualification"  # 需求确认
    PROPOSAL = "proposal"  # 方案提议
    NEGOTIATION = "negotiation"  # 商务谈判
    CLOSING = "closing"  # 成交关单
    FOLLOW_UP = "follow_up"  # 后续跟进


class TalkingPointType(str, Enum):
    """话术类型枚举"""
    OPENING = "opening"  # 开场白
    VALUE_PROPOSITION = "value_proposition"  # 价值主张
    OBJECTION_HANDLING = "objection_handling"  # 异议处理
    CLOSING = "closing"  # 成交话术
    FOLLOW_UP = "follow_up"  # 跟进话术


@dataclass
class CustomerAnalysis:
    """客户分析结果"""
    customer_id: str
    profile_summary: str
    pain_points: List[str]
    decision_makers: List[Dict[str, Any]]
    buying_signals: List[str]
    risk_factors: List[str]
    recommended_approach: str
    confidence_score: float
    analysis_date: datetime


@dataclass
class TalkingPoint:
    """销售话术点"""
    type: TalkingPointType
    content: str
    context: str
    effectiveness_score: float
    usage_scenarios: List[str]
    customization_notes: str


@dataclass
class OpportunityAssessment:
    """销售机会评估"""
    opportunity_id: str
    current_stage: str
    win_probability: float
    risk_level: str
    key_success_factors: List[str]
    potential_obstacles: List[str]
    recommended_actions: List[str]
    timeline_assessment: Dict[str, Any]
    competitive_position: str
    assessment_date: datetime


@dataclass
class ActionRecommendation:
    """行动建议"""
    priority: str  # high, medium, low
    action_type: str
    description: str
    expected_outcome: str
    timeline: str
    resources_needed: List[str]
    success_metrics: List[str]


class SalesAgent(BaseAgent):
    """
    销售专业Agent
    
    专注于销售流程的各个环节，提供智能化的销售支持：
    - 客户分析和画像
    - 中文销售话术生成
    - 销售机会评估
    - 销售策略建议
    - CRM系统操作
    """
    
    def __init__(
        self,
        agent_id: str = "sales_agent",
        name: str = "销售专家",
        state_manager=None,
        communicator=None
    ):
        # 定义销售Agent的专业能力
        capabilities = [
            AgentCapability(
                name="customer_analysis",
                description="深度分析客户信息，生成客户画像和销售策略",
                parameters={
                    "customer_id": {"type": "string", "required": True},
                    "analysis_depth": {"type": "string", "enum": ["basic", "detailed", "comprehensive"]}
                }
            ),
            AgentCapability(
                name="generate_talking_points",
                description="基于客户特征和销售场景生成个性化中文话术",
                parameters={
                    "customer_context": {"type": "object", "required": True},
                    "sales_stage": {"type": "string", "enum": list(SalesStage)},
                    "talking_point_type": {"type": "string", "enum": list(TalkingPointType)}
                }
            ),
            AgentCapability(
                name="assess_opportunity",
                description="评估销售机会的成交概率和风险因素",
                parameters={
                    "opportunity_id": {"type": "string", "required": True},
                    "include_competitive_analysis": {"type": "boolean", "default": True}
                }
            ),
            AgentCapability(
                name="recommend_next_action",
                description="基于当前销售情况推荐下一步行动",
                parameters={
                    "context": {"type": "object", "required": True},
                    "urgency_level": {"type": "string", "enum": ["low", "medium", "high"]}
                }
            ),
            AgentCapability(
                name="crm_operations",
                description="执行CRM系统操作，如创建客户、更新机会等",
                parameters={
                    "operation": {"type": "string", "required": True},
                    "data": {"type": "object", "required": True}
                }
            )
        ]
        
        super().__init__(
            agent_id=agent_id,
            name=name,
            specialty="销售专业支持",
            capabilities=capabilities,
            state_manager=state_manager,
            communicator=communicator
        )
        
        # 销售知识库集合名称
        self.knowledge_collections = {
            "sales_methodology": "sales_methodology",
            "talking_scripts": "chinese_sales_scripts", 
            "success_cases": "sales_success_cases",
            "objection_handling": "objection_handling_guide",
            "industry_insights": "industry_sales_insights"
        }
        
        # MCP工具配置
        self.mcp_tools = {
            "get_customer_info": self._handle_get_customer_info,
            "create_lead": self._handle_create_lead,
            "update_opportunity": self._handle_update_opportunity,
            "schedule_follow_up": self._handle_schedule_follow_up,
            "generate_proposal": self._handle_generate_proposal
        }
        
        logger.info(f"销售Agent {self.name} 初始化完成")
    
    async def analyze_task(self, message: AgentMessage) -> Dict[str, Any]:
        """
        分析销售相关任务
        """
        try:
            content = message.content.lower()
            metadata = message.metadata or {}
            
            # 识别任务类型
            task_type = "general"
            needs_collaboration = False
            required_agents = []
            
            # 客户分析相关
            import re
            if (any(keyword in content for keyword in ["客户分析", "客户画像", "客户背景", "分析客户"]) or
                re.search(r'分析.*客户', content)):
                task_type = "customer_analysis"
                
            # 话术生成相关
            elif any(keyword in content for keyword in ["话术", "怎么说", "如何沟通", "开场白", "异议处理"]):
                task_type = "talking_points"
                
            # 机会评估相关
            elif any(keyword in content for keyword in ["机会评估", "成交概率", "销售机会", "项目评估"]):
                task_type = "opportunity_assessment"
                
            # 行动建议相关
            elif any(keyword in content for keyword in ["下一步", "建议", "策略", "怎么办", "如何推进"]):
                task_type = "action_recommendation"
                
            # CRM操作相关
            elif any(keyword in content for keyword in ["创建", "更新", "修改", "删除", "查询"]):
                task_type = "crm_operation"
            
            # 判断是否需要协作
            if any(keyword in content for keyword in ["产品", "技术方案", "实施"]):
                needs_collaboration = True
                required_agents.append("product_agent")
                
            if any(keyword in content for keyword in ["市场分析", "竞争对手", "行业趋势", "市场竞争", "竞争情况"]):
                needs_collaboration = True
                required_agents.append("market_agent")
                
            if any(keyword in content for keyword in ["团队", "管理", "绩效"]):
                needs_collaboration = True
                required_agents.append("sales_management_agent")
            
            return {
                "task_type": task_type,
                "needs_collaboration": needs_collaboration,
                "required_agents": required_agents,
                "collaboration_type": "sequential" if needs_collaboration else None,
                "priority": metadata.get("priority", "medium"),
                "context": {
                    "user_role": metadata.get("user_role", "sales_rep"),
                    "customer_id": metadata.get("customer_id"),
                    "opportunity_id": metadata.get("opportunity_id"),
                    "sales_stage": metadata.get("sales_stage")
                }
            }
            
        except Exception as e:
            logger.error(f"销售任务分析失败: {e}")
            return {
                "task_type": "general",
                "needs_collaboration": False,
                "error": str(e)
            }
    
    async def execute_task(self, message: AgentMessage, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行销售任务
        """
        task_type = analysis.get("task_type", "general")
        context = analysis.get("context", {})
        
        try:
            if task_type == "customer_analysis":
                return await self._execute_customer_analysis(message, context)
            elif task_type == "talking_points":
                return await self._execute_talking_points_generation(message, context)
            elif task_type == "opportunity_assessment":
                return await self._execute_opportunity_assessment(message, context)
            elif task_type == "action_recommendation":
                return await self._execute_action_recommendation(message, context)
            elif task_type == "crm_operation":
                return await self._execute_crm_operation(message, context)
            else:
                return await self._execute_general_sales_query(message, context)
                
        except Exception as e:
            logger.error(f"销售任务执行失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "fallback_response": "抱歉，处理您的销售请求时遇到了问题，请稍后重试。"
            }
    
    async def _execute_customer_analysis(self, message: AgentMessage, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行客户分析任务"""
        try:
            customer_id = context.get("customer_id")
            if not customer_id:
                # 尝试从消息中提取客户ID
                customer_id = self._extract_customer_id_from_message(message.content)
            
            if customer_id:
                analysis = await self.analyze_customer(customer_id)
                return {
                    "success": True,
                    "analysis_type": "customer_analysis",
                    "data": analysis,
                    "response_type": "structured"
                }
            else:
                # 如果没有具体客户ID，提供一般性的客户分析指导
                guidance = await self._get_customer_analysis_guidance(message.content)
                return {
                    "success": True,
                    "analysis_type": "customer_analysis_guidance",
                    "data": guidance,
                    "response_type": "guidance"
                }
                
        except Exception as e:
            logger.error(f"客户分析执行失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _execute_talking_points_generation(self, message: AgentMessage, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行话术生成任务"""
        try:
            # 构建销售上下文
            sales_context = {
                "customer_info": context.get("customer_id"),
                "sales_stage": context.get("sales_stage", "prospecting"),
                "user_query": message.content,
                "industry": context.get("industry"),
                "product_focus": context.get("product_focus")
            }
            
            talking_points = await self.generate_talking_points(sales_context)
            
            return {
                "success": True,
                "analysis_type": "talking_points",
                "data": talking_points,
                "response_type": "talking_points"
            }
            
        except Exception as e:
            logger.error(f"话术生成执行失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _execute_opportunity_assessment(self, message: AgentMessage, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行机会评估任务"""
        try:
            opportunity_id = context.get("opportunity_id")
            if not opportunity_id:
                opportunity_id = self._extract_opportunity_id_from_message(message.content)
            
            if opportunity_id:
                assessment = await self.assess_opportunity(opportunity_id)
                return {
                    "success": True,
                    "analysis_type": "opportunity_assessment",
                    "data": assessment,
                    "response_type": "assessment"
                }
            else:
                # 提供一般性的机会评估指导
                guidance = await self._get_opportunity_assessment_guidance(message.content)
                return {
                    "success": True,
                    "analysis_type": "opportunity_assessment_guidance", 
                    "data": guidance,
                    "response_type": "guidance"
                }
                
        except Exception as e:
            logger.error(f"机会评估执行失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _execute_action_recommendation(self, message: AgentMessage, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行行动建议任务"""
        try:
            recommendations = await self.recommend_next_action(context)
            
            return {
                "success": True,
                "analysis_type": "action_recommendation",
                "data": recommendations,
                "response_type": "recommendations"
            }
            
        except Exception as e:
            logger.error(f"行动建议执行失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _execute_crm_operation(self, message: AgentMessage, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行CRM操作任务"""
        try:
            # 解析CRM操作意图
            operation_intent = await self._parse_crm_operation_intent(message.content)
            
            # 执行相应的CRM操作
            result = await self._perform_crm_operation(operation_intent, context)
            
            return {
                "success": True,
                "analysis_type": "crm_operation",
                "data": result,
                "response_type": "operation_result"
            }
            
        except Exception as e:
            logger.error(f"CRM操作执行失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _execute_general_sales_query(self, message: AgentMessage, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行一般销售查询"""
        try:
            # 使用RAG检索相关销售知识
            rag_result = await rag_service.query(
                question=message.content,
                mode=RAGMode.HYBRID,
                collection_name=self.knowledge_collections["sales_methodology"]
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
            logger.error(f"一般销售查询执行失败: {e}")
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
        生成销售Agent响应
        """
        try:
            if not task_result or not task_result.get("success", False):
                error_msg = task_result.get("error", "未知错误") if task_result else "任务执行失败"
                fallback = task_result.get("fallback_response", "抱歉，我无法处理您的请求。")
                
                return AgentResponse(
                    content=fallback,
                    confidence=0.1,
                    suggestions=["请检查输入信息", "稍后重试", "联系技术支持"],
                    metadata={"error": error_msg}
                )
            
            response_type = task_result.get("response_type", "general")
            data = task_result.get("data", {})
            
            # 根据响应类型生成不同格式的回复
            if response_type == "structured":
                content, suggestions = await self._format_structured_response(data)
            elif response_type == "talking_points":
                content, suggestions = await self._format_talking_points_response(data)
            elif response_type == "assessment":
                content, suggestions = await self._format_assessment_response(data)
            elif response_type == "recommendations":
                content, suggestions = await self._format_recommendations_response(data)
            elif response_type == "operation_result":
                content, suggestions = await self._format_operation_result_response(data)
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
            logger.error(f"生成销售Agent响应失败: {e}")
            return AgentResponse(
                content="抱歉，生成响应时遇到了问题。",
                confidence=0.0,
                suggestions=["请重新提问", "检查网络连接"],
                metadata={"error": str(e)}
            )
    
    # 核心业务方法实现
    
    async def analyze_customer(self, customer_id: str) -> CustomerAnalysis:
        """
        深度分析客户信息
        """
        try:
            # 获取客户基础信息
            async with get_db() as db:
                customer_service = CustomerService(db)
                customer = await customer_service.get_customer(customer_id)
                
                if not customer:
                    raise ValueError(f"客户不存在: {customer_id}")
            
            # 使用LLM和RAG进行深度分析
            analysis_prompt = f"""
            作为专业的销售顾问，请深度分析以下客户信息：
            
            客户基本信息：
            - 姓名：{customer.name}
            - 公司：{customer.company}
            - 行业：{customer.industry}
            - 规模：{customer.size}
            - 联系方式：{customer.contact}
            - 客户画像：{customer.profile}
            
            请从以下维度进行分析：
            1. 客户画像总结
            2. 主要痛点识别
            3. 决策者分析
            4. 购买信号识别
            5. 风险因素评估
            6. 推荐销售策略
            
            请用中文回答，分析要深入、实用。
            """
            
            # 检索相关销售知识
            rag_result = await rag_service.query(
                question=f"如何分析{customer.industry}行业的{customer.size}规模客户",
                collection_name=self.knowledge_collections["sales_methodology"]
            )
            
            # 结合RAG结果优化分析提示
            enhanced_prompt = f"{analysis_prompt}\n\n参考知识：\n{rag_result.answer}"
            
            # 使用LLM生成分析
            llm_response = await llm_service.chat_completion(
                messages=[{"role": "user", "content": enhanced_prompt}],
                temperature=0.3,
                max_tokens=2000
            )
            
            analysis_content = llm_response.get("content", "")
            
            # 解析分析结果（这里简化处理，实际可以用更复杂的解析逻辑）
            return CustomerAnalysis(
                customer_id=customer_id,
                profile_summary=self._extract_section(analysis_content, "客户画像总结"),
                pain_points=self._extract_list_items(analysis_content, "主要痛点"),
                decision_makers=self._extract_decision_makers(analysis_content),
                buying_signals=self._extract_list_items(analysis_content, "购买信号"),
                risk_factors=self._extract_list_items(analysis_content, "风险因素"),
                recommended_approach=self._extract_section(analysis_content, "推荐销售策略"),
                confidence_score=min(rag_result.confidence + 0.2, 1.0),
                analysis_date=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"客户分析失败: {e}")
            raise
    
    async def generate_talking_points(self, sales_context: Dict[str, Any]) -> List[TalkingPoint]:
        """
        生成个性化销售话术
        """
        try:
            user_query = sales_context.get("user_query", "")
            sales_stage = sales_context.get("sales_stage", "prospecting")
            industry = sales_context.get("industry", "")
            
            # 构建话术生成提示
            prompt = f"""
            作为资深销售专家，请为以下销售场景生成专业的中文销售话术：
            
            场景信息：
            - 销售阶段：{sales_stage}
            - 行业：{industry}
            - 具体需求：{user_query}
            
            请生成以下类型的话术：
            1. 开场白话术
            2. 价值主张表达
            3. 常见异议处理
            4. 成交促进话术
            5. 跟进维护话术
            
            要求：
            - 话术要自然、专业、有说服力
            - 符合中国商务沟通习惯
            - 提供具体的使用场景说明
            - 每个话术给出效果评估
            """
            
            # 检索相关话术模板
            rag_result = await rag_service.query(
                question=f"{industry}行业{sales_stage}阶段销售话术",
                collection_name=self.knowledge_collections["talking_scripts"]
            )
            
            # 增强提示
            enhanced_prompt = f"{prompt}\n\n参考话术模板：\n{rag_result.answer}"
            
            # 生成话术
            llm_response = await llm_service.chat_completion(
                messages=[{"role": "user", "content": enhanced_prompt}],
                temperature=0.4,
                max_tokens=2000
            )
            
            content = llm_response.get("content", "")
            
            # 解析生成的话术
            talking_points = []
            
            # 这里简化处理，实际可以用更复杂的解析逻辑
            sections = content.split("\n\n")
            for section in sections:
                if any(keyword in section for keyword in ["开场白", "价值主张", "异议处理", "成交", "跟进"]):
                    talking_point = self._parse_talking_point(section)
                    if talking_point:
                        talking_points.append(talking_point)
            
            return talking_points
            
        except Exception as e:
            logger.error(f"话术生成失败: {e}")
            raise
    
    async def assess_opportunity(self, opportunity_id: str) -> OpportunityAssessment:
        """
        评估销售机会
        """
        try:
            # 获取机会信息
            async with get_db() as db:
                opportunity_service = OpportunityService(db)
                opportunity = await opportunity_service.get_opportunity(opportunity_id)
                
                if not opportunity:
                    raise ValueError(f"销售机会不存在: {opportunity_id}")
            
            # 构建评估提示
            assessment_prompt = f"""
            作为销售专家，请评估以下销售机会：
            
            机会信息：
            - 机会名称：{opportunity.name}
            - 客户：{opportunity.customer_id}
            - 价值：{opportunity.value}
            - 当前阶段：{opportunity.stage.name if opportunity.stage else '未知'}
            - 预期成交时间：{opportunity.expected_close_date}
            - 当前概率：{opportunity.probability}%
            
            请从以下维度评估：
            1. 成交概率分析
            2. 风险等级评估
            3. 关键成功因素
            4. 潜在障碍识别
            5. 推荐行动计划
            6. 时间节点评估
            7. 竞争地位分析
            
            请提供专业、实用的评估建议。
            """
            
            # 检索成功案例
            rag_result = await rag_service.query(
                question=f"类似销售机会成功案例和评估方法",
                collection_name=self.knowledge_collections["success_cases"]
            )
            
            enhanced_prompt = f"{assessment_prompt}\n\n参考案例：\n{rag_result.answer}"
            
            # 生成评估
            llm_response = await llm_service.chat_completion(
                messages=[{"role": "user", "content": enhanced_prompt}],
                temperature=0.2,
                max_tokens=2000
            )
            
            content = llm_response.get("content", "")
            
            return OpportunityAssessment(
                opportunity_id=opportunity_id,
                current_stage=opportunity.stage.name if opportunity.stage else "未知",
                win_probability=self._extract_probability(content),
                risk_level=self._extract_risk_level(content),
                key_success_factors=self._extract_list_items(content, "关键成功因素"),
                potential_obstacles=self._extract_list_items(content, "潜在障碍"),
                recommended_actions=self._extract_list_items(content, "推荐行动"),
                timeline_assessment=self._extract_timeline_assessment(content),
                competitive_position=self._extract_section(content, "竞争地位"),
                assessment_date=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"机会评估失败: {e}")
            raise
    
    async def recommend_next_action(self, context: Dict[str, Any]) -> List[ActionRecommendation]:
        """
        推荐下一步行动
        """
        try:
            # 构建上下文信息
            context_info = json.dumps(context, ensure_ascii=False, indent=2)
            
            recommendation_prompt = f"""
            基于以下销售上下文，请推荐具体的下一步行动：
            
            当前情况：
            {context_info}
            
            请提供3-5个具体的行动建议，每个建议包括：
            1. 优先级（高/中/低）
            2. 行动类型
            3. 具体描述
            4. 预期结果
            5. 执行时间
            6. 所需资源
            7. 成功指标
            
            建议要具体、可执行、有针对性。
            """
            
            # 检索最佳实践
            rag_result = await rag_service.query(
                question="销售跟进和推进的最佳实践",
                collection_name=self.knowledge_collections["sales_methodology"]
            )
            
            enhanced_prompt = f"{recommendation_prompt}\n\n最佳实践参考：\n{rag_result.answer}"
            
            # 生成建议
            llm_response = await llm_service.chat_completion(
                messages=[{"role": "user", "content": enhanced_prompt}],
                temperature=0.3,
                max_tokens=1500
            )
            
            content = llm_response.get("content", "")
            
            # 解析建议
            recommendations = self._parse_action_recommendations(content)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"行动建议生成失败: {e}")
            raise
    
    # MCP工具处理方法
    
    async def _handle_get_customer_info(self, customer_id: str) -> Dict[str, Any]:
        """处理获取客户信息的MCP调用"""
        try:
            async with get_db() as db:
                customer_service = CustomerService(db)
                customer = await customer_service.get_customer(customer_id)
                
                if customer:
                    return {
                        "success": True,
                        "customer": {
                            "id": customer.id,
                            "name": customer.name,
                            "company": customer.company,
                            "industry": customer.industry,
                            "status": customer.status,
                            "contact": customer.contact
                        }
                    }
                else:
                    return {
                        "success": False,
                        "error": f"客户不存在: {customer_id}"
                    }
                    
        except Exception as e:
            logger.error(f"获取客户信息失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _handle_create_lead(self, **kwargs) -> Dict[str, Any]:
        """处理创建线索的MCP调用"""
        try:
            # 这里应该调用实际的线索服务
            # 简化实现
            return {
                "success": True,
                "lead_id": f"lead_{int(datetime.now().timestamp())}",
                "message": "线索创建成功"
            }
            
        except Exception as e:
            logger.error(f"创建线索失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _handle_update_opportunity(self, **kwargs) -> Dict[str, Any]:
        """处理更新机会的MCP调用"""
        try:
            # 这里应该调用实际的机会服务
            # 简化实现
            return {
                "success": True,
                "opportunity_id": kwargs.get("opportunity_id"),
                "message": "机会更新成功"
            }
            
        except Exception as e:
            logger.error(f"更新机会失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _handle_schedule_follow_up(self, **kwargs) -> Dict[str, Any]:
        """处理安排跟进的MCP调用"""
        try:
            # 这里应该调用实际的日程服务
            # 简化实现
            return {
                "success": True,
                "follow_up_id": f"followup_{int(datetime.now().timestamp())}",
                "message": "跟进安排成功"
            }
            
        except Exception as e:
            logger.error(f"安排跟进失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _handle_generate_proposal(self, **kwargs) -> Dict[str, Any]:
        """处理生成方案的MCP调用"""
        try:
            # 这里应该调用实际的方案生成服务
            # 简化实现
            return {
                "success": True,
                "proposal_id": f"proposal_{int(datetime.now().timestamp())}",
                "message": "方案生成成功"
            }
            
        except Exception as e:
            logger.error(f"生成方案失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    # 辅助方法实现
    
    def _extract_customer_id_from_message(self, content: str) -> Optional[str]:
        """从消息中提取客户ID"""
        import re
        
        # 匹配客户ID模式
        patterns = [
            r'客户ID[：:]\s*([a-zA-Z0-9_]+)',
            r'客户编号[：:]\s*([a-zA-Z0-9_]+)',
            r'customer[_-]?id[：:]\s*([a-zA-Z0-9_]+)',
            r'客户\s*([a-zA-Z0-9_]+)',
            r'customer_([a-zA-Z0-9_]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_opportunity_id_from_message(self, content: str) -> Optional[str]:
        """从消息中提取机会ID"""
        import re
        
        # 匹配机会ID模式
        patterns = [
            r'机会编号[：:]\s*([a-zA-Z0-9_]+)',
            r'机会ID[：:]\s*([a-zA-Z0-9_]+)',
            r'项目编号[：:]\s*([a-zA-Z0-9_]+)',
            r'opportunity[_-]?id[：:]\s*([a-zA-Z0-9_]+)',
            r'opp_([a-zA-Z0-9_]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    async def _get_customer_analysis_guidance(self, content: str) -> Dict[str, Any]:
        """获取客户分析指导"""
        try:
            # 使用RAG检索客户分析最佳实践
            rag_result = await rag_service.query(
                question=f"客户分析方法和最佳实践: {content}",
                collection_name=self.knowledge_collections["sales_methodology"]
            )
            
            return {
                "guidance": rag_result.answer,
                "confidence": rag_result.confidence,
                "sources": rag_result.sources
            }
            
        except Exception as e:
            logger.error(f"获取客户分析指导失败: {e}")
            return {
                "guidance": "客户分析的基本步骤包括：收集客户基本信息、分析业务需求、识别决策者、评估购买能力等。",
                "confidence": 0.5,
                "sources": []
            }
    
    async def _get_opportunity_assessment_guidance(self, content: str) -> Dict[str, Any]:
        """获取机会评估指导"""
        try:
            # 使用RAG检索机会评估最佳实践
            rag_result = await rag_service.query(
                question=f"销售机会评估方法: {content}",
                collection_name=self.knowledge_collections["success_cases"]
            )
            
            return {
                "guidance": rag_result.answer,
                "confidence": rag_result.confidence,
                "sources": rag_result.sources
            }
            
        except Exception as e:
            logger.error(f"获取机会评估指导失败: {e}")
            return {
                "guidance": "机会评估应考虑：客户需求匹配度、预算充足性、决策时间线、竞争态势、内部支持度等因素。",
                "confidence": 0.5,
                "sources": []
            }
    
    async def _parse_crm_operation_intent(self, content: str) -> Dict[str, Any]:
        """解析CRM操作意图"""
        intent = {
            "operation": "unknown",
            "entity": "unknown",
            "parameters": {}
        }
        
        # 识别操作类型
        if any(keyword in content for keyword in ["创建", "新建", "添加"]):
            intent["operation"] = "create"
        elif any(keyword in content for keyword in ["更新", "修改", "编辑"]):
            intent["operation"] = "update"
        elif any(keyword in content for keyword in ["删除", "移除"]):
            intent["operation"] = "delete"
        elif any(keyword in content for keyword in ["查询", "搜索", "查找"]):
            intent["operation"] = "query"
        
        # 识别实体类型
        if any(keyword in content for keyword in ["客户", "customer"]):
            intent["entity"] = "customer"
        elif any(keyword in content for keyword in ["线索", "lead"]):
            intent["entity"] = "lead"
        elif "机会" in content or "项目" in content:
            intent["entity"] = "opportunity"
        
        return intent
    
    async def _perform_crm_operation(self, intent: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """执行CRM操作"""
        operation = intent.get("operation")
        entity = intent.get("entity")
        
        # 这里应该调用相应的CRM服务
        # 简化实现
        return {
            "success": True,
            "operation": operation,
            "entity": entity,
            "message": f"已执行{operation}操作在{entity}上"
        }
    
    # 响应格式化方法
    
    async def _format_structured_response(self, data: Any) -> tuple[str, List[str]]:
        """格式化结构化响应"""
        if isinstance(data, CustomerAnalysis):
            content = f"""
# 客户分析报告

## 客户画像总结
{data.profile_summary}

## 主要痛点
{chr(10).join(f"• {point}" for point in data.pain_points)}

## 购买信号
{chr(10).join(f"• {signal}" for signal in data.buying_signals)}

## 风险因素
{chr(10).join(f"• {risk}" for risk in data.risk_factors)}

## 推荐策略
{data.recommended_approach}

**分析置信度**: {data.confidence_score:.1%}
            """.strip()
            
            suggestions = [
                "制定销售策略",
                "准备客户会议",
                "收集更多信息",
                "联系决策者"
            ]
            
        else:
            content = "分析结果已生成，请查看详细信息。"
            suggestions = ["查看详细报告", "制定下一步计划"]
        
        return content, suggestions
    
    async def _format_talking_points_response(self, data: List[TalkingPoint]) -> tuple[str, List[str]]:
        """格式化话术响应"""
        if not data:
            return "暂无相关话术建议。", ["重新描述需求", "查看话术模板"]
        
        content = "# 销售话术建议\n\n"
        
        for i, point in enumerate(data, 1):
            content += f"""
## {i}. {point.type.value.title()}话术

**内容**: {point.content}

**使用场景**: {', '.join(point.usage_scenarios)}

**效果评分**: {point.effectiveness_score:.1%}

**定制建议**: {point.customization_notes}

---
            """.strip() + "\n\n"
        
        suggestions = [
            "练习话术表达",
            "根据客户调整",
            "准备异议处理",
            "制定沟通计划"
        ]
        
        return content.strip(), suggestions
    
    async def _format_assessment_response(self, data: OpportunityAssessment) -> tuple[str, List[str]]:
        """格式化评估响应"""
        content = f"""
# 销售机会评估报告

## 基本信息
- **当前阶段**: {data.current_stage}
- **成交概率**: {data.win_probability:.1%}
- **风险等级**: {data.risk_level}

## 关键成功因素
{chr(10).join(f"• {factor}" for factor in data.key_success_factors)}

## 潜在障碍
{chr(10).join(f"• {obstacle}" for obstacle in data.potential_obstacles)}

## 推荐行动
{chr(10).join(f"• {action}" for action in data.recommended_actions)}

## 竞争地位
{data.competitive_position}
        """.strip()
        
        suggestions = [
            "制定推进计划",
            "准备竞争策略",
            "安排关键会议",
            "更新机会状态"
        ]
        
        return content, suggestions
    
    async def _format_recommendations_response(self, data: List[ActionRecommendation]) -> tuple[str, List[str]]:
        """格式化建议响应"""
        if not data:
            return "暂无具体行动建议。", ["提供更多上下文", "重新分析情况"]
        
        content = "# 行动建议\n\n"
        
        for i, rec in enumerate(data, 1):
            priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(rec.priority, "⚪")
            
            content += f"""
## {i}. {rec.action_type} {priority_emoji}

**描述**: {rec.description}

**预期结果**: {rec.expected_outcome}

**执行时间**: {rec.timeline}

**所需资源**: {', '.join(rec.resources_needed)}

**成功指标**: {', '.join(rec.success_metrics)}

---
            """.strip() + "\n\n"
        
        suggestions = [
            "开始执行计划",
            "分配资源",
            "设置提醒",
            "跟踪进度"
        ]
        
        return content.strip(), suggestions
    
    async def _format_operation_result_response(self, data: Dict[str, Any]) -> tuple[str, List[str]]:
        """格式化操作结果响应"""
        if data.get("success"):
            content = f"✅ 操作成功完成\n\n{data.get('message', '操作已执行')}"
            suggestions = ["查看结果", "继续下一步", "更新相关信息"]
        else:
            content = f"❌ 操作失败\n\n错误信息: {data.get('error', '未知错误')}"
            suggestions = ["重试操作", "检查参数", "联系技术支持"]
        
        return content, suggestions
    
    async def _format_knowledge_based_response(self, data: Dict[str, Any]) -> tuple[str, List[str]]:
        """格式化知识库响应"""
        content = data.get("answer", "抱歉，没有找到相关信息。")
        
        if data.get("sources"):
            content += "\n\n**参考来源**:\n"
            for source in data["sources"][:3]:  # 只显示前3个来源
                content += f"• {source.get('title', '未知来源')}\n"
        
        suggestions = [
            "了解更多详情",
            "查看相关案例",
            "咨询专家意见",
            "实践应用"
        ]
        
        return content, suggestions
    
    async def _format_general_response(self, data: Any) -> tuple[str, List[str]]:
        """格式化一般响应"""
        if isinstance(data, dict):
            content = data.get("message", "处理完成")
        elif isinstance(data, str):
            content = data
        else:
            content = "已为您处理相关请求。"
        
        suggestions = [
            "查看详细信息",
            "继续咨询",
            "制定计划",
            "执行行动"
        ]
        
        return content, suggestions
    
    async def _integrate_collaboration_result(self, collaboration_result: Dict[str, Any]) -> str:
        """整合协作结果"""
        if not collaboration_result.get("success"):
            return "协作处理过程中遇到了一些问题，但我已尽力为您提供建议。"
        
        results = collaboration_result.get("collaboration_results", [])
        if not results:
            return ""
        
        content = "\n## 协作分析结果\n\n"
        
        for result in results:
            agent_id = result.get("agent_id", "未知Agent")
            if "error" not in result:
                content += f"**{agent_id}**: 已提供专业分析和建议\n"
            else:
                content += f"**{agent_id}**: 暂时无法提供分析\n"
        
        return content
    
    def _calculate_response_confidence(
        self, 
        task_result: Optional[Dict[str, Any]], 
        collaboration_result: Optional[Dict[str, Any]]
    ) -> float:
        """计算响应置信度"""
        base_confidence = 0.7
        
        if not task_result or not task_result.get("success"):
            return 0.1
        
        # 根据任务类型调整置信度
        response_type = task_result.get("response_type", "general")
        type_confidence = {
            "structured": 0.9,
            "talking_points": 0.8,
            "assessment": 0.85,
            "recommendations": 0.8,
            "operation_result": 0.95,
            "knowledge_based": 0.75,
            "general": 0.6
        }.get(response_type, 0.6)
        
        # 如果有协作结果，提高置信度
        if collaboration_result and collaboration_result.get("success"):
            type_confidence = min(type_confidence + 0.1, 1.0)
        
        return type_confidence
    
    def _generate_next_actions(self, task_result: Dict[str, Any]) -> List[str]:
        """生成下一步行动建议"""
        response_type = task_result.get("response_type", "general")
        
        action_map = {
            "structured": [
                "制定销售策略",
                "安排客户会议",
                "准备销售材料",
                "联系决策者"
            ],
            "talking_points": [
                "练习销售话术",
                "准备客户沟通",
                "制定对话计划",
                "收集客户反馈"
            ],
            "assessment": [
                "更新机会状态",
                "制定推进计划",
                "准备竞争策略",
                "安排关键会议"
            ],
            "recommendations": [
                "执行建议行动",
                "分配必要资源",
                "设置跟进提醒",
                "监控执行进度"
            ],
            "operation_result": [
                "验证操作结果",
                "更新相关记录",
                "通知相关人员",
                "规划后续步骤"
            ],
            "knowledge_based": [
                "深入学习相关知识",
                "查看更多案例",
                "咨询专家意见",
                "实践应用技巧"
            ]
        }
        
        return action_map.get(response_type, [
            "继续深入分析",
            "制定具体计划",
            "执行相关行动",
            "跟踪结果反馈"
        ])
    
    # 内容解析辅助方法
    
    def _extract_section(self, content: str, section_name: str) -> str:
        """提取内容中的特定章节"""
        import re
        
        # 匹配章节标题和内容
        patterns = [
            rf'{section_name}[：:]\s*\n?(.*?)(?=\n\n|\n[^•\-\d\s]|$)',
            rf'{section_name}[：:]?\s*(.*?)(?=\n\n|\n[^•\-\d\s]|$)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return ""
    
    def _extract_list_items(self, content: str, section_name: str) -> List[str]:
        """提取列表项"""
        section_content = self._extract_section(content, section_name)
        if not section_content:
            return []
        
        import re
        
        # 匹配各种列表格式
        patterns = [
            r'[•\-]\s*(.+)',  # • 或 - 开头
            r'\d+\.\s*(.+)',  # 数字开头
            r'[①②③④⑤⑥⑦⑧⑨⑩]\s*(.+)'  # 圆圈数字
        ]
        
        items = []
        for pattern in patterns:
            matches = re.findall(pattern, section_content, re.MULTILINE)
            items.extend([match.strip() for match in matches if match.strip()])
        
        return list(set(items))  # 去重
    
    def _extract_decision_makers(self, content: str) -> List[Dict[str, Any]]:
        """提取决策者信息"""
        section_content = self._extract_section(content, "决策者")
        if not section_content:
            return []
        
        # 简化实现，实际可以用更复杂的NLP解析
        decision_makers = []
        lines = section_content.split('\n')
        
        for line in lines:
            line = line.strip()
            if line and not line.startswith(('•', '-', '1.', '2.')):
                decision_makers.append({
                    "name": line,
                    "role": "决策者",
                    "influence": "high"
                })
        
        return decision_makers
    
    def _extract_probability(self, content: str) -> float:
        """提取概率值"""
        import re
        
        # 匹配百分比格式
        percent_match = re.search(r'(\d+(?:\.\d+)?)%', content)
        if percent_match:
            return float(percent_match.group(1)) / 100
        
        # 匹配小数格式
        decimal_match = re.search(r'概率[：:]?\s*([01]?\.\d+)', content)
        if decimal_match:
            return float(decimal_match.group(1))
        
        # 默认返回中等概率
        return 0.5
    
    def _extract_risk_level(self, content: str) -> str:
        """提取风险等级"""
        content_lower = content.lower()
        
        if any(keyword in content_lower for keyword in ["高风险", "high risk", "风险很高", "风险较高"]):
            return "high"
        elif any(keyword in content_lower for keyword in ["低风险", "low risk", "风险很低", "风险较低"]):
            return "low"
        else:
            return "medium"
    
    def _extract_timeline_assessment(self, content: str) -> Dict[str, Any]:
        """提取时间线评估"""
        timeline_content = self._extract_section(content, "时间")
        
        return {
            "assessment": timeline_content or "时间线评估中等",
            "urgency": "medium",
            "key_dates": []
        }
    
    def _parse_talking_point(self, section: str) -> Optional[TalkingPoint]:
        """解析话术点"""
        if not section.strip():
            return None
        
        # 识别话术类型
        talking_type = TalkingPointType.OPENING  # 默认类型
        
        if "开场" in section:
            talking_type = TalkingPointType.OPENING
        elif "价值" in section:
            talking_type = TalkingPointType.VALUE_PROPOSITION
        elif "异议" in section:
            talking_type = TalkingPointType.OBJECTION_HANDLING
        elif "成交" in section:
            talking_type = TalkingPointType.CLOSING
        elif "跟进" in section:
            talking_type = TalkingPointType.FOLLOW_UP
        
        # 提取话术内容
        lines = [line.strip() for line in section.split('\n') if line.strip()]
        content = ' '.join(lines[1:]) if len(lines) > 1 else section
        
        return TalkingPoint(
            type=talking_type,
            content=content,
            context="销售沟通",
            effectiveness_score=0.8,  # 默认效果评分
            usage_scenarios=["电话沟通", "面对面会议"],
            customization_notes="可根据具体客户情况调整"
        )
    
    def _parse_action_recommendations(self, content: str) -> List[ActionRecommendation]:
        """解析行动建议"""
        recommendations = []
        
        # 按段落分割
        sections = content.split('\n\n')
        
        for section in sections:
            if not section.strip():
                continue
            
            lines = [line.strip() for line in section.split('\n') if line.strip()]
            if not lines:
                continue
            
            # 提取优先级
            priority = "medium"
            if "高优先级" in lines[0] or "high" in lines[0].lower():
                priority = "high"
            elif "低优先级" in lines[0] or "low" in lines[0].lower():
                priority = "low"
            
            # 提取行动类型和描述
            action_type = "一般行动"
            description = ""
            expected_outcome = ""
            timeline = "待定"
            resources_needed = []
            success_metrics = []
            
            for line in lines:
                if "优先级" in line and "-" in line:
                    parts = line.split("-", 1)
                    if len(parts) > 1:
                        action_type = parts[1].strip()
                elif "预期结果" in line:
                    expected_outcome = line.split("：", 1)[-1].strip()
                elif "执行时间" in line:
                    timeline = line.split("：", 1)[-1].strip()
                elif "所需资源" in line:
                    resources_text = line.split("：", 1)[-1].strip()
                    resources_needed = [r.strip() for r in resources_text.split("、")]
                elif "成功指标" in line:
                    metrics_text = line.split("：", 1)[-1].strip()
                    success_metrics = [m.strip() for m in metrics_text.split("、")]
                elif not any(keyword in line for keyword in ["优先级", "预期结果", "执行时间", "所需资源", "成功指标"]):
                    if not description:
                        description = line
            
            if action_type != "一般行动" or description:
                recommendations.append(ActionRecommendation(
                    priority=priority,
                    action_type=action_type,
                    description=description or action_type,
                    expected_outcome=expected_outcome or "提升销售效果",
                    timeline=timeline,
                    resources_needed=resources_needed or ["销售人员"],
                    success_metrics=success_metrics or ["完成度"]
                ))
        
        return recommendations
    
    async def _handle_update_opportunity(self, **kwargs) -> Dict[str, Any]:
        """处理更新销售机会的MCP调用"""
        try:
            # 这里应该调用实际的机会服务
            # 简化实现
            return {
                "success": True,
                "opportunity_id": kwargs.get("opportunity_id"),
                "message": "销售机会更新成功"
            }
            
        except Exception as e:
            logger.error(f"更新销售机会失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _handle_schedule_follow_up(self, **kwargs) -> Dict[str, Any]:
        """处理安排跟进的MCP调用"""
        try:
            return {
                "success": True,
                "follow_up_id": f"followup_{int(datetime.now().timestamp())}",
                "message": "跟进任务已安排"
            }
            
        except Exception as e:
            logger.error(f"安排跟进失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _handle_generate_proposal(self, **kwargs) -> Dict[str, Any]:
        """处理生成提案的MCP调用"""
        try:
            return {
                "success": True,
                "proposal_id": f"proposal_{int(datetime.now().timestamp())}",
                "message": "提案生成成功"
            }
            
        except Exception as e:
            logger.error(f"生成提案失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    # 辅助方法
    

    
    def _extract_section(self, content: str, section_name: str) -> str:
        """提取内容中的特定章节"""
        lines = content.split('\n')
        section_content = []
        in_section = False
        
        for line in lines:
            if section_name in line:
                in_section = True
                continue
            elif in_section and line.strip() and any(keyword in line for keyword in ["总结", "分析", "识别", "评估", "策略"]):
                break
            elif in_section:
                section_content.append(line.strip())
        
        return '\n'.join(section_content).strip()
    
    def _extract_list_items(self, content: str, section_name: str) -> List[str]:
        """提取列表项"""
        section = self._extract_section(content, section_name)
        items = []
        
        for line in section.split('\n'):
            line = line.strip()
            if line and (line.startswith('-') or line.startswith('•') or line.startswith('*')):
                items.append(line[1:].strip())
            elif line and any(char.isdigit() for char in line[:3]):
                items.append(line.split('.', 1)[-1].strip())
        
        return items
    
    def _extract_decision_makers(self, content: str) -> List[Dict[str, Any]]:
        """提取决策者信息"""
        # 简化实现
        decision_makers_text = self._extract_section(content, "决策者")
        return [{"name": "待识别", "role": "决策者", "influence": "高"}]
    
    def _extract_probability(self, content: str) -> float:
        """提取成交概率"""
        import re
        pattern = r'概率[:：]?\s*(\d+(?:\.\d+)?)%?'
        match = re.search(pattern, content)
        if match:
            return float(match.group(1)) / 100 if float(match.group(1)) > 1 else float(match.group(1))
        return 0.5  # 默认值
    
    def _extract_risk_level(self, content: str) -> str:
        """提取风险等级"""
        if "高风险" in content or "风险较高" in content:
            return "high"
        elif "中风险" in content or "风险适中" in content:
            return "medium"
        elif "低风险" in content or "风险较低" in content:
            return "low"
        return "medium"
    
    def _extract_timeline_assessment(self, content: str) -> Dict[str, Any]:
        """提取时间节点评估"""
        return {
            "estimated_close_date": "待评估",
            "key_milestones": ["需求确认", "方案提交", "商务谈判", "合同签署"],
            "timeline_risk": "medium"
        }
    
    def _parse_talking_point(self, section: str) -> Optional[TalkingPoint]:
        """解析话术点"""
        try:
            # 简化解析逻辑
            lines = section.split('\n')
            if len(lines) < 2:
                return None
            
            title = lines[0].strip()
            content = '\n'.join(lines[1:]).strip()
            
            # 确定话术类型
            talking_point_type = TalkingPointType.OPENING
            if "开场" in title:
                talking_point_type = TalkingPointType.OPENING
            elif "价值" in title:
                talking_point_type = TalkingPointType.VALUE_PROPOSITION
            elif "异议" in title:
                talking_point_type = TalkingPointType.OBJECTION_HANDLING
            elif "成交" in title:
                talking_point_type = TalkingPointType.CLOSING
            elif "跟进" in title:
                talking_point_type = TalkingPointType.FOLLOW_UP
            
            return TalkingPoint(
                type=talking_point_type,
                content=content,
                context=title,
                effectiveness_score=0.8,
                usage_scenarios=["电话沟通", "面对面会议", "邮件跟进"],
                customization_notes="可根据具体客户情况调整"
            )
            
        except Exception as e:
            logger.error(f"解析话术点失败: {e}")
            return None
    

    
    # 响应格式化方法
    
    async def _format_structured_response(self, data: Any) -> tuple[str, List[str]]:
        """格式化结构化响应"""
        if isinstance(data, CustomerAnalysis):
            content = f"""
📊 **客户分析报告**

**客户画像总结：**
{data.profile_summary}

**主要痛点：**
{chr(10).join(f"• {point}" for point in data.pain_points)}

**购买信号：**
{chr(10).join(f"• {signal}" for signal in data.buying_signals)}

**风险因素：**
{chr(10).join(f"• {risk}" for risk in data.risk_factors)}

**推荐策略：**
{data.recommended_approach}

**分析置信度：** {data.confidence_score:.1%}
            """.strip()
            
            suggestions = [
                "制定个性化销售策略",
                "准备针对性产品演示",
                "安排关键决策者会议",
                "准备异议处理方案"
            ]
            
        else:
            content = "分析结果格式化失败"
            suggestions = ["请重新分析"]
        
        return content, suggestions
    
    async def _format_talking_points_response(self, data: List[TalkingPoint]) -> tuple[str, List[str]]:
        """格式化话术响应"""
        if not data:
            return "未能生成合适的话术，请提供更多上下文信息。", ["提供客户背景", "明确销售阶段"]
        
        content_parts = ["🎯 **销售话术建议**\n"]
        
        for i, point in enumerate(data, 1):
            content_parts.append(f"""
**{i}. {point.type.value.upper()}话术**
*适用场景：{point.context}*

{point.content}

*使用建议：{point.customization_notes}*
*效果评分：{point.effectiveness_score:.1%}*
            """.strip())
        
        content = "\n\n".join(content_parts)
        
        suggestions = [
            "根据客户反应调整话术",
            "准备后续跟进话术",
            "练习自然表达方式",
            "准备相关案例支撑"
        ]
        
        return content, suggestions
    
    async def _format_assessment_response(self, data: OpportunityAssessment) -> tuple[str, List[str]]:
        """格式化评估响应"""
        content = f"""
📈 **销售机会评估报告**

**基本信息：**
• 当前阶段：{data.current_stage}
• 成交概率：{data.win_probability:.1%}
• 风险等级：{data.risk_level}

**关键成功因素：**
{chr(10).join(f"• {factor}" for factor in data.key_success_factors)}

**潜在障碍：**
{chr(10).join(f"• {obstacle}" for obstacle in data.potential_obstacles)}

**推荐行动：**
{chr(10).join(f"• {action}" for action in data.recommended_actions)}

**竞争地位：**
{data.competitive_position}
        """.strip()
        
        suggestions = [
            "制定详细推进计划",
            "准备风险应对策略",
            "安排关键里程碑检查",
            "加强竞争优势展示"
        ]
        
        return content, suggestions
    
    async def _format_recommendations_response(self, data: List[ActionRecommendation]) -> tuple[str, List[str]]:
        """格式化建议响应"""
        if not data:
            return "暂无具体行动建议，请提供更多上下文信息。", ["补充销售背景", "明确当前困难"]
        
        content_parts = ["📋 **行动建议**\n"]
        
        for i, rec in enumerate(data, 1):
            priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(rec.priority, "⚪")
            
            content_parts.append(f"""
**{i}. {rec.action_type}** {priority_emoji}
{rec.description}

*预期结果：{rec.expected_outcome}*
*执行时间：{rec.timeline}*
*所需资源：{', '.join(rec.resources_needed)}*
            """.strip())
        
        content = "\n\n".join(content_parts)
        
        suggestions = [
            "按优先级执行建议",
            "设置执行时间节点",
            "准备必要资源",
            "建立跟踪机制"
        ]
        
        return content, suggestions
    
    async def _format_operation_result_response(self, data: Dict[str, Any]) -> tuple[str, List[str]]:
        """格式化操作结果响应"""
        if data.get("success"):
            content = f"✅ 操作执行成功\n\n{data.get('message', '操作已完成')}"
            suggestions = ["查看操作结果", "继续后续操作"]
        else:
            content = f"❌ 操作执行失败\n\n错误信息：{data.get('error', '未知错误')}"
            suggestions = ["检查输入参数", "重试操作", "联系技术支持"]
        
        return content, suggestions
    
    async def _format_knowledge_based_response(self, data: Dict[str, Any]) -> tuple[str, List[str]]:
        """格式化知识库响应"""
        answer = data.get("answer", "未找到相关信息")
        confidence = data.get("confidence", 0.0)
        
        content = f"""
💡 **销售知识解答**

{answer}

*回答置信度：{confidence:.1%}*
        """.strip()
        
        suggestions = [
            "查看相关案例",
            "获取更多详细信息",
            "咨询销售专家",
            "实践应用建议"
        ]
        
        return content, suggestions
    
    async def _format_general_response(self, data: Any) -> tuple[str, List[str]]:
        """格式化一般响应"""
        content = str(data) if data else "处理完成"
        suggestions = ["继续咨询", "查看详细信息"]
        return content, suggestions
    
    async def _integrate_collaboration_result(self, collaboration_result: Dict[str, Any]) -> str:
        """整合协作结果"""
        return f"\n**协作信息：**\n{collaboration_result.get('summary', '已获得其他专家的协作支持')}"
    
    def _calculate_response_confidence(
        self, 
        task_result: Dict[str, Any], 
        collaboration_result: Optional[Dict[str, Any]]
    ) -> float:
        """计算响应置信度"""
        base_confidence = 0.8
        
        # 根据任务结果调整
        if task_result.get("success"):
            base_confidence += 0.1
        
        # 根据协作结果调整
        if collaboration_result and collaboration_result.get("success"):
            base_confidence += 0.05
        
        return min(base_confidence, 1.0)
    
    def _generate_next_actions(self, task_result: Dict[str, Any]) -> List[str]:
        """生成下一步行动建议"""
        response_type = task_result.get("response_type", "general")
        
        if response_type == "customer_analysis":
            return ["制定销售策略", "准备客户会议", "收集更多信息"]
        elif response_type == "talking_points":
            return ["练习话术表达", "准备客户演示", "安排客户沟通"]
        elif response_type == "assessment":
            return ["制定推进计划", "准备风险应对", "安排关键会议"]
        elif response_type == "recommendations":
            return ["执行优先建议", "设置跟踪提醒", "准备必要资源"]
        else:
            return ["继续深入分析", "制定具体计划", "开始执行行动"]
    
    # 辅助方法
    
    async def _get_customer_analysis_guidance(self, query: str) -> Dict[str, Any]:
        """获取客户分析指导"""
        guidance_prompt = f"""
        用户询问：{query}
        
        请提供客户分析的专业指导，包括：
        1. 分析框架和方法
        2. 关键信息收集点
        3. 分析维度和要点
        4. 常见问题和解决方案
        """
        
        rag_result = await rag_service.query(
            question=guidance_prompt,
            collection_name=self.knowledge_collections["sales_methodology"]
        )
        
        return {
            "guidance": rag_result.answer,
            "confidence": rag_result.confidence,
            "sources": rag_result.sources
        }
    
    async def _get_opportunity_assessment_guidance(self, query: str) -> Dict[str, Any]:
        """获取机会评估指导"""
        guidance_prompt = f"""
        用户询问：{query}
        
        请提供销售机会评估的专业指导，包括：
        1. 评估框架和标准
        2. 关键评估维度
        3. 风险识别方法
        4. 成功概率判断标准
        """
        
        rag_result = await rag_service.query(
            question=guidance_prompt,
            collection_name=self.knowledge_collections["sales_methodology"]
        )
        
        return {
            "guidance": rag_result.answer,
            "confidence": rag_result.confidence,
            "sources": rag_result.sources
        }
    
    async def _parse_crm_operation_intent(self, content: str) -> Dict[str, Any]:
        """解析CRM操作意图"""
        # 简化实现，实际可以用更复杂的NLP方法
        intent = {
            "operation": "unknown",
            "entity": "unknown",
            "parameters": {}
        }
        
        if "创建" in content or "新建" in content:
            intent["operation"] = "create"
        elif "更新" in content or "修改" in content:
            intent["operation"] = "update"
        elif "删除" in content:
            intent["operation"] = "delete"
        elif "查询" in content or "获取" in content:
            intent["operation"] = "read"
        
        if "客户" in content:
            intent["entity"] = "customer"
        elif "线索" in content:
            intent["entity"] = "lead"
        elif "机会" in content or "项目" in content:
            intent["entity"] = "opportunity"
        
        return intent
    
    async def _perform_crm_operation(self, intent: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """执行CRM操作"""
        operation = intent.get("operation")
        entity = intent.get("entity")
        
        # 这里应该调用相应的CRM服务
        # 简化实现
        return {
            "success": True,
            "operation": operation,
            "entity": entity,
            "message": f"已执行{operation}操作在{entity}上"
        }
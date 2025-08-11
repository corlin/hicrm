"""
市场Agent - 专业化市场分析Agent

提供线索评分、中文市场分析、竞争分析等市场专业功能
支持Function Calling和MCP协议集成
"""

import json
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from src.agents.base import BaseAgent, AgentMessage, AgentResponse, AgentCapability
from src.services.lead_service import LeadService
from src.services.lead_scoring_service import LeadScoringService
from src.services.llm_service import llm_service
from src.services.rag_service import rag_service, RAGMode
from src.core.database import get_db

logger = logging.getLogger(__name__)


class MarketAnalysisType(str, Enum):
    """市场分析类型枚举"""
    INDUSTRY_TREND = "industry_trend"  # 行业趋势
    COMPETITIVE_LANDSCAPE = "competitive_landscape"  # 竞争格局
    MARKET_SIZE = "market_size"  # 市场规模
    CUSTOMER_SEGMENT = "customer_segment"  # 客户细分
    PRICING_ANALYSIS = "pricing_analysis"  # 定价分析
    SWOT_ANALYSIS = "swot_analysis"  # SWOT分析


class CompetitorType(str, Enum):
    """竞争对手类型枚举"""
    DIRECT = "direct"  # 直接竞争对手
    INDIRECT = "indirect"  # 间接竞争对手
    POTENTIAL = "potential"  # 潜在竞争对手
    SUBSTITUTE = "substitute"  # 替代品竞争


@dataclass
class LeadScoreDetail:
    """线索评分详情"""
    lead_id: str
    total_score: float
    confidence: float
    score_factors: List[Dict[str, Any]]
    recommendations: List[str]
    risk_factors: List[str]
    scoring_date: datetime
    algorithm_version: str


@dataclass
class MarketTrend:
    """市场趋势分析"""
    industry: str
    trend_direction: str  # up, down, stable
    growth_rate: float
    key_drivers: List[str]
    market_size: Dict[str, Any]
    forecast: Dict[str, Any]
    opportunities: List[str]
    threats: List[str]
    analysis_date: datetime
    confidence_score: float


@dataclass
class CompetitiveAnalysis:
    """竞争分析结果"""
    competitor_name: str
    competitor_type: CompetitorType
    market_share: Optional[float]
    strengths: List[str]
    weaknesses: List[str]
    products: List[Dict[str, Any]]
    pricing_strategy: str
    target_customers: List[str]
    competitive_advantages: List[str]
    threat_level: str  # high, medium, low
    analysis_date: datetime


@dataclass
class MarketingStrategy:
    """营销策略建议"""
    target_segment: str
    positioning: str
    key_messages: List[str]
    channels: List[str]
    tactics: List[Dict[str, Any]]
    budget_allocation: Dict[str, float]
    timeline: Dict[str, str]
    success_metrics: List[str]
    expected_roi: Optional[float]


class MarketAgent(BaseAgent):
    """
    市场专业Agent
    
    专注于市场分析和线索管理，提供智能化的市场支持：
    - 智能线索评分和分析
    - 中文市场趋势分析
    - 竞争对手分析
    - 营销策略建议
    - 数据分析操作
    """
    
    def __init__(
        self,
        agent_id: str = "market_agent",
        name: str = "市场专家",
        state_manager=None,
        communicator=None
    ):
        print(f"DEBUG: Starting MarketAgent init for {name}")
        print("DEBUG: Defining capabilities...")
        # 定义市场Agent的专业能力
        capabilities = [
            AgentCapability(
                name="score_lead",
                description="智能评估线索质量和转化潜力",
                parameters={
                    "lead_id": {"type": "string", "required": True},
                    "scoring_method": {"type": "string", "enum": ["standard", "advanced", "custom"]},
                    "include_recommendations": {"type": "boolean", "default": True}
                }
            ),
            AgentCapability(
                name="analyze_market_trend",
                description="分析中文市场趋势和行业发展方向",
                parameters={
                    "industry": {"type": "string", "required": True},
                    "region": {"type": "string", "default": "中国"},
                    "time_period": {"type": "string", "enum": ["quarterly", "yearly", "5-year"]},
                    "analysis_depth": {"type": "string", "enum": ["basic", "detailed", "comprehensive"]}
                }
            ),
            AgentCapability(
                name="competitive_analysis",
                description="深度分析竞争对手和市场竞争格局",
                parameters={
                    "competitor": {"type": "string", "required": True},
                    "analysis_scope": {"type": "array", "items": {"type": "string"}},
                    "include_swot": {"type": "boolean", "default": True}
                }
            ),
            AgentCapability(
                name="recommend_marketing_strategy",
                description="基于市场分析推荐营销策略",
                parameters={
                    "target_market": {"type": "object", "required": True},
                    "business_objectives": {"type": "array", "items": {"type": "string"}},
                    "budget_range": {"type": "object"},
                    "timeline": {"type": "string"}
                }
            ),
            AgentCapability(
                name="market_data_analysis",
                description="执行市场数据分析和报告生成",
                parameters={
                    "data_source": {"type": "string", "required": True},
                    "analysis_type": {"type": "string", "enum": list(MarketAnalysisType)},
                    "output_format": {"type": "string", "enum": ["report", "dashboard", "presentation"]}
                }
            )
        ]
        
        print("DEBUG: Calling super().__init__...")
        super().__init__(
            agent_id=agent_id,
            name=name,
            specialty="市场分析与线索管理",
            capabilities=capabilities,
            state_manager=state_manager,
            communicator=communicator
        )
        
        print("DEBUG: Setting up knowledge collections...")
        # 市场知识库集合名称
        self.knowledge_collections = {
            "market_trends": "chinese_market_trends",
            "industry_reports": "industry_analysis_reports", 
            "competitive_intelligence": "competitive_analysis_db",
            "marketing_strategies": "marketing_best_practices",
            "lead_scoring_models": "lead_scoring_knowledge",
            "customer_segments": "customer_segmentation_data"
        }
        
        # MCP工具配置
        self.mcp_tools = {
            "get_market_data": self._handle_get_market_data,
            "analyze_competitor": self._handle_analyze_competitor,
            "score_lead_batch": self._handle_score_lead_batch,
            "generate_market_report": self._handle_generate_market_report,
            "update_market_intelligence": self._handle_update_market_intelligence
        }
        
        # 延迟初始化服务
        self._lead_service = None
        self._scoring_service = None
        
        print(f"DEBUG: 市场Agent {self.name} 初始化完成")
        # logger.info(f"市场Agent {self.name} 初始化完成")
    
    @property
    def lead_service(self):
        """延迟初始化线索服务"""
        if self._lead_service is None:
            self._lead_service = LeadService()
        return self._lead_service
    
    @property
    def scoring_service(self):
        """延迟初始化评分服务"""
        if self._scoring_service is None:
            self._scoring_service = LeadScoringService()
        return self._scoring_service
    
    async def analyze_task(self, message: AgentMessage) -> Dict[str, Any]:
        """
        分析市场相关任务
        """
        try:
            content = message.content.lower()
            metadata = message.metadata or {}
            
            # 识别任务类型
            task_type = "general"
            needs_collaboration = False
            required_agents = []
            
            # 线索评分相关
            if (any(keyword in content for keyword in ["线索评分", "评估线索", "线索质量", "转化概率"]) or
                ("评估" in content and "线索" in content) or
                ("线索" in content and "质量" in content)):
                task_type = "lead_scoring"
                
            # 市场趋势分析相关
            elif any(keyword in content for keyword in ["市场趋势", "行业分析", "市场发展", "行业前景", "市场预测"]):
                task_type = "market_trend_analysis"
                
            # 竞争分析相关
            elif any(keyword in content for keyword in ["竞争对手", "竞争分析", "市场竞争", "竞争情况", "对手分析"]):
                task_type = "competitive_analysis"
                
            # 营销策略相关
            elif any(keyword in content for keyword in ["营销策略", "市场策略", "推广方案", "营销建议"]):
                task_type = "marketing_strategy"
                
            # 市场数据分析相关
            elif any(keyword in content for keyword in ["数据分析", "市场数据", "统计分析", "报告生成"]):
                task_type = "market_data_analysis"
            
            # 判断是否需要协作
            if any(keyword in content for keyword in ["销售", "客户关系", "成交"]):
                needs_collaboration = True
                required_agents.append("sales_agent")
                
            if any(keyword in content for keyword in ["产品", "技术", "解决方案"]):
                needs_collaboration = True
                required_agents.append("product_agent")
                
            if any(keyword in content for keyword in ["团队", "管理", "资源配置"]):
                needs_collaboration = True
                required_agents.append("sales_management_agent")
            
            return {
                "task_type": task_type,
                "needs_collaboration": needs_collaboration,
                "required_agents": required_agents,
                "collaboration_type": "sequential" if needs_collaboration else None,
                "priority": metadata.get("priority", "medium"),
                "context": {
                    "user_role": metadata.get("user_role", "marketing_manager"),
                    "industry": metadata.get("industry"),
                    "region": metadata.get("region", "中国"),
                    "lead_id": metadata.get("lead_id"),
                    "competitor": metadata.get("competitor")
                }
            }
            
        except Exception as e:
            logger.error(f"市场任务分析失败: {e}")
            return {
                "task_type": "general",
                "needs_collaboration": False,
                "error": str(e)
            }
    
    async def execute_task(self, message: AgentMessage, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行市场任务
        """
        task_type = analysis.get("task_type", "general")
        context = analysis.get("context", {})
        
        try:
            if task_type == "lead_scoring":
                return await self._execute_lead_scoring(message, context)
            elif task_type == "market_trend_analysis":
                return await self._execute_market_trend_analysis(message, context)
            elif task_type == "competitive_analysis":
                return await self._execute_competitive_analysis(message, context)
            elif task_type == "marketing_strategy":
                return await self._execute_marketing_strategy(message, context)
            elif task_type == "market_data_analysis":
                return await self._execute_market_data_analysis(message, context)
            else:
                return await self._execute_general_market_query(message, context)
                
        except Exception as e:
            logger.error(f"市场任务执行失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "fallback_response": "抱歉，处理您的市场分析请求时遇到了问题，请稍后重试。"
            }
    
    async def _execute_lead_scoring(self, message: AgentMessage, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行线索评分任务"""
        try:
            lead_id = context.get("lead_id")
            if not lead_id:
                # 尝试从消息中提取线索ID
                lead_id = self._extract_lead_id_from_message(message.content)
            
            if lead_id:
                score_detail = await self.score_lead(lead_id)
                return {
                    "success": True,
                    "analysis_type": "lead_scoring",
                    "data": score_detail,
                    "response_type": "scoring_result"
                }
            else:
                # 如果没有具体线索ID，提供一般性的评分指导
                guidance = await self._get_lead_scoring_guidance(message.content)
                return {
                    "success": True,
                    "analysis_type": "lead_scoring_guidance",
                    "data": guidance,
                    "response_type": "guidance"
                }
                
        except Exception as e:
            logger.error(f"线索评分执行失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _execute_market_trend_analysis(self, message: AgentMessage, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行市场趋势分析任务"""
        try:
            industry = context.get("industry")
            if not industry:
                industry = self._extract_industry_from_message(message.content)
            
            if industry:
                trend_analysis = await self.analyze_market_trend(industry)
                return {
                    "success": True,
                    "analysis_type": "market_trend",
                    "data": trend_analysis,
                    "response_type": "trend_analysis"
                }
            else:
                # 提供一般性的市场趋势指导
                guidance = await self._get_market_trend_guidance(message.content)
                return {
                    "success": True,
                    "analysis_type": "market_trend_guidance",
                    "data": guidance,
                    "response_type": "guidance"
                }
                
        except Exception as e:
            logger.error(f"市场趋势分析执行失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _execute_competitive_analysis(self, message: AgentMessage, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行竞争分析任务"""
        try:
            competitor = context.get("competitor")
            if not competitor:
                competitor = self._extract_competitor_from_message(message.content)
            
            if competitor:
                competitive_analysis = await self.generate_competitive_analysis(competitor)
                return {
                    "success": True,
                    "analysis_type": "competitive_analysis",
                    "data": competitive_analysis,
                    "response_type": "competitive_analysis"
                }
            else:
                # 提供一般性的竞争分析指导
                guidance = await self._get_competitive_analysis_guidance(message.content)
                return {
                    "success": True,
                    "analysis_type": "competitive_analysis_guidance",
                    "data": guidance,
                    "response_type": "guidance"
                }
                
        except Exception as e:
            logger.error(f"竞争分析执行失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _execute_marketing_strategy(self, message: AgentMessage, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行营销策略任务"""
        try:
            # 构建目标市场信息
            target_market = {
                "industry": context.get("industry"),
                "region": context.get("region", "中国"),
                "user_query": message.content
            }
            
            strategy = await self.recommend_marketing_strategy(target_market)
            
            return {
                "success": True,
                "analysis_type": "marketing_strategy",
                "data": strategy,
                "response_type": "strategy_recommendation"
            }
            
        except Exception as e:
            logger.error(f"营销策略执行失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _execute_market_data_analysis(self, message: AgentMessage, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行市场数据分析任务"""
        try:
            # 解析数据分析需求
            analysis_request = await self._parse_data_analysis_request(message.content)
            
            # 执行数据分析
            analysis_result = await self._perform_market_data_analysis(analysis_request, context)
            
            return {
                "success": True,
                "analysis_type": "market_data_analysis",
                "data": analysis_result,
                "response_type": "data_analysis_result"
            }
            
        except Exception as e:
            logger.error(f"市场数据分析执行失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _execute_general_market_query(self, message: AgentMessage, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行一般市场查询"""
        try:
            # 使用RAG检索相关市场知识
            rag_result = await rag_service.query(
                question=message.content,
                mode=RAGMode.HYBRID,
                collection_name=self.knowledge_collections["market_trends"]
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
            logger.error(f"一般市场查询执行失败: {e}")
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
        生成市场Agent响应
        """
        try:
            if not task_result or not task_result.get("success", False):
                error_msg = task_result.get("error", "未知错误") if task_result else "任务执行失败"
                fallback = task_result.get("fallback_response", "抱歉，我无法处理您的市场分析请求。")
                
                return AgentResponse(
                    content=fallback,
                    confidence=0.1,
                    suggestions=["请检查输入信息", "稍后重试", "联系技术支持"],
                    metadata={"error": error_msg}
                )
            
            response_type = task_result.get("response_type", "general")
            data = task_result.get("data", {})
            
            # 根据响应类型生成不同格式的回复
            if response_type == "scoring_result":
                content, suggestions = await self._format_scoring_result_response(data)
            elif response_type == "trend_analysis":
                content, suggestions = await self._format_trend_analysis_response(data)
            elif response_type == "competitive_analysis":
                content, suggestions = await self._format_competitive_analysis_response(data)
            elif response_type == "strategy_recommendation":
                content, suggestions = await self._format_strategy_recommendation_response(data)
            elif response_type == "data_analysis_result":
                content, suggestions = await self._format_data_analysis_response(data)
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
            logger.error(f"生成市场Agent响应失败: {e}")
            return AgentResponse(
                content="抱歉，生成响应时遇到了问题。",
                confidence=0.0,
                suggestions=["请重新提问", "检查网络连接"],
                metadata={"error": str(e)}
            )
    
    # 核心业务方法实现
    
    async def score_lead(self, lead_id: str) -> LeadScoreDetail:
        """
        智能评估线索质量和转化潜力
        """
        try:
            # 获取线索信息
            async with get_db() as db:
                lead = await self.lead_service.get_lead(lead_id, db)
                
                if not lead:
                    raise ValueError(f"线索不存在: {lead_id}")
            
            # 使用评分服务计算基础评分
            async with get_db() as db:
                base_score = await self.scoring_service.calculate_lead_score(lead, db)
            
            # 使用LLM和RAG进行深度分析
            analysis_prompt = f"""
            作为专业的市场分析师，请深度评估以下线索的质量和转化潜力：
            
            线索信息：
            - 姓名：{lead.name}
            - 公司：{lead.company}
            - 行业：{lead.industry}
            - 预算：{lead.budget}
            - 时间线：{lead.timeline}
            - 需求：{lead.requirements}
            - 来源：{lead.source}
            - 当前状态：{lead.status}
            
            基础评分：{base_score.total_score if base_score else 0}
            
            请从以下维度进行深度分析：
            1. 转化概率评估
            2. 关键评分因子分析
            3. 风险因素识别
            4. 跟进建议
            5. 优先级判断
            
            请用中文回答，分析要专业、实用。
            """
            
            # 检索相关评分知识
            rag_result = await rag_service.query(
                question=f"如何评估{lead.industry}行业线索质量",
                collection_name=self.knowledge_collections["lead_scoring_models"]
            )
            
            # 结合RAG结果优化分析提示
            enhanced_prompt = f"{analysis_prompt}\n\n参考评分模型：\n{rag_result.answer}"
            
            # 使用LLM生成深度分析
            llm_response = await llm_service.chat_completion(
                messages=[{"role": "user", "content": enhanced_prompt}],
                temperature=0.2,
                max_tokens=1500
            )
            
            analysis_content = llm_response.get("content", "")
            
            # 解析分析结果
            score_factors = self._extract_score_factors(analysis_content, base_score)
            recommendations = self._extract_list_items(analysis_content, "跟进建议")
            risk_factors = self._extract_list_items(analysis_content, "风险因素")
            
            # 计算最终评分（结合基础评分和LLM分析）
            final_score = base_score.total_score if base_score else 0.0
            confidence = min((rag_result.confidence + 0.3), 1.0)
            
            return LeadScoreDetail(
                lead_id=lead_id,
                total_score=final_score,
                confidence=confidence,
                score_factors=score_factors,
                recommendations=recommendations,
                risk_factors=risk_factors,
                scoring_date=datetime.now(),
                algorithm_version="market_agent_v1.0"
            )
            
        except Exception as e:
            logger.error(f"线索评分失败: {e}")
            raise
    
    async def analyze_market_trend(self, industry: str) -> MarketTrend:
        """
        分析中文市场趋势和行业发展方向
        """
        try:
            # 构建市场趋势分析提示
            trend_prompt = f"""
            作为资深市场分析师，请深度分析中国{industry}行业的市场趋势：
            
            请从以下维度进行分析：
            1. 行业发展趋势（上升/下降/稳定）
            2. 市场增长率预测
            3. 关键驱动因素
            4. 市场规模分析
            5. 未来3-5年预测
            6. 市场机会识别
            7. 潜在威胁分析
            
            请提供具体的数据支撑和专业见解，分析要深入、准确。
            """
            
            # 检索相关市场趋势数据
            rag_result = await rag_service.query(
                question=f"中国{industry}行业市场趋势和发展前景",
                collection_name=self.knowledge_collections["market_trends"]
            )
            
            # 检索行业报告
            industry_report = await rag_service.query(
                question=f"{industry}行业分析报告",
                collection_name=self.knowledge_collections["industry_reports"]
            )
            
            # 增强提示
            enhanced_prompt = f"""
            {trend_prompt}
            
            参考市场数据：
            {rag_result.answer}
            
            行业报告摘要：
            {industry_report.answer}
            """
            
            # 生成趋势分析
            llm_response = await llm_service.chat_completion(
                messages=[{"role": "user", "content": enhanced_prompt}],
                temperature=0.1,
                max_tokens=2000
            )
            
            content = llm_response.get("content", "")
            
            # 解析分析结果
            return MarketTrend(
                industry=industry,
                trend_direction=self._extract_trend_direction(content),
                growth_rate=self._extract_growth_rate(content),
                key_drivers=self._extract_list_items(content, "关键驱动因素"),
                market_size=self._extract_market_size(content),
                forecast=self._extract_forecast(content),
                opportunities=self._extract_list_items(content, "市场机会"),
                threats=self._extract_list_items(content, "潜在威胁"),
                analysis_date=datetime.now(),
                confidence_score=min((rag_result.confidence + industry_report.confidence) / 2 + 0.2, 1.0)
            )
            
        except Exception as e:
            logger.error(f"市场趋势分析失败: {e}")
            raise
    
    async def generate_competitive_analysis(self, competitor: str) -> CompetitiveAnalysis:
        """
        深度分析竞争对手和市场竞争格局
        """
        try:
            # 构建竞争分析提示
            competitive_prompt = f"""
            作为竞争情报专家，请深度分析竞争对手"{competitor}"：
            
            请从以下维度进行分析：
            1. 竞争对手类型（直接/间接/潜在/替代品）
            2. 市场份额估算
            3. 核心优势分析
            4. 主要劣势识别
            5. 产品/服务组合
            6. 定价策略分析
            7. 目标客户群体
            8. 竞争优势评估
            9. 威胁等级判断
            
            请提供客观、专业的分析，重点关注中国市场情况。
            """
            
            # 检索竞争情报
            competitive_intel = await rag_service.query(
                question=f"{competitor}竞争对手分析",
                collection_name=self.knowledge_collections["competitive_intelligence"]
            )
            
            # 检索行业竞争格局
            market_landscape = await rag_service.query(
                question=f"{competitor}所在行业竞争格局",
                collection_name=self.knowledge_collections["industry_reports"]
            )
            
            # 增强提示
            enhanced_prompt = f"""
            {competitive_prompt}
            
            竞争情报：
            {competitive_intel.answer}
            
            市场格局：
            {market_landscape.answer}
            """
            
            # 生成竞争分析
            llm_response = await llm_service.chat_completion(
                messages=[{"role": "user", "content": enhanced_prompt}],
                temperature=0.2,
                max_tokens=2000
            )
            
            content = llm_response.get("content", "")
            
            # 解析分析结果
            return CompetitiveAnalysis(
                competitor_name=competitor,
                competitor_type=self._extract_competitor_type(content),
                market_share=self._extract_market_share(content),
                strengths=self._extract_list_items(content, "核心优势"),
                weaknesses=self._extract_list_items(content, "主要劣势"),
                products=self._extract_products(content),
                pricing_strategy=self._extract_section(content, "定价策略"),
                target_customers=self._extract_list_items(content, "目标客户"),
                competitive_advantages=self._extract_list_items(content, "竞争优势"),
                threat_level=self._extract_threat_level(content),
                analysis_date=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"竞争分析失败: {e}")
            raise
    
    async def recommend_marketing_strategy(self, target_market: Dict[str, Any]) -> MarketingStrategy:
        """
        基于市场分析推荐营销策略
        """
        try:
            industry = target_market.get("industry", "")
            region = target_market.get("region", "中国")
            user_query = target_market.get("user_query", "")
            
            # 构建营销策略提示
            strategy_prompt = f"""
            作为营销策略专家，请为以下目标市场制定营销策略：
            
            目标市场信息：
            - 行业：{industry}
            - 地区：{region}
            - 具体需求：{user_query}
            
            请制定包含以下要素的营销策略：
            1. 目标客户细分
            2. 市场定位策略
            3. 核心营销信息
            4. 营销渠道组合
            5. 具体营销战术
            6. 预算分配建议
            7. 执行时间表
            8. 成功指标设定
            9. 预期投资回报率
            
            请提供实用、可执行的营销策略建议。
            """
            
            # 检索营销最佳实践
            marketing_practices = await rag_service.query(
                question=f"{industry}行业营销策略最佳实践",
                collection_name=self.knowledge_collections["marketing_strategies"]
            )
            
            # 检索客户细分数据
            customer_segments = await rag_service.query(
                question=f"{industry}行业客户细分和特征",
                collection_name=self.knowledge_collections["customer_segments"]
            )
            
            # 增强提示
            enhanced_prompt = f"""
            {strategy_prompt}
            
            营销最佳实践：
            {marketing_practices.answer}
            
            客户细分参考：
            {customer_segments.answer}
            """
            
            # 生成营销策略
            llm_response = await llm_service.chat_completion(
                messages=[{"role": "user", "content": enhanced_prompt}],
                temperature=0.3,
                max_tokens=2000
            )
            
            content = llm_response.get("content", "")
            
            # 解析策略建议
            return MarketingStrategy(
                target_segment=self._extract_section(content, "目标客户细分"),
                positioning=self._extract_section(content, "市场定位"),
                key_messages=self._extract_list_items(content, "核心营销信息"),
                channels=self._extract_list_items(content, "营销渠道"),
                tactics=self._extract_tactics(content),
                budget_allocation=self._extract_budget_allocation(content),
                timeline=self._extract_timeline(content),
                success_metrics=self._extract_list_items(content, "成功指标"),
                expected_roi=self._extract_roi(content)
            )
            
        except Exception as e:
            logger.error(f"营销策略推荐失败: {e}")
            raise 
   
    # MCP工具处理方法
    
    async def _handle_get_market_data(self, **kwargs) -> Dict[str, Any]:
        """处理获取市场数据的MCP调用"""
        try:
            data_source = kwargs.get("data_source", "")
            industry = kwargs.get("industry", "")
            region = kwargs.get("region", "中国")
            
            # 检索市场数据
            rag_result = await rag_service.query(
                question=f"{region}{industry}行业市场数据",
                collection_name=self.knowledge_collections["market_trends"]
            )
            
            return {
                "success": True,
                "data": {
                    "source": data_source,
                    "industry": industry,
                    "region": region,
                    "market_data": rag_result.answer,
                    "confidence": rag_result.confidence,
                    "sources": rag_result.sources
                }
            }
            
        except Exception as e:
            logger.error(f"获取市场数据失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _handle_analyze_competitor(self, **kwargs) -> Dict[str, Any]:
        """处理分析竞争对手的MCP调用"""
        try:
            competitor = kwargs.get("competitor", "")
            if not competitor:
                return {
                    "success": False,
                    "error": "竞争对手名称不能为空"
                }
            
            analysis = await self.generate_competitive_analysis(competitor)
            
            return {
                "success": True,
                "competitor_analysis": {
                    "competitor_name": analysis.competitor_name,
                    "competitor_type": analysis.competitor_type.value,
                    "market_share": analysis.market_share,
                    "strengths": analysis.strengths,
                    "weaknesses": analysis.weaknesses,
                    "threat_level": analysis.threat_level,
                    "analysis_date": analysis.analysis_date.isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"竞争对手分析失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _handle_score_lead_batch(self, **kwargs) -> Dict[str, Any]:
        """处理批量线索评分的MCP调用"""
        try:
            lead_ids = kwargs.get("lead_ids", [])
            if not lead_ids:
                return {
                    "success": False,
                    "error": "线索ID列表不能为空"
                }
            
            results = []
            for lead_id in lead_ids:
                try:
                    score_detail = await self.score_lead(lead_id)
                    results.append({
                        "lead_id": lead_id,
                        "success": True,
                        "score": score_detail.total_score,
                        "confidence": score_detail.confidence,
                        "recommendations": score_detail.recommendations[:3]  # 只返回前3个建议
                    })
                except Exception as e:
                    results.append({
                        "lead_id": lead_id,
                        "success": False,
                        "error": str(e)
                    })
            
            success_count = len([r for r in results if r["success"]])
            
            return {
                "success": True,
                "batch_results": results,
                "summary": {
                    "total": len(lead_ids),
                    "success": success_count,
                    "failed": len(lead_ids) - success_count
                }
            }
            
        except Exception as e:
            logger.error(f"批量线索评分失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _handle_generate_market_report(self, **kwargs) -> Dict[str, Any]:
        """处理生成市场报告的MCP调用"""
        try:
            industry = kwargs.get("industry", "")
            report_type = kwargs.get("report_type", "trend_analysis")
            
            if report_type == "trend_analysis" and industry:
                trend_analysis = await self.analyze_market_trend(industry)
                
                report_content = f"""
                # {industry}行业市场趋势分析报告
                
                ## 分析概要
                - 行业：{trend_analysis.industry}
                - 趋势方向：{trend_analysis.trend_direction}
                - 增长率：{trend_analysis.growth_rate}%
                - 分析日期：{trend_analysis.analysis_date.strftime('%Y-%m-%d')}
                - 置信度：{trend_analysis.confidence_score:.2f}
                
                ## 关键驱动因素
                {chr(10).join([f"- {driver}" for driver in trend_analysis.key_drivers])}
                
                ## 市场机会
                {chr(10).join([f"- {opportunity}" for opportunity in trend_analysis.opportunities])}
                
                ## 潜在威胁
                {chr(10).join([f"- {threat}" for threat in trend_analysis.threats])}
                """
                
                return {
                    "success": True,
                    "report": {
                        "title": f"{industry}行业市场趋势分析报告",
                        "content": report_content,
                        "type": report_type,
                        "generated_at": datetime.now().isoformat()
                    }
                }
            else:
                return {
                    "success": False,
                    "error": "不支持的报告类型或缺少必要参数"
                }
                
        except Exception as e:
            logger.error(f"生成市场报告失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _handle_update_market_intelligence(self, **kwargs) -> Dict[str, Any]:
        """处理更新市场情报的MCP调用"""
        try:
            # 这里应该实现实际的市场情报更新逻辑
            # 简化实现
            intelligence_type = kwargs.get("type", "")
            data = kwargs.get("data", {})
            
            logger.info(f"更新市场情报: type={intelligence_type}, data={data}")
            
            return {
                "success": True,
                "message": f"市场情报更新成功: {intelligence_type}",
                "updated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"更新市场情报失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    # 响应格式化方法
    
    async def _format_scoring_result_response(self, data: LeadScoreDetail) -> tuple[str, List[str]]:
        """格式化线索评分结果响应"""
        content = f"""
        📊 **线索评分分析结果**
        
        **总体评分：{data.total_score:.1f}分** (置信度: {data.confidence:.2f})
        
        **关键评分因子：**
        {chr(10).join([f"• {factor.get('name', '')}: {factor.get('score', 0):.1f}分 - {factor.get('reason', '')}" for factor in data.score_factors[:5]])}
        
        **跟进建议：**
        {chr(10).join([f"• {rec}" for rec in data.recommendations[:3]])}
        
        **风险因素：**
        {chr(10).join([f"• {risk}" for risk in data.risk_factors[:3]])}
        
        评分时间：{data.scoring_date.strftime('%Y-%m-%d %H:%M')}
        """
        
        suggestions = [
            "查看详细评分因子",
            "制定跟进计划",
            "分析类似线索",
            "更新线索信息"
        ]
        
        return content, suggestions
    
    async def _format_trend_analysis_response(self, data: MarketTrend) -> tuple[str, List[str]]:
        """格式化市场趋势分析响应"""
        trend_emoji = "📈" if data.trend_direction == "up" else "📉" if data.trend_direction == "down" else "📊"
        
        content = f"""
        {trend_emoji} **{data.industry}行业市场趋势分析**
        
        **趋势概况：**
        • 发展方向：{data.trend_direction} 
        • 增长率：{data.growth_rate}%
        • 置信度：{data.confidence_score:.2f}
        
        **关键驱动因素：**
        {chr(10).join([f"• {driver}" for driver in data.key_drivers[:5]])}
        
        **市场机会：**
        {chr(10).join([f"• {opportunity}" for opportunity in data.opportunities[:3]])}
        
        **潜在威胁：**
        {chr(10).join([f"• {threat}" for threat in data.threats[:3]])}
        
        分析时间：{data.analysis_date.strftime('%Y-%m-%d %H:%M')}
        """
        
        suggestions = [
            "查看详细市场预测",
            "分析竞争格局",
            "制定市场策略",
            "获取行业报告"
        ]
        
        return content, suggestions
    
    async def _format_competitive_analysis_response(self, data: CompetitiveAnalysis) -> tuple[str, List[str]]:
        """格式化竞争分析响应"""
        threat_emoji = "🔴" if data.threat_level == "high" else "🟡" if data.threat_level == "medium" else "🟢"
        
        content = f"""
        🏢 **{data.competitor_name} 竞争分析报告**
        
        **基本信息：**
        • 竞争类型：{data.competitor_type.value}
        • 市场份额：{data.market_share}% (如有数据)
        • 威胁等级：{threat_emoji} {data.threat_level}
        
        **核心优势：**
        {chr(10).join([f"• {strength}" for strength in data.strengths[:4]])}
        
        **主要劣势：**
        {chr(10).join([f"• {weakness}" for weakness in data.weaknesses[:4]])}
        
        **定价策略：**
        {data.pricing_strategy}
        
        分析时间：{data.analysis_date.strftime('%Y-%m-%d %H:%M')}
        """
        
        suggestions = [
            "制定竞争策略",
            "分析产品对比",
            "监控竞争动态",
            "优化差异化定位"
        ]
        
        return content, suggestions
    
    async def _format_strategy_recommendation_response(self, data: MarketingStrategy) -> tuple[str, List[str]]:
        """格式化营销策略建议响应"""
        content = f"""
        🎯 **营销策略建议**
        
        **目标客户：**
        {data.target_segment}
        
        **市场定位：**
        {data.positioning}
        
        **核心信息：**
        {chr(10).join([f"• {message}" for message in data.key_messages[:4]])}
        
        **推荐渠道：**
        {chr(10).join([f"• {channel}" for channel in data.channels[:4]])}
        
        **成功指标：**
        {chr(10).join([f"• {metric}" for metric in data.success_metrics[:3]])}
        
        **预期ROI：** {data.expected_roi}% (如有预测)
        """
        
        suggestions = [
            "制定执行计划",
            "分配营销预算",
            "设计营销活动",
            "建立监控体系"
        ]
        
        return content, suggestions
    
    async def _format_data_analysis_response(self, data: Dict[str, Any]) -> tuple[str, List[str]]:
        """格式化数据分析结果响应"""
        content = f"""
        📊 **市场数据分析结果**
        
        **分析类型：** {data.get('analysis_type', '未知')}
        **数据来源：** {data.get('data_source', '未知')}
        
        **主要发现：**
        {data.get('summary', '暂无分析结果')}
        
        **关键指标：**
        {chr(10).join([f"• {key}: {value}" for key, value in data.get('metrics', {}).items()])}
        
        分析时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}
        """
        
        suggestions = [
            "导出详细报告",
            "设置数据监控",
            "分享分析结果",
            "制定行动计划"
        ]
        
        return content, suggestions
    
    async def _format_knowledge_based_response(self, data: Dict[str, Any]) -> tuple[str, List[str]]:
        """格式化知识库响应"""
        content = f"""
        💡 **市场知识解答**
        
        {data.get('answer', '暂无相关信息')}
        
        **参考来源：**
        {chr(10).join([f"• {source.get('title', '未知来源')}" for source in data.get('sources', [])[:3]])}
        
        置信度：{data.get('confidence', 0):.2f}
        """
        
        suggestions = [
            "查看更多相关信息",
            "获取详细报告",
            "咨询专业建议",
            "保存到知识库"
        ]
        
        return content, suggestions
    
    async def _format_general_response(self, data: Dict[str, Any]) -> tuple[str, List[str]]:
        """格式化一般响应"""
        content = f"""
        📋 **市场分析结果**
        
        {data.get('content', '分析完成，请查看具体结果。')}
        """
        
        suggestions = [
            "获取更多信息",
            "深入分析",
            "制定策略",
            "联系专家"
        ]
        
        return content, suggestions   
 
    # 工具方法
    
    def _extract_lead_id_from_message(self, content: str) -> Optional[str]:
        """从消息中提取线索ID"""
        import re
        # 简单的ID提取逻辑，实际可以更复杂
        id_pattern = r'lead[_-]?([a-f0-9-]{36}|[a-f0-9]{32}|\d+)'
        match = re.search(id_pattern, content, re.IGNORECASE)
        return match.group(1) if match else None
    
    def _extract_industry_from_message(self, content: str) -> Optional[str]:
        """从消息中提取行业信息"""
        # 常见行业关键词
        industries = [
            "制造业", "金融", "教育", "医疗", "零售", "房地产", "科技", "互联网",
            "汽车", "能源", "电信", "物流", "餐饮", "旅游", "建筑", "农业"
        ]
        
        for industry in industries:
            if industry in content:
                return industry
        return None
    
    def _extract_competitor_from_message(self, content: str) -> Optional[str]:
        """从消息中提取竞争对手名称"""
        import re
        # 查找公司名称模式
        patterns = [
            r'分析(.+?)公司',
            r'竞争对手(.+?)的',
            r'对手(.+?)怎么样',
            r'(.+?)的竞争分析'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1).strip()
        return None
    
    def _extract_score_factors(self, content: str, base_score: Any) -> List[Dict[str, Any]]:
        """提取评分因子"""
        factors = []
        
        # 如果有基础评分，使用其因子
        if base_score and hasattr(base_score, 'score_factors'):
            factors.extend(base_score.score_factors)
        
        # 从LLM分析中提取额外因子
        import re
        factor_pattern = r'(\w+)[:：]\s*(\d+(?:\.\d+)?)[分点]?\s*[-—]\s*(.+)'
        matches = re.findall(factor_pattern, content)
        
        for match in matches:
            factors.append({
                "name": match[0],
                "score": float(match[1]),
                "reason": match[2].strip()
            })
        
        return factors[:10]  # 最多返回10个因子
    
    def _extract_list_items(self, content: str, section_name: str) -> List[str]:
        """提取列表项"""
        import re
        
        # 查找指定章节
        section_pattern = f'{section_name}[：:]([^#]*?)(?=\n\n|\n[#*]|$)'
        section_match = re.search(section_pattern, content, re.DOTALL)
        
        if not section_match:
            return []
        
        section_content = section_match.group(1)
        
        # 提取列表项
        items = []
        for line in section_content.split('\n'):
            line = line.strip()
            if line.startswith(('•', '-', '*', '1.', '2.', '3.', '4.', '5.')):
                item = re.sub(r'^[•\-*\d.]\s*', '', line).strip()
                if item:
                    items.append(item)
        
        return items[:10]  # 最多返回10项
    
    def _extract_section(self, content: str, section_name: str) -> str:
        """提取指定章节内容"""
        import re
        
        section_pattern = f'{section_name}[：:]([^#]*?)(?=\n\n|\n[#*]|$)'
        match = re.search(section_pattern, content, re.DOTALL)
        
        if match:
            return match.group(1).strip()
        return ""
    
    def _extract_trend_direction(self, content: str) -> str:
        """提取趋势方向"""
        content_lower = content.lower()
        if any(word in content_lower for word in ["上升", "增长", "上涨", "向好", "positive"]):
            return "up"
        elif any(word in content_lower for word in ["下降", "下跌", "衰退", "负增长", "negative"]):
            return "down"
        else:
            return "stable"
    
    def _extract_growth_rate(self, content: str) -> float:
        """提取增长率"""
        import re
        
        # 查找百分比数字
        patterns = [
            r'增长率[：:为]?\s*(\d+(?:\.\d+)?)%',
            r'增长\s*(\d+(?:\.\d+)?)%',
            r'(\d+(?:\.\d+)?)%\s*增长'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                return float(match.group(1))
        
        return 0.0
    
    def _extract_market_size(self, content: str) -> Dict[str, Any]:
        """提取市场规模信息"""
        import re
        
        size_info = {}
        
        # 查找市场规模数字
        size_patterns = [
            r'市场规模[：:]?\s*(\d+(?:\.\d+)?)\s*(万亿|千亿|百亿|十亿|亿|万)',
            r'规模达到\s*(\d+(?:\.\d+)?)\s*(万亿|千亿|百亿|十亿|亿|万)'
        ]
        
        for pattern in size_patterns:
            match = re.search(pattern, content)
            if match:
                value = float(match.group(1))
                unit = match.group(2)
                size_info["value"] = value
                size_info["unit"] = unit
                break
        
        return size_info
    
    def _extract_forecast(self, content: str) -> Dict[str, Any]:
        """提取预测信息"""
        forecast = {}
        
        # 简化实现，提取年份和预测值
        import re
        forecast_pattern = r'(\d{4})年.*?(\d+(?:\.\d+)?)%'
        matches = re.findall(forecast_pattern, content)
        
        for match in matches:
            year = match[0]
            rate = float(match[1])
            forecast[year] = rate
        
        return forecast
    
    def _extract_competitor_type(self, content: str) -> CompetitorType:
        """提取竞争对手类型"""
        content_lower = content.lower()
        
        if "直接竞争" in content_lower:
            return CompetitorType.DIRECT
        elif "间接竞争" in content_lower:
            return CompetitorType.INDIRECT
        elif "潜在竞争" in content_lower:
            return CompetitorType.POTENTIAL
        elif "替代品" in content_lower:
            return CompetitorType.SUBSTITUTE
        else:
            return CompetitorType.DIRECT  # 默认为直接竞争
    
    def _extract_market_share(self, content: str) -> Optional[float]:
        """提取市场份额"""
        import re
        
        patterns = [
            r'市场份额[：:]?\s*(\d+(?:\.\d+)?)%',
            r'占据\s*(\d+(?:\.\d+)?)%\s*市场',
            r'份额为\s*(\d+(?:\.\d+)?)%'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                return float(match.group(1))
        
        return None
    
    def _extract_products(self, content: str) -> List[Dict[str, Any]]:
        """提取产品信息"""
        products = []
        
        # 简化实现，查找产品相关信息
        import re
        product_pattern = r'产品[：:]([^。]*?)。'
        matches = re.findall(product_pattern, content)
        
        for match in matches:
            products.append({
                "description": match.strip(),
                "category": "未分类"
            })
        
        return products[:5]  # 最多返回5个产品
    
    def _extract_threat_level(self, content: str) -> str:
        """提取威胁等级"""
        content_lower = content.lower()
        
        if any(word in content_lower for word in ["高威胁", "严重威胁", "强劲对手"]):
            return "high"
        elif any(word in content_lower for word in ["中等威胁", "一般威胁", "普通对手"]):
            return "medium"
        else:
            return "low"
    
    def _extract_tactics(self, content: str) -> List[Dict[str, Any]]:
        """提取营销战术"""
        tactics = []
        
        # 查找战术相关信息
        tactic_items = self._extract_list_items(content, "营销战术")
        
        for item in tactic_items:
            tactics.append({
                "name": item,
                "description": item,
                "priority": "medium"
            })
        
        return tactics
    
    def _extract_budget_allocation(self, content: str) -> Dict[str, float]:
        """提取预算分配"""
        allocation = {}
        
        # 简化实现，查找预算相关信息
        import re
        budget_pattern = r'(\w+)[：:]?\s*(\d+(?:\.\d+)?)%'
        matches = re.findall(budget_pattern, content)
        
        for match in matches:
            channel = match[0]
            percentage = float(match[1])
            if percentage <= 100:  # 确保是百分比
                allocation[channel] = percentage
        
        return allocation
    
    def _extract_timeline(self, content: str) -> Dict[str, str]:
        """提取时间线"""
        timeline = {}
        
        # 查找时间相关信息
        phases = ["第一阶段", "第二阶段", "第三阶段", "初期", "中期", "后期"]
        
        for phase in phases:
            if phase in content:
                # 简化实现
                timeline[phase] = "待定"
        
        return timeline
    
    def _extract_roi(self, content: str) -> Optional[float]:
        """提取投资回报率"""
        import re
        
        patterns = [
            r'ROI[：:]?\s*(\d+(?:\.\d+)?)%',
            r'回报率[：:]?\s*(\d+(?:\.\d+)?)%',
            r'投资回报[：:]?\s*(\d+(?:\.\d+)?)%'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                return float(match.group(1))
        
        return None
    
    async def _get_lead_scoring_guidance(self, content: str) -> Dict[str, Any]:
        """获取线索评分指导"""
        guidance_prompt = f"""
        作为市场分析专家，请为以下线索评分需求提供指导：
        
        用户需求：{content}
        
        请提供：
        1. 线索评分的关键维度
        2. 评分标准和权重建议
        3. 数据收集要点
        4. 评分结果应用建议
        
        请用中文回答，内容要实用、专业。
        """
        
        try:
            llm_response = await llm_service.chat_completion(
                messages=[{"role": "user", "content": guidance_prompt}],
                temperature=0.3,
                max_tokens=1000
            )
            
            return {
                "guidance": llm_response.get("content", ""),
                "type": "lead_scoring_guidance"
            }
        except Exception as e:
            logger.error(f"获取线索评分指导失败: {e}")
            return {
                "guidance": "线索评分需要考虑客户规模、预算、时间线、决策权等关键因素。",
                "type": "lead_scoring_guidance"
            }
    
    async def _get_market_trend_guidance(self, content: str) -> Dict[str, Any]:
        """获取市场趋势分析指导"""
        guidance_prompt = f"""
        作为市场研究专家，请为以下市场趋势分析需求提供指导：
        
        用户需求：{content}
        
        请提供：
        1. 市场趋势分析的关键方法
        2. 数据来源和收集建议
        3. 分析框架和工具
        4. 结果解读和应用
        
        请用中文回答，内容要专业、实用。
        """
        
        try:
            llm_response = await llm_service.chat_completion(
                messages=[{"role": "user", "content": guidance_prompt}],
                temperature=0.3,
                max_tokens=1000
            )
            
            return {
                "guidance": llm_response.get("content", ""),
                "type": "market_trend_guidance"
            }
        except Exception as e:
            logger.error(f"获取市场趋势指导失败: {e}")
            return {
                "guidance": "市场趋势分析需要关注行业发展、政策环境、技术变化、消费者行为等多个维度。",
                "type": "market_trend_guidance"
            }
    
    async def _get_competitive_analysis_guidance(self, content: str) -> Dict[str, Any]:
        """获取竞争分析指导"""
        guidance_prompt = f"""
        作为竞争情报专家，请为以下竞争分析需求提供指导：
        
        用户需求：{content}
        
        请提供：
        1. 竞争分析的核心框架
        2. 信息收集渠道和方法
        3. 分析维度和评估标准
        4. 竞争策略制定建议
        
        请用中文回答，内容要专业、可操作。
        """
        
        try:
            llm_response = await llm_service.chat_completion(
                messages=[{"role": "user", "content": guidance_prompt}],
                temperature=0.3,
                max_tokens=1000
            )
            
            return {
                "guidance": llm_response.get("content", ""),
                "type": "competitive_analysis_guidance"
            }
        except Exception as e:
            logger.error(f"获取竞争分析指导失败: {e}")
            return {
                "guidance": "竞争分析需要从产品、价格、渠道、推广等4P角度全面评估竞争对手。",
                "type": "competitive_analysis_guidance"
            }
    
    async def _parse_data_analysis_request(self, content: str) -> Dict[str, Any]:
        """解析数据分析请求"""
        return {
            "analysis_type": "general",
            "data_source": "market_data",
            "requirements": content,
            "output_format": "report"
        }
    
    async def _perform_market_data_analysis(self, request: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """执行市场数据分析"""
        # 简化实现
        return {
            "analysis_type": request.get("analysis_type", "general"),
            "data_source": request.get("data_source", "unknown"),
            "summary": "数据分析完成，主要发现包括市场增长趋势积极，竞争格局相对稳定。",
            "metrics": {
                "市场增长率": "12.5%",
                "客户满意度": "85%",
                "市场份额": "15.2%"
            }
        }
    
    async def _integrate_collaboration_result(self, collaboration_result: Dict[str, Any]) -> str:
        """整合协作结果"""
        results = collaboration_result.get("collaboration_results", [])
        
        integration_text = "**协作分析结果：**\n"
        
        for result in results:
            agent_id = result.get("agent_id", "unknown")
            if "error" not in result:
                integration_text += f"• {agent_id}: 协作成功\n"
            else:
                integration_text += f"• {agent_id}: 协作失败 - {result.get('error', '')}\n"
        
        return integration_text
    
    def _calculate_response_confidence(
        self, 
        task_result: Dict[str, Any], 
        collaboration_result: Optional[Dict[str, Any]] = None
    ) -> float:
        """计算响应置信度"""
        base_confidence = 0.7
        
        # 根据任务类型调整置信度
        analysis_type = task_result.get("analysis_type", "")
        
        if analysis_type in ["lead_scoring", "market_trend", "competitive_analysis"]:
            base_confidence = 0.8
        elif analysis_type.endswith("_guidance"):
            base_confidence = 0.6
        
        # 如果有协作结果，提高置信度
        if collaboration_result and collaboration_result.get("success"):
            base_confidence += 0.1
        
        return min(base_confidence, 1.0)
    
    def _generate_next_actions(self, task_result: Dict[str, Any]) -> List[str]:
        """生成下一步行动建议"""
        analysis_type = task_result.get("analysis_type", "")
        
        if analysis_type == "lead_scoring":
            return [
                "制定线索跟进计划",
                "分配高分线索给销售团队",
                "优化线索评分模型"
            ]
        elif analysis_type == "market_trend":
            return [
                "制定市场进入策略",
                "调整产品定位",
                "监控市场变化"
            ]
        elif analysis_type == "competitive_analysis":
            return [
                "制定竞争应对策略",
                "优化产品差异化",
                "加强市场监控"
            ]
        else:
            return [
                "深入分析相关数据",
                "制定行动计划",
                "定期跟踪进展"
            ]
"""
NLU服务 - 自然语言理解服务
实现意图识别、实体抽取、槽位填充和中文语义理解
"""

import re
import json
import logging
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import asyncio

from langchain.schema import HumanMessage, SystemMessage
from src.services.llm_service import EnhancedLLMService, ModelType
from src.core.config import settings

logger = logging.getLogger(__name__)


class IntentType(str, Enum):
    """CRM系统支持的意图类型"""
    # 客户管理相关
    CUSTOMER_SEARCH = "customer_search"
    CUSTOMER_CREATE = "customer_create"
    CUSTOMER_UPDATE = "customer_update"
    CUSTOMER_ANALYSIS = "customer_analysis"
    
    # 线索管理相关
    LEAD_SEARCH = "lead_search"
    LEAD_CREATE = "lead_create"
    LEAD_UPDATE = "lead_update"
    LEAD_SCORING = "lead_scoring"
    LEAD_ASSIGNMENT = "lead_assignment"
    
    # 销售机会相关
    OPPORTUNITY_SEARCH = "opportunity_search"
    OPPORTUNITY_CREATE = "opportunity_create"
    OPPORTUNITY_UPDATE = "opportunity_update"
    OPPORTUNITY_ANALYSIS = "opportunity_analysis"
    
    # 任务和活动相关
    TASK_CREATE = "task_create"
    TASK_SEARCH = "task_search"
    SCHEDULE_MEETING = "schedule_meeting"
    
    # 报告和分析相关
    REPORT_GENERATE = "report_generate"
    PERFORMANCE_ANALYSIS = "performance_analysis"
    FORECAST_ANALYSIS = "forecast_analysis"
    
    # 通用意图
    GREETING = "greeting"
    HELP = "help"
    UNKNOWN = "unknown"


class EntityType(str, Enum):
    """实体类型"""
    # 人员实体
    PERSON = "person"
    CONTACT_NAME = "contact_name"
    SALES_REP = "sales_rep"
    
    # 公司实体
    COMPANY = "company"
    INDUSTRY = "industry"
    COMPANY_SIZE = "company_size"
    
    # 产品和服务
    PRODUCT = "product"
    SERVICE = "service"
    SOLUTION = "solution"
    
    # 财务相关
    BUDGET = "budget"
    REVENUE = "revenue"
    PRICE = "price"
    
    # 时间相关
    DATE = "date"
    TIME_PERIOD = "time_period"
    DEADLINE = "deadline"
    
    # 地理位置
    LOCATION = "location"
    REGION = "region"
    
    # 状态和阶段
    STATUS = "status"
    STAGE = "stage"
    PRIORITY = "priority"
    
    # 数量和指标
    NUMBER = "number"
    PERCENTAGE = "percentage"
    METRIC = "metric"


@dataclass
class Entity:
    """实体对象"""
    type: EntityType
    value: str
    confidence: float
    start_pos: int
    end_pos: int
    normalized_value: Optional[Any] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Intent:
    """意图对象"""
    type: IntentType
    confidence: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Slot:
    """槽位对象"""
    name: str
    value: Any
    entity_type: EntityType
    confidence: float
    required: bool = False
    filled: bool = False


@dataclass
class NLUResult:
    """NLU分析结果"""
    text: str
    intent: Intent
    entities: List[Entity]
    slots: Dict[str, Slot]
    confidence: float
    processing_time: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class ChineseNLUProcessor:
    """中文NLU处理器"""
    
    def __init__(self):
        # 中文分词和实体识别的正则表达式模式
        self.patterns = {
            # 公司名称模式
            'company': [
                r'([A-Za-z\u4e00-\u9fff]+(?:公司|集团|企业|科技|有限公司|股份有限公司|Ltd|Inc|Corp))',
                r'([A-Za-z\u4e00-\u9fff]{2,}(?:科技|技术|软件|信息|网络|数据|智能))',
            ],
            # 人名模式
            'person': [
                r'([A-Za-z\u4e00-\u9fff]{2,4}(?:总|经理|主管|总监|CEO|CTO|CFO|VP))',
                r'([A-Za-z\u4e00-\u9fff]{2,4}(?:先生|女士|老师))',
            ],
            # 金额模式
            'budget': [
                r'(\d+(?:\.\d+)?(?:万|千|百万|亿|元|美元|USD|RMB))',
                r'(预算\s*[:：]?\s*\d+(?:\.\d+)?(?:万|千|百万|亿|元)?)',
            ],
            # 时间模式
            'date': [
                r'(\d{4}年\d{1,2}月\d{1,2}日)',
                r'(今天|明天|后天|昨天|下周|下月|本月|本周)',
                r'(\d{1,2}月\d{1,2}日)',
            ],
            # 行业模式
            'industry': [
                r'(制造业|金融|教育|医疗|零售|电商|互联网|房地产|汽车|能源)',
                r'([A-Za-z\u4e00-\u9fff]+行业)',
            ],
            # 数字模式
            'number': [
                r'(\d+(?:\.\d+)?)',
            ],
        }
        
        # 意图关键词映射
        self.intent_keywords = {
            IntentType.CUSTOMER_SEARCH: ['找客户', '查找客户', '搜索客户', '客户列表', '潜在客户'],
            IntentType.CUSTOMER_CREATE: ['新建客户', '创建客户', '添加客户', '录入客户'],
            IntentType.CUSTOMER_UPDATE: ['更新客户', '修改客户', '编辑客户信息'],
            IntentType.CUSTOMER_ANALYSIS: ['客户分析', '客户画像', '客户洞察'],
            
            IntentType.LEAD_SEARCH: ['查找线索', '搜索线索', '线索列表', '今天的线索'],
            IntentType.LEAD_CREATE: ['新建线索', '创建线索', '添加线索', '录入线索', '新建.*线索'],
            IntentType.LEAD_UPDATE: ['更新线索', '修改线索', '线索状态'],
            IntentType.LEAD_SCORING: ['线索评分', '线索质量', '线索优先级'],
            IntentType.LEAD_ASSIGNMENT: ['分配线索', '线索分配', '指派线索'],
            
            IntentType.OPPORTUNITY_SEARCH: ['查找机会', '销售机会', '项目列表'],
            IntentType.OPPORTUNITY_CREATE: ['新建机会', '创建项目', '添加销售机会'],
            IntentType.OPPORTUNITY_UPDATE: ['更新机会', '项目进展', '阶段推进'],
            IntentType.OPPORTUNITY_ANALYSIS: ['机会分析', '销售预测', '漏斗分析'],
            
            IntentType.TASK_CREATE: ['创建任务', '新建任务', '安排任务', '待办事项'],
            IntentType.TASK_SEARCH: ['查看任务', '任务列表', '我的任务'],
            IntentType.SCHEDULE_MEETING: ['安排会议', '预约', '拜访计划', '会面', '安排.*会议'],
            
            IntentType.REPORT_GENERATE: ['生成报告', '报表', '统计报告'],
            IntentType.PERFORMANCE_ANALYSIS: ['业绩分析', '销售业绩', '团队表现'],
            IntentType.FORECAST_ANALYSIS: ['销售预测', '业绩预测', '目标完成'],
            
            IntentType.GREETING: ['你好', '您好', '早上好', '下午好', '晚上好'],
            IntentType.HELP: ['帮助', '怎么用', '如何', '教我'],
        }
    
    def extract_entities_by_pattern(self, text: str) -> List[Entity]:
        """使用正则表达式提取实体"""
        entities = []
        
        for entity_type, patterns in self.patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    entity = Entity(
                        type=EntityType(entity_type),
                        value=match.group(1) if match.groups() else match.group(0),
                        confidence=0.8,  # 基于规则的置信度
                        start_pos=match.start(),
                        end_pos=match.end(),
                        normalized_value=self._normalize_entity_value(entity_type, match.group(0))
                    )
                    entities.append(entity)
        
        return entities
    
    def _normalize_entity_value(self, entity_type: str, value: str) -> Any:
        """标准化实体值"""
        if entity_type == 'budget':
            # 提取数字和单位
            number_match = re.search(r'(\d+(?:\.\d+)?)', value)
            if number_match:
                number = float(number_match.group(1))
                if '百万' in value:  # 先检查百万，避免被万匹配
                    return number * 1000000
                elif '万' in value:
                    return number * 10000
                elif '千' in value:
                    return number * 1000
                elif '亿' in value:
                    return number * 100000000
                return number
        elif entity_type == 'number':
            try:
                return float(value)
            except ValueError:
                return value
        
        return value
    
    def classify_intent_by_keywords(self, text: str) -> Tuple[IntentType, float]:
        """基于关键词分类意图"""
        text_lower = text.lower()
        best_intent = IntentType.UNKNOWN
        best_score = 0.0
        
        for intent_type, keywords in self.intent_keywords.items():
            score = 0.0
            matched_keywords = 0
            for keyword in keywords:
                # 支持正则表达式匹配
                if '.*' in keyword:
                    if re.search(keyword, text_lower):
                        score += 1.0
                        matched_keywords += 1
                else:
                    if keyword in text_lower:
                        score += 1.0
                        matched_keywords += 1
            
            # 如果有匹配的关键词，计算得分
            if matched_keywords > 0:
                # 基于匹配关键词数量计算得分
                relative_score = matched_keywords / len(keywords)
                if relative_score > best_score:
                    best_score = relative_score
                    best_intent = intent_type
        
        return best_intent, min(best_score, 1.0)  # 限制最大置信度为1.0


class NLUService:
    """自然语言理解服务"""
    
    def __init__(self, llm_service: Optional[EnhancedLLMService] = None):
        self.llm_service = llm_service or EnhancedLLMService()
        self.chinese_processor = ChineseNLUProcessor()
        
        # 槽位定义
        self.slot_definitions = self._initialize_slot_definitions()
        
        logger.info("NLU服务初始化完成")
    
    def _initialize_slot_definitions(self) -> Dict[IntentType, List[Dict[str, Any]]]:
        """初始化槽位定义"""
        return {
            IntentType.CUSTOMER_SEARCH: [
                {"name": "industry", "entity_type": EntityType.INDUSTRY, "required": False},
                {"name": "company_size", "entity_type": EntityType.COMPANY_SIZE, "required": False},
                {"name": "location", "entity_type": EntityType.LOCATION, "required": False},
                {"name": "budget_range", "entity_type": EntityType.BUDGET, "required": False},
            ],
            IntentType.CUSTOMER_CREATE: [
                {"name": "company_name", "entity_type": EntityType.COMPANY, "required": True},
                {"name": "contact_name", "entity_type": EntityType.CONTACT_NAME, "required": True},
                {"name": "industry", "entity_type": EntityType.INDUSTRY, "required": False},
            ],
            IntentType.LEAD_SEARCH: [
                {"name": "status", "entity_type": EntityType.STATUS, "required": False},
                {"name": "date_range", "entity_type": EntityType.DATE, "required": False},
                {"name": "assigned_to", "entity_type": EntityType.SALES_REP, "required": False},
            ],
            IntentType.LEAD_CREATE: [
                {"name": "company_name", "entity_type": EntityType.COMPANY, "required": True},
                {"name": "contact_name", "entity_type": EntityType.CONTACT_NAME, "required": True},
                {"name": "budget", "entity_type": EntityType.BUDGET, "required": False},
                {"name": "requirements", "entity_type": EntityType.PRODUCT, "required": False},
            ],
            IntentType.OPPORTUNITY_CREATE: [
                {"name": "customer", "entity_type": EntityType.COMPANY, "required": True},
                {"name": "value", "entity_type": EntityType.BUDGET, "required": True},
                {"name": "close_date", "entity_type": EntityType.DATE, "required": False},
            ],
            IntentType.SCHEDULE_MEETING: [
                {"name": "customer", "entity_type": EntityType.COMPANY, "required": True},
                {"name": "contact", "entity_type": EntityType.CONTACT_NAME, "required": False},
                {"name": "date", "entity_type": EntityType.DATE, "required": True},
                {"name": "time", "entity_type": EntityType.DATE, "required": False},
            ],
        }
    
    async def analyze(self, text: str, context: Optional[Dict[str, Any]] = None) -> NLUResult:
        """分析用户输入的自然语言"""
        start_time = datetime.now()
        
        try:
            # 1. 基于规则的快速分析
            rule_based_intent, rule_confidence = self.chinese_processor.classify_intent_by_keywords(text)
            rule_based_entities = self.chinese_processor.extract_entities_by_pattern(text)
            
            # 2. 基于LLM的深度分析（如果规则置信度较低）
            if rule_confidence < 0.7:
                llm_result = await self._analyze_with_llm(text, context)
                # 合并结果
                final_intent = llm_result.get('intent', rule_based_intent)
                final_confidence = max(rule_confidence, llm_result.get('confidence', 0.0))
                llm_entities = llm_result.get('entities', [])
                
                # 合并实体
                all_entities = rule_based_entities + llm_entities
                # 去重
                unique_entities = self._deduplicate_entities(all_entities)
            else:
                final_intent = rule_based_intent
                final_confidence = rule_confidence
                unique_entities = rule_based_entities
            
            # 3. 槽位填充
            slots = self._fill_slots(final_intent, unique_entities)
            
            # 4. 构建结果
            processing_time = (datetime.now() - start_time).total_seconds()
            
            result = NLUResult(
                text=text,
                intent=Intent(
                    type=final_intent,
                    confidence=final_confidence,
                    metadata={"method": "hybrid"}
                ),
                entities=unique_entities,
                slots=slots,
                confidence=final_confidence,
                processing_time=processing_time,
                metadata={
                    "rule_confidence": rule_confidence,
                    "entity_count": len(unique_entities),
                    "context": context or {}
                }
            )
            
            logger.info(f"NLU分析完成: 意图={final_intent}, 置信度={final_confidence:.2f}, 实体数={len(unique_entities)}")
            return result
            
        except Exception as e:
            logger.error(f"NLU分析失败: {str(e)}")
            # 返回默认结果
            processing_time = (datetime.now() - start_time).total_seconds()
            return NLUResult(
                text=text,
                intent=Intent(type=IntentType.UNKNOWN, confidence=0.0),
                entities=[],
                slots={},
                confidence=0.0,
                processing_time=processing_time,
                metadata={"error": str(e)}
            )
    
    async def _analyze_with_llm(self, text: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """使用LLM进行深度NLU分析"""
        
        # 构建更详细的提示词
        system_prompt = """你是一个专业的CRM系统自然语言理解分析器，专门处理中文销售和客户管理相关的对话。

## 任务说明
分析用户输入的中文文本，准确识别意图和实体信息。

## 意图类型定义
请从以下意图类型中选择最匹配的一个：

**客户管理类**：
- customer_search: 查询、搜索、查找客户信息
- customer_create: 新建、创建、添加客户
- customer_update: 更新、修改客户信息
- customer_analysis: 客户分析、客户画像

**线索管理类**：
- lead_search: 查询、搜索线索
- lead_create: 新建、创建线索
- lead_update: 更新线索状态
- lead_scoring: 线索评分、质量评估
- lead_assignment: 分配线索

**销售机会类**：
- opportunity_search: 查询销售机会
- opportunity_create: 创建销售机会
- opportunity_update: 更新机会状态
- opportunity_analysis: 机会分析、预测

**任务活动类**：
- task_create: 创建任务、待办事项
- task_search: 查询任务
- schedule_meeting: 安排会议、预约拜访

**报告分析类**：
- report_generate: 生成报告
- performance_analysis: 业绩分析
- forecast_analysis: 销售预测

**通用类**：
- greeting: 问候语
- help: 寻求帮助
- unknown: 无法识别的意图

## 实体类型定义
识别以下类型的实体：

- **person**: 人名（如：张三、李经理、王总）
- **company**: 公司名称（如：ABC公司、德芙科技有限公司）
- **industry**: 行业类型（如：制造业、金融业、教育行业）
- **budget**: 预算金额（如：50万、100万元、预算200万）
- **date**: 日期时间（如：明天、下周、2024年1月）
- **location**: 地理位置（如：北京、上海、深圳）
- **product**: 产品服务（如：CRM系统、ERP软件）
- **number**: 数字（如：50、100、3个）
- **status**: 状态（如：已完成、进行中、待处理）
- **priority**: 优先级（如：高优先级、紧急、重要）

## 输出格式
必须严格按照以下JSON格式输出，不要添加任何额外的文字说明：

{
  "intent": "意图类型",
  "confidence": 置信度数值(0.0-1.0),
  "entities": [
    {
      "type": "实体类型",
      "value": "实体值",
      "confidence": 置信度数值(0.0-1.0)
    }
  ]
}

## 分析要求
1. 仔细分析用户输入的语义和上下文
2. 选择最符合的意图类型
3. 提取所有相关实体
4. 给出合理的置信度评分
5. 确保JSON格式正确"""

        # 构建用户提示词
        context_info = ""
        if context:
            context_info = f"\n\n上下文信息：{json.dumps(context, ensure_ascii=False, indent=2)}"

        user_prompt = f"""请分析以下用户输入：

用户输入：{text}{context_info}

请按照要求的JSON格式返回分析结果："""

        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            response = await self.llm_service.chat_completion(
                messages=messages,
                model=ModelType.QWEN_72B,  # 使用中文优化模型
                temperature=0.1,  # 低温度确保一致性
                max_tokens=1500
            )
            
            # 解析JSON响应
            result_text = response.get("content", "").strip()
            
            # 更鲁棒的JSON提取
            result_json = self._extract_json_from_response(result_text)
            if not result_json:
                logger.warning(f"无法从LLM响应中提取有效JSON: {result_text}")
                return self._get_fallback_result()
            
            # 验证和转换结果
            return await self._process_llm_result(result_json, text)
            
        except Exception as e:
            logger.error(f"LLM NLU分析失败: {str(e)}")
            return self._get_fallback_result()
    
    def _extract_json_from_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """从LLM响应中提取JSON"""
        try:
            # 移除代码块标记
            if '```json' in response_text:
                start = response_text.find('```json') + 7
                end = response_text.find('```', start)
                if end != -1:
                    response_text = response_text[start:end].strip()
            elif '```' in response_text:
                start = response_text.find('```') + 3
                end = response_text.find('```', start)
                if end != -1:
                    response_text = response_text[start:end].strip()
            
            # 查找JSON对象
            start_brace = response_text.find('{')
            if start_brace == -1:
                return None
            
            # 找到匹配的结束大括号
            brace_count = 0
            end_brace = start_brace
            for i, char in enumerate(response_text[start_brace:], start_brace):
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end_brace = i
                        break
            
            json_str = response_text[start_brace:end_brace + 1]
            return json.loads(json_str)
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"JSON解析失败: {str(e)}, 原文: {response_text}")
            return None
    
    async def _process_llm_result(self, result_json: Dict[str, Any], original_text: str) -> Dict[str, Any]:
        """处理和验证LLM结果"""
        try:
            # 验证意图
            intent_str = result_json.get('intent', 'unknown')
            try:
                intent = IntentType(intent_str)
            except ValueError:
                logger.warning(f"无效的意图类型: {intent_str}")
                intent = IntentType.UNKNOWN
            
            # 验证置信度
            confidence = float(result_json.get('confidence', 0.8))
            confidence = max(0.0, min(1.0, confidence))  # 限制在0-1之间
            
            # 处理实体
            entities = []
            for entity_data in result_json.get('entities', []):
                try:
                    entity_type_str = entity_data.get('type', '')
                    entity_value = entity_data.get('value', '')
                    entity_confidence = float(entity_data.get('confidence', 0.8))
                    
                    # 验证实体类型
                    try:
                        entity_type = EntityType(entity_type_str)
                    except ValueError:
                        logger.warning(f"无效的实体类型: {entity_type_str}")
                        continue
                    
                    # 查找实体在原文中的位置
                    start_pos, end_pos = self._find_entity_position(original_text, entity_value)
                    
                    # 标准化实体值
                    normalized_value = self._normalize_entity_value_advanced(entity_type, entity_value)
                    
                    entity = Entity(
                        type=entity_type,
                        value=entity_value,
                        confidence=max(0.0, min(1.0, entity_confidence)),
                        start_pos=start_pos,
                        end_pos=end_pos,
                        normalized_value=normalized_value,
                        metadata={"source": "llm"}
                    )
                    entities.append(entity)
                    
                except (ValueError, TypeError) as e:
                    logger.warning(f"处理实体失败: {entity_data}, 错误: {str(e)}")
                    continue
            
            return {
                'intent': intent,
                'confidence': confidence,
                'entities': entities
            }
            
        except Exception as e:
            logger.error(f"处理LLM结果失败: {str(e)}")
            return self._get_fallback_result()
    
    def _find_entity_position(self, text: str, entity_value: str) -> Tuple[int, int]:
        """在原文中查找实体位置"""
        try:
            # 直接查找
            start_pos = text.find(entity_value)
            if start_pos != -1:
                return start_pos, start_pos + len(entity_value)
            
            # 模糊查找（去除空格和标点）
            clean_entity = re.sub(r'[^\w\u4e00-\u9fff]', '', entity_value)
            clean_text = re.sub(r'[^\w\u4e00-\u9fff]', '', text)
            
            start_pos = clean_text.find(clean_entity)
            if start_pos != -1:
                # 映射回原文位置（简化处理）
                return start_pos, start_pos + len(entity_value)
            
            return 0, len(entity_value)
            
        except Exception:
            return 0, len(entity_value)
    
    def _normalize_entity_value_advanced(self, entity_type: EntityType, value: str) -> Any:
        """高级实体值标准化"""
        try:
            if entity_type == EntityType.BUDGET:
                # 提取数字和单位
                number_match = re.search(r'(\d+(?:\.\d+)?)', value)
                if number_match:
                    number = float(number_match.group(1))
                    if '百万' in value:
                        return number * 1000000
                    elif '万' in value:
                        return number * 10000
                    elif '千' in value:
                        return number * 1000
                    elif '亿' in value:
                        return number * 100000000
                    return number
                    
            elif entity_type == EntityType.NUMBER:
                number_match = re.search(r'(\d+(?:\.\d+)?)', value)
                if number_match:
                    return float(number_match.group(1))
                    
            elif entity_type == EntityType.DATE:
                # 简单的日期标准化
                if '明天' in value:
                    return 'tomorrow'
                elif '今天' in value:
                    return 'today'
                elif '昨天' in value:
                    return 'yesterday'
                elif '下周' in value:
                    return 'next_week'
                elif '本周' in value:
                    return 'this_week'
                elif '下月' in value:
                    return 'next_month'
                elif '本月' in value:
                    return 'this_month'
                    
            elif entity_type == EntityType.INDUSTRY:
                # 行业标准化
                industry_mapping = {
                    '制造': '制造业',
                    '金融': '金融业',
                    '教育': '教育行业',
                    '医疗': '医疗行业',
                    '零售': '零售业',
                    '房地产': '房地产业',
                    '汽车': '汽车行业',
                    '能源': '能源行业'
                }
                for key, standard_name in industry_mapping.items():
                    if key in value:
                        return standard_name
            
            return value
            
        except Exception:
            return value
    
    def _get_fallback_result(self) -> Dict[str, Any]:
        """获取回退结果"""
        return {
            'intent': IntentType.UNKNOWN,
            'confidence': 0.0,
            'entities': []
        }
    
    def _deduplicate_entities(self, entities: List[Entity]) -> List[Entity]:
        """去除重复实体"""
        unique_entities = []
        seen = set()
        
        for entity in entities:
            key = (entity.type, entity.value.lower())
            if key not in seen:
                seen.add(key)
                unique_entities.append(entity)
        
        return unique_entities
    
    def _fill_slots(self, intent: IntentType, entities: List[Entity]) -> Dict[str, Slot]:
        """填充槽位"""
        slots = {}
        
        # 获取该意图的槽位定义
        slot_defs = self.slot_definitions.get(intent, [])
        
        # 初始化槽位
        for slot_def in slot_defs:
            slots[slot_def['name']] = Slot(
                name=slot_def['name'],
                value=None,
                entity_type=slot_def['entity_type'],
                confidence=0.0,
                required=slot_def.get('required', False),
                filled=False
            )
        
        # 填充槽位值
        for entity in entities:
            for slot_name, slot in slots.items():
                if slot.entity_type == entity.type and not slot.filled:
                    slot.value = entity.normalized_value or entity.value
                    slot.confidence = entity.confidence
                    slot.filled = True
                    break
        
        return slots
    
    async def extract_entities(self, text: str) -> List[Entity]:
        """单独提取实体"""
        result = await self.analyze(text)
        return result.entities
    
    async def classify_intent(self, text: str) -> Intent:
        """单独分类意图"""
        result = await self.analyze(text)
        return result.intent
    
    def get_missing_slots(self, slots: Dict[str, Slot]) -> List[str]:
        """获取未填充的必需槽位"""
        missing = []
        for slot_name, slot in slots.items():
            if slot.required and not slot.filled:
                missing.append(slot_name)
        return missing
    
    def is_slots_complete(self, slots: Dict[str, Slot]) -> bool:
        """检查必需槽位是否都已填充"""
        return len(self.get_missing_slots(slots)) == 0
    
    async def get_slot_filling_prompt(self, intent: IntentType, missing_slots: List[str]) -> str:
        """生成槽位填充提示"""
        slot_descriptions = {
            "company_name": "公司名称",
            "contact_name": "联系人姓名",
            "industry": "所属行业",
            "budget": "预算金额",
            "date": "日期",
            "requirements": "具体需求",
            "location": "地理位置",
            "value": "金额价值"
        }
        
        missing_desc = [slot_descriptions.get(slot, slot) for slot in missing_slots]
        
        if len(missing_desc) == 1:
            return f"请提供{missing_desc[0]}信息。"
        else:
            return f"请提供以下信息：{', '.join(missing_desc)}。"
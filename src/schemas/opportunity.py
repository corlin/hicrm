"""
销售机会Pydantic模式
"""

from pydantic import BaseModel, Field, ConfigDict, validator
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum

from src.models.opportunity import OpportunityStatus, OpportunityPriority, StageType


class ProductInfo(BaseModel):
    """产品信息模式"""
    id: str = Field(..., description="产品ID")
    name: str = Field(..., description="产品名称")
    version: Optional[str] = Field(None, description="产品版本")
    quantity: int = Field(1, description="数量", ge=1)
    unit_price: Optional[float] = Field(None, description="单价", ge=0)
    total_price: Optional[float] = Field(None, description="总价", ge=0)
    description: Optional[str] = Field(None, description="产品描述")


class CompetitorInfo(BaseModel):
    """竞争对手信息模式"""
    name: str = Field(..., description="竞争对手名称")
    strengths: List[str] = Field(default_factory=list, description="优势")
    weaknesses: List[str] = Field(default_factory=list, description="劣势")
    market_position: Optional[str] = Field(None, description="市场地位")
    pricing: Optional[float] = Field(None, description="价格", ge=0)
    notes: Optional[str] = Field(None, description="备注")


class StakeholderInfo(BaseModel):
    """利益相关者信息模式"""
    name: str = Field(..., description="姓名")
    title: str = Field(..., description="职位")
    role: str = Field(..., description="角色")
    influence_level: str = Field(..., description="影响力等级")
    decision_power: str = Field(..., description="决策权力")
    contact: Optional[Dict[str, str]] = Field(None, description="联系方式")
    notes: Optional[str] = Field(None, description="备注")


class RiskInfo(BaseModel):
    """风险信息模式"""
    type: str = Field(..., description="风险类型")
    description: str = Field(..., description="风险描述")
    probability: float = Field(..., description="发生概率", ge=0.0, le=1.0)
    impact: str = Field(..., description="影响程度")
    mitigation_plan: Optional[str] = Field(None, description="缓解计划")
    owner: Optional[str] = Field(None, description="负责人")


class NextAction(BaseModel):
    """后续行动模式"""
    action: str = Field(..., description="行动内容")
    assignee: str = Field(..., description="负责人")
    due_date: Optional[datetime] = Field(None, description="截止日期")
    priority: str = Field("medium", description="优先级")
    status: str = Field("pending", description="状态")


class OpportunityStageBase(BaseModel):
    """销售机会阶段基础模式"""
    name: str = Field(..., description="阶段名称", min_length=1, max_length=100)
    description: Optional[str] = Field(None, description="阶段描述")
    stage_type: StageType = Field(..., description="阶段类型")
    order: int = Field(..., description="阶段顺序", ge=1)
    probability: float = Field(..., description="成功概率", ge=0.0, le=1.0)
    requirements: List[str] = Field(default_factory=list, description="阶段要求列表")
    entry_criteria: List[str] = Field(default_factory=list, description="进入标准")
    exit_criteria: List[str] = Field(default_factory=list, description="退出标准")
    duration_days: Optional[int] = Field(None, description="预期持续天数", ge=1)
    is_active: bool = Field(True, description="是否启用")
    custom_fields: Dict[str, Any] = Field(default_factory=dict, description="自定义字段")


class OpportunityStageCreate(OpportunityStageBase):
    """创建销售机会阶段模式"""
    pass


class OpportunityStageUpdate(BaseModel):
    """更新销售机会阶段模式"""
    name: Optional[str] = Field(None, description="阶段名称", min_length=1, max_length=100)
    description: Optional[str] = Field(None, description="阶段描述")
    stage_type: Optional[StageType] = Field(None, description="阶段类型")
    order: Optional[int] = Field(None, description="阶段顺序", ge=1)
    probability: Optional[float] = Field(None, description="成功概率", ge=0.0, le=1.0)
    requirements: Optional[List[str]] = Field(None, description="阶段要求列表")
    entry_criteria: Optional[List[str]] = Field(None, description="进入标准")
    exit_criteria: Optional[List[str]] = Field(None, description="退出标准")
    duration_days: Optional[int] = Field(None, description="预期持续天数", ge=1)
    is_active: Optional[bool] = Field(None, description="是否启用")
    custom_fields: Optional[Dict[str, Any]] = Field(None, description="自定义字段")


class OpportunityStageResponse(OpportunityStageBase):
    """销售机会阶段响应模式"""
    id: str = Field(..., description="阶段ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    model_config = ConfigDict(from_attributes=True)


class ActivityBase(BaseModel):
    """活动基础模式"""
    activity_type: str = Field(..., description="活动类型", min_length=1, max_length=50)
    title: str = Field(..., description="活动标题", min_length=1, max_length=200)
    description: Optional[str] = Field(None, description="活动描述")
    scheduled_at: Optional[datetime] = Field(None, description="计划时间")
    duration_minutes: Optional[int] = Field(None, description="持续时间(分钟)", ge=1)
    participants: List[str] = Field(default_factory=list, description="参与者列表")
    organizer: Optional[str] = Field(None, description="组织者", max_length=100)
    outcome: Optional[str] = Field(None, description="活动结果", max_length=100)
    next_actions: List[NextAction] = Field(default_factory=list, description="后续行动")
    status: str = Field("planned", description="活动状态")
    custom_fields: Dict[str, Any] = Field(default_factory=dict, description="自定义字段")


class ActivityCreate(ActivityBase):
    """创建活动模式"""
    pass


class ActivityUpdate(BaseModel):
    """更新活动模式"""
    activity_type: Optional[str] = Field(None, description="活动类型", min_length=1, max_length=50)
    title: Optional[str] = Field(None, description="活动标题", min_length=1, max_length=200)
    description: Optional[str] = Field(None, description="活动描述")
    scheduled_at: Optional[datetime] = Field(None, description="计划时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    duration_minutes: Optional[int] = Field(None, description="持续时间(分钟)", ge=1)
    participants: Optional[List[str]] = Field(None, description="参与者列表")
    organizer: Optional[str] = Field(None, description="组织者", max_length=100)
    outcome: Optional[str] = Field(None, description="活动结果", max_length=100)
    next_actions: Optional[List[NextAction]] = Field(None, description="后续行动")
    status: Optional[str] = Field(None, description="活动状态")
    custom_fields: Optional[Dict[str, Any]] = Field(None, description="自定义字段")


class ActivityResponse(ActivityBase):
    """活动响应模式"""
    id: str = Field(..., description="活动ID")
    opportunity_id: str = Field(..., description="机会ID")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    model_config = ConfigDict(from_attributes=True)


class StageHistoryResponse(BaseModel):
    """阶段历史响应模式"""
    id: str = Field(..., description="历史记录ID")
    opportunity_id: str = Field(..., description="机会ID")
    from_stage_id: Optional[str] = Field(None, description="原阶段ID")
    to_stage_id: str = Field(..., description="目标阶段ID")
    reason: Optional[str] = Field(None, description="变更原因")
    notes: Optional[str] = Field(None, description="变更备注")
    changed_by: Optional[str] = Field(None, description="变更人")
    duration_days: Optional[int] = Field(None, description="在原阶段停留天数")
    changed_at: datetime = Field(..., description="变更时间")
    
    # 关联的阶段信息
    from_stage: Optional[OpportunityStageResponse] = Field(None, description="原阶段信息")
    to_stage: OpportunityStageResponse = Field(..., description="目标阶段信息")

    model_config = ConfigDict(from_attributes=True)


class OpportunityBase(BaseModel):
    """销售机会基础模式"""
    name: str = Field(..., description="机会名称", min_length=1, max_length=200)
    description: Optional[str] = Field(None, description="机会描述")
    customer_id: str = Field(..., description="客户ID")
    value: float = Field(..., description="机会价值", ge=0)
    probability: Optional[float] = Field(None, description="成功概率", ge=0.0, le=1.0)
    stage_id: str = Field(..., description="当前阶段ID")
    expected_close_date: Optional[datetime] = Field(None, description="预期关闭日期")
    status: OpportunityStatus = Field(OpportunityStatus.OPEN, description="机会状态")
    priority: OpportunityPriority = Field(OpportunityPriority.MEDIUM, description="优先级")
    products: List[ProductInfo] = Field(default_factory=list, description="相关产品列表")
    solution_details: Dict[str, Any] = Field(default_factory=dict, description="解决方案详情")
    competitors: List[CompetitorInfo] = Field(default_factory=list, description="竞争对手信息")
    competitive_advantages: List[str] = Field(default_factory=list, description="竞争优势")
    stakeholders: List[StakeholderInfo] = Field(default_factory=list, description="利益相关者信息")
    decision_makers: List[str] = Field(default_factory=list, description="决策者信息")
    risks: List[RiskInfo] = Field(default_factory=list, description="风险列表")
    challenges: List[str] = Field(default_factory=list, description="挑战列表")
    assigned_to: Optional[str] = Field(None, description="负责人", max_length=100)
    team_members: List[str] = Field(default_factory=list, description="团队成员")
    tags: List[str] = Field(default_factory=list, description="标签列表")
    category: Optional[str] = Field(None, description="机会类别", max_length=100)
    custom_fields: Dict[str, Any] = Field(default_factory=dict, description="自定义字段")
    notes: Optional[str] = Field(None, description="备注")

    @validator('expected_close_date')
    def validate_expected_close_date(cls, v):
        if v and v < datetime.now():
            raise ValueError('预期关闭日期不能早于当前时间')
        return v

    @validator('value')
    def validate_value(cls, v):
        if v < 0:
            raise ValueError('机会价值不能为负数')
        return v


class OpportunityCreate(OpportunityBase):
    """创建销售机会模式"""
    pass


class OpportunityUpdate(BaseModel):
    """更新销售机会模式"""
    name: Optional[str] = Field(None, description="机会名称", min_length=1, max_length=200)
    description: Optional[str] = Field(None, description="机会描述")
    customer_id: Optional[str] = Field(None, description="客户ID")
    value: Optional[float] = Field(None, description="机会价值", ge=0)
    probability: Optional[float] = Field(None, description="成功概率", ge=0.0, le=1.0)
    stage_id: Optional[str] = Field(None, description="当前阶段ID")
    expected_close_date: Optional[datetime] = Field(None, description="预期关闭日期")
    actual_close_date: Optional[datetime] = Field(None, description="实际关闭日期")
    status: Optional[OpportunityStatus] = Field(None, description="机会状态")
    priority: Optional[OpportunityPriority] = Field(None, description="优先级")
    products: Optional[List[ProductInfo]] = Field(None, description="相关产品列表")
    solution_details: Optional[Dict[str, Any]] = Field(None, description="解决方案详情")
    competitors: Optional[List[CompetitorInfo]] = Field(None, description="竞争对手信息")
    competitive_advantages: Optional[List[str]] = Field(None, description="竞争优势")
    stakeholders: Optional[List[StakeholderInfo]] = Field(None, description="利益相关者信息")
    decision_makers: Optional[List[str]] = Field(None, description="决策者信息")
    risks: Optional[List[RiskInfo]] = Field(None, description="风险列表")
    challenges: Optional[List[str]] = Field(None, description="挑战列表")
    assigned_to: Optional[str] = Field(None, description="负责人", max_length=100)
    team_members: Optional[List[str]] = Field(None, description="团队成员")
    tags: Optional[List[str]] = Field(None, description="标签列表")
    category: Optional[str] = Field(None, description="机会类别", max_length=100)
    custom_fields: Optional[Dict[str, Any]] = Field(None, description="自定义字段")
    notes: Optional[str] = Field(None, description="备注")


class OpportunityResponse(OpportunityBase):
    """销售机会响应模式"""
    id: str = Field(..., description="机会ID")
    actual_close_date: Optional[datetime] = Field(None, description="实际关闭日期")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    # 关联数据
    stage: OpportunityStageResponse = Field(..., description="当前阶段信息")
    activities: List[ActivityResponse] = Field(default_factory=list, description="活动记录")
    stage_history: List[StageHistoryResponse] = Field(default_factory=list, description="阶段历史")

    model_config = ConfigDict(from_attributes=True)


class OpportunityListResponse(BaseModel):
    """销售机会列表响应模式"""
    opportunities: List[OpportunityResponse] = Field(..., description="机会列表")
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页大小")
    pages: int = Field(..., description="总页数")


class StageTransitionRequest(BaseModel):
    """阶段转换请求模式"""
    opportunity_id: str = Field(..., description="机会ID")
    to_stage_id: str = Field(..., description="目标阶段ID")
    reason: Optional[str] = Field(None, description="转换原因", max_length=200)
    notes: Optional[str] = Field(None, description="转换备注")
    validate_criteria: bool = Field(True, description="是否验证转换标准")


class StageTransitionResponse(BaseModel):
    """阶段转换响应模式"""
    success: bool = Field(..., description="转换是否成功")
    message: str = Field(..., description="转换结果消息")
    opportunity: Optional[OpportunityResponse] = Field(None, description="更新后的机会信息")
    validation_errors: List[str] = Field(default_factory=list, description="验证错误列表")


class OpportunityStatistics(BaseModel):
    """销售机会统计模式"""
    total_opportunities: int = Field(..., description="总机会数")
    total_value: float = Field(..., description="总价值")
    weighted_value: float = Field(..., description="加权价值")
    by_status: Dict[str, int] = Field(..., description="按状态统计")
    by_stage: Dict[str, int] = Field(..., description="按阶段统计")
    by_priority: Dict[str, int] = Field(..., description="按优先级统计")
    by_assigned: Dict[str, int] = Field(..., description="按负责人统计")
    average_value: float = Field(..., description="平均价值")
    win_rate: float = Field(..., description="赢单率")
    average_sales_cycle: float = Field(..., description="平均销售周期(天)")
    created_this_month: int = Field(..., description="本月新增")
    expected_close_this_month: int = Field(..., description="本月预期关闭")


class FunnelAnalysis(BaseModel):
    """销售漏斗分析模式"""
    stage_id: str = Field(..., description="阶段ID")
    stage_name: str = Field(..., description="阶段名称")
    opportunity_count: int = Field(..., description="机会数量")
    total_value: float = Field(..., description="总价值")
    weighted_value: float = Field(..., description="加权价值")
    conversion_rate: float = Field(..., description="转化率")
    average_duration: float = Field(..., description="平均停留时间(天)")


class FunnelAnalysisResponse(BaseModel):
    """销售漏斗分析响应模式"""
    funnel_stages: List[FunnelAnalysis] = Field(..., description="漏斗阶段分析")
    overall_conversion_rate: float = Field(..., description="整体转化率")
    total_pipeline_value: float = Field(..., description="总管道价值")
    weighted_pipeline_value: float = Field(..., description="加权管道价值")
    analysis_date: datetime = Field(..., description="分析日期")
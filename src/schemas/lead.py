"""
线索Pydantic模式
"""

from pydantic import BaseModel, Field, ConfigDict, validator
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum

from src.models.lead import LeadStatus, LeadSource


class ContactInfo(BaseModel):
    """联系信息模式"""
    phone: Optional[str] = Field(None, description="电话号码")
    email: Optional[str] = Field(None, description="邮箱地址")
    wechat: Optional[str] = Field(None, description="微信号")
    address: Optional[str] = Field(None, description="地址")
    linkedin: Optional[str] = Field(None, description="LinkedIn")


class CompanyInfo(BaseModel):
    """公司信息模式"""
    size: Optional[str] = Field(None, description="公司规模")
    revenue: Optional[float] = Field(None, description="年收入")
    employees: Optional[int] = Field(None, description="员工数量")
    website: Optional[str] = Field(None, description="网站")
    location: Optional[str] = Field(None, description="位置")
    founded_year: Optional[int] = Field(None, description="成立年份")


class ScoreFactorDetail(BaseModel):
    """评分因子详情模式"""
    name: str = Field(..., description="因子名称")
    category: str = Field(..., description="因子类别")
    weight: float = Field(..., description="权重", ge=0.0, le=1.0)
    value: float = Field(..., description="因子值", ge=0.0, le=100.0)
    score: float = Field(..., description="加权分数", ge=0.0)
    reason: str = Field(..., description="评分原因")


class LeadScoreDetail(BaseModel):
    """线索评分详情模式"""
    total_score: float = Field(..., description="总分", ge=0.0, le=100.0)
    confidence: float = Field(..., description="置信度", ge=0.0, le=1.0)
    factors: List[ScoreFactorDetail] = Field(..., description="评分因子列表")
    algorithm_version: str = Field(..., description="算法版本")
    calculated_at: datetime = Field(..., description="计算时间")


class InteractionBase(BaseModel):
    """互动基础模式"""
    interaction_type: str = Field(..., description="互动类型")
    channel: Optional[str] = Field(None, description="渠道")
    direction: Optional[str] = Field(None, description="方向")
    subject: Optional[str] = Field(None, description="主题")
    content: Optional[str] = Field(None, description="内容")
    outcome: Optional[str] = Field(None, description="结果")
    next_action: Optional[str] = Field(None, description="下一步行动")
    participant: Optional[str] = Field(None, description="参与者")
    interaction_at: Optional[datetime] = Field(None, description="互动时间")


class InteractionCreate(InteractionBase):
    """创建互动模式"""
    pass


class InteractionResponse(InteractionBase):
    """互动响应模式"""
    id: str = Field(..., description="互动ID")
    lead_id: str = Field(..., description="线索ID")
    created_at: datetime = Field(..., description="创建时间")

    model_config = ConfigDict(from_attributes=True)


class LeadBase(BaseModel):
    """线索基础模式"""
    name: str = Field(..., description="联系人姓名", min_length=1, max_length=100)
    company: str = Field(..., description="公司名称", min_length=1, max_length=200)
    title: Optional[str] = Field(None, description="职位", max_length=100)
    industry: Optional[str] = Field(None, description="行业", max_length=100)
    contact: Optional[ContactInfo] = Field(None, description="联系信息")
    company_info: Optional[CompanyInfo] = Field(None, description="公司信息")
    requirements: Optional[str] = Field(None, description="需求描述")
    budget: Optional[float] = Field(None, description="预算", ge=0)
    timeline: Optional[str] = Field(None, description="时间线", max_length=100)
    source: LeadSource = Field(..., description="线索来源")
    status: Optional[LeadStatus] = Field(LeadStatus.NEW, description="线索状态")
    assigned_to: Optional[str] = Field(None, description="分配给", max_length=100)
    tags: List[str] = Field(default_factory=list, description="标签列表")
    notes: Optional[str] = Field(None, description="备注")
    custom_fields: Dict[str, Any] = Field(default_factory=dict, description="自定义字段")

    @validator('budget')
    def validate_budget(cls, v):
        if v is not None and v < 0:
            raise ValueError('预算不能为负数')
        return v


class LeadCreate(LeadBase):
    """创建线索模式"""
    pass


class LeadUpdate(BaseModel):
    """更新线索模式"""
    name: Optional[str] = Field(None, description="联系人姓名", min_length=1, max_length=100)
    company: Optional[str] = Field(None, description="公司名称", min_length=1, max_length=200)
    title: Optional[str] = Field(None, description="职位", max_length=100)
    industry: Optional[str] = Field(None, description="行业", max_length=100)
    contact: Optional[ContactInfo] = Field(None, description="联系信息")
    company_info: Optional[CompanyInfo] = Field(None, description="公司信息")
    requirements: Optional[str] = Field(None, description="需求描述")
    budget: Optional[float] = Field(None, description="预算", ge=0)
    timeline: Optional[str] = Field(None, description="时间线", max_length=100)
    source: Optional[LeadSource] = Field(None, description="线索来源")
    status: Optional[LeadStatus] = Field(None, description="线索状态")
    assigned_to: Optional[str] = Field(None, description="分配给", max_length=100)
    tags: Optional[List[str]] = Field(None, description="标签列表")
    notes: Optional[str] = Field(None, description="备注")
    custom_fields: Optional[Dict[str, Any]] = Field(None, description="自定义字段")


class LeadResponse(LeadBase):
    """线索响应模式"""
    id: str = Field(..., description="线索ID")
    assigned_at: Optional[datetime] = Field(None, description="分配时间")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    # 可选的关联数据
    current_score: Optional[LeadScoreDetail] = Field(None, description="当前评分")
    interactions: List[InteractionResponse] = Field(default_factory=list, description="互动记录")

    model_config = ConfigDict(from_attributes=True)


class LeadListResponse(BaseModel):
    """线索列表响应模式"""
    leads: List[LeadResponse] = Field(..., description="线索列表")
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页大小")
    pages: int = Field(..., description="总页数")


class ScoreFactorConfig(BaseModel):
    """评分因子配置模式"""
    name: str = Field(..., description="因子名称")
    category: str = Field(..., description="因子类别")
    description: Optional[str] = Field(None, description="因子描述")
    weight: float = Field(..., description="权重", ge=0.0, le=1.0)
    max_score: float = Field(100.0, description="最大分值", ge=0.0)
    min_score: float = Field(0.0, description="最小分值", ge=0.0)
    calculation_rules: Dict[str, Any] = Field(..., description="计算规则")
    is_active: bool = Field(True, description="是否启用")

    @validator('max_score')
    def validate_max_score(cls, v, values):
        if 'min_score' in values and v <= values['min_score']:
            raise ValueError('最大分值必须大于最小分值')
        return v


class ScoreFactorResponse(ScoreFactorConfig):
    """评分因子响应模式"""
    id: str = Field(..., description="因子ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    model_config = ConfigDict(from_attributes=True)


class LeadScoreRequest(BaseModel):
    """线索评分请求模式"""
    lead_id: str = Field(..., description="线索ID")
    force_recalculate: bool = Field(False, description="是否强制重新计算")


class LeadScoreResponse(BaseModel):
    """线索评分响应模式"""
    id: str = Field(..., description="评分ID")
    lead_id: str = Field(..., description="线索ID")
    score_detail: LeadScoreDetail = Field(..., description="评分详情")

    model_config = ConfigDict(from_attributes=True)


class LeadAssignmentRequest(BaseModel):
    """线索分配请求模式"""
    lead_ids: List[str] = Field(..., description="线索ID列表")
    assigned_to: str = Field(..., description="分配给")
    reason: Optional[str] = Field(None, description="分配原因")


class LeadAssignmentResponse(BaseModel):
    """线索分配响应模式"""
    success_count: int = Field(..., description="成功分配数量")
    failed_count: int = Field(..., description="失败分配数量")
    failed_leads: List[str] = Field(default_factory=list, description="失败的线索ID列表")
    message: str = Field(..., description="分配结果消息")


class LeadStatistics(BaseModel):
    """线索统计模式"""
    total_leads: int = Field(..., description="总线索数")
    by_status: Dict[str, int] = Field(..., description="按状态统计")
    by_source: Dict[str, int] = Field(..., description="按来源统计")
    by_assigned: Dict[str, int] = Field(..., description="按分配人统计")
    average_score: float = Field(..., description="平均评分")
    conversion_rate: float = Field(..., description="转化率")
    created_today: int = Field(..., description="今日新增")
    created_this_week: int = Field(..., description="本周新增")
    created_this_month: int = Field(..., description="本月新增")
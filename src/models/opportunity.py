"""
销售机会数据模型
"""

from sqlalchemy import Column, String, DateTime, Text, JSON, Enum as SQLEnum, Float, Integer, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from src.core.database import Base


class OpportunityStatus(str, enum.Enum):
    """销售机会状态枚举"""
    OPEN = "open"
    WON = "won"
    LOST = "lost"
    CANCELLED = "cancelled"


class OpportunityPriority(str, enum.Enum):
    """销售机会优先级枚举"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class StageType(str, enum.Enum):
    """阶段类型枚举"""
    QUALIFICATION = "qualification"
    NEEDS_ANALYSIS = "needs_analysis"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    CLOSING = "closing"
    DELIVERY = "delivery"


class OpportunityStage(Base):
    """销售机会阶段模型"""
    __tablename__ = "opportunity_stages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # 阶段基本信息
    name = Column(String(100), nullable=False, comment="阶段名称")
    description = Column(Text, comment="阶段描述")
    stage_type = Column(SQLEnum(StageType), nullable=False, comment="阶段类型")
    
    # 阶段配置
    order = Column(Integer, nullable=False, comment="阶段顺序")
    probability = Column(Float, nullable=False, comment="成功概率", default=0.0)
    
    # 阶段要求和标准
    requirements = Column(JSON, comment="阶段要求列表")
    entry_criteria = Column(JSON, comment="进入标准")
    exit_criteria = Column(JSON, comment="退出标准")
    
    # 阶段配置
    duration_days = Column(Integer, comment="预期持续天数")
    is_active = Column(Boolean, default=True, comment="是否启用")
    
    # 自定义字段
    custom_fields = Column(JSON, comment="自定义字段")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    
    # 关系
    opportunities = relationship("Opportunity", back_populates="stage")

    def __repr__(self):
        return f"<OpportunityStage(id={self.id}, name={self.name}, order={self.order})>"


class Opportunity(Base):
    """销售机会数据模型"""
    __tablename__ = "opportunities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # 基本信息
    name = Column(String(200), nullable=False, comment="机会名称")
    description = Column(Text, comment="机会描述")
    
    # 客户关联
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False, comment="客户ID")
    
    # 商业信息
    value = Column(Float, nullable=False, comment="机会价值", default=0.0)
    probability = Column(Float, comment="成功概率", default=0.0)
    
    # 阶段信息
    stage_id = Column(UUID(as_uuid=True), ForeignKey("opportunity_stages.id"), nullable=False, comment="当前阶段ID")
    
    # 时间信息
    expected_close_date = Column(DateTime, comment="预期关闭日期")
    actual_close_date = Column(DateTime, comment="实际关闭日期")
    
    # 状态和优先级
    status = Column(SQLEnum(OpportunityStatus), default=OpportunityStatus.OPEN, comment="机会状态")
    priority = Column(SQLEnum(OpportunityPriority), default=OpportunityPriority.MEDIUM, comment="优先级")
    
    # 产品和解决方案
    products = Column(JSON, comment="相关产品列表")
    solution_details = Column(JSON, comment="解决方案详情")
    
    # 竞争信息
    competitors = Column(JSON, comment="竞争对手信息")
    competitive_advantages = Column(JSON, comment="竞争优势")
    
    # 利益相关者
    stakeholders = Column(JSON, comment="利益相关者信息")
    decision_makers = Column(JSON, comment="决策者信息")
    
    # 风险和挑战
    risks = Column(JSON, comment="风险列表")
    challenges = Column(JSON, comment="挑战列表")
    
    # 分配信息
    assigned_to = Column(String(100), comment="负责人")
    team_members = Column(JSON, comment="团队成员")
    
    # 标签和分类
    tags = Column(JSON, comment="标签列表")
    category = Column(String(100), comment="机会类别")
    
    # 自定义字段
    custom_fields = Column(JSON, comment="自定义字段")
    
    # 备注
    notes = Column(Text, comment="备注")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    
    # 关系
    customer = relationship("Customer", back_populates="opportunities")
    stage = relationship("OpportunityStage", back_populates="opportunities")
    activities = relationship("OpportunityActivity", back_populates="opportunity", cascade="all, delete-orphan")
    stage_history = relationship("OpportunityStageHistory", back_populates="opportunity", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Opportunity(id={self.id}, name={self.name}, value={self.value}, status={self.status})>"


class OpportunityActivity(Base):
    """销售机会活动记录模型"""
    __tablename__ = "opportunity_activities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    opportunity_id = Column(UUID(as_uuid=True), ForeignKey("opportunities.id"), nullable=False, comment="机会ID")
    
    # 活动信息
    activity_type = Column(String(50), nullable=False, comment="活动类型")
    title = Column(String(200), nullable=False, comment="活动标题")
    description = Column(Text, comment="活动描述")
    
    # 时间信息
    scheduled_at = Column(DateTime, comment="计划时间")
    completed_at = Column(DateTime, comment="完成时间")
    duration_minutes = Column(Integer, comment="持续时间(分钟)")
    
    # 参与者
    participants = Column(JSON, comment="参与者列表")
    organizer = Column(String(100), comment="组织者")
    
    # 结果
    outcome = Column(String(100), comment="活动结果")
    next_actions = Column(JSON, comment="后续行动")
    
    # 状态
    status = Column(String(50), default="planned", comment="活动状态")
    
    # 自定义字段
    custom_fields = Column(JSON, comment="自定义字段")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    
    # 关系
    opportunity = relationship("Opportunity", back_populates="activities")

    def __repr__(self):
        return f"<OpportunityActivity(id={self.id}, opportunity_id={self.opportunity_id}, type={self.activity_type})>"


class OpportunityStageHistory(Base):
    """销售机会阶段历史记录模型"""
    __tablename__ = "opportunity_stage_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    opportunity_id = Column(UUID(as_uuid=True), ForeignKey("opportunities.id"), nullable=False, comment="机会ID")
    
    # 阶段变更信息
    from_stage_id = Column(UUID(as_uuid=True), ForeignKey("opportunity_stages.id"), comment="原阶段ID")
    to_stage_id = Column(UUID(as_uuid=True), ForeignKey("opportunity_stages.id"), nullable=False, comment="目标阶段ID")
    
    # 变更原因和备注
    reason = Column(String(200), comment="变更原因")
    notes = Column(Text, comment="变更备注")
    
    # 变更人员
    changed_by = Column(String(100), comment="变更人")
    
    # 阶段停留时间
    duration_days = Column(Integer, comment="在原阶段停留天数")
    
    # 时间戳
    changed_at = Column(DateTime, default=datetime.utcnow, comment="变更时间")
    
    # 关系
    opportunity = relationship("Opportunity", back_populates="stage_history")
    from_stage = relationship("OpportunityStage", foreign_keys=[from_stage_id])
    to_stage = relationship("OpportunityStage", foreign_keys=[to_stage_id])

    def __repr__(self):
        return f"<OpportunityStageHistory(id={self.id}, opportunity_id={self.opportunity_id}, changed_at={self.changed_at})>"
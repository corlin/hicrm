"""
线索数据模型
"""

from sqlalchemy import Column, String, DateTime, Text, JSON, Enum as SQLEnum, Float, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from src.core.database import Base


class LeadStatus(str, enum.Enum):
    """线索状态枚举"""
    NEW = "new"
    QUALIFIED = "qualified"
    CONTACTED = "contacted"
    CONVERTED = "converted"
    LOST = "lost"


class LeadSource(str, enum.Enum):
    """线索来源枚举"""
    WEBSITE = "website"
    SOCIAL_MEDIA = "social_media"
    EMAIL_CAMPAIGN = "email_campaign"
    REFERRAL = "referral"
    COLD_CALL = "cold_call"
    TRADE_SHOW = "trade_show"
    PARTNER = "partner"
    ADVERTISEMENT = "advertisement"
    OTHER = "other"


class Lead(Base):
    """线索数据模型"""
    __tablename__ = "leads"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # 基本信息
    name = Column(String(100), nullable=False, comment="联系人姓名")
    company = Column(String(200), nullable=False, comment="公司名称")
    title = Column(String(100), comment="职位")
    industry = Column(String(100), comment="行业")
    
    # 联系信息 - 存储为JSON
    contact = Column(JSON, comment="联系信息")
    
    # 公司信息 - 存储为JSON
    company_info = Column(JSON, comment="公司信息")
    
    # 需求信息
    requirements = Column(Text, comment="需求描述")
    budget = Column(Float, comment="预算")
    timeline = Column(String(100), comment="时间线")
    
    # 线索来源和状态
    source = Column(SQLEnum(LeadSource), nullable=False, comment="线索来源")
    status = Column(SQLEnum(LeadStatus), default=LeadStatus.NEW, comment="线索状态")
    
    # 分配信息
    assigned_to = Column(String(100), comment="分配给")
    assigned_at = Column(DateTime, comment="分配时间")
    
    # 标签和备注
    tags = Column(JSON, comment="标签列表")
    notes = Column(Text, comment="备注")
    
    # 自定义字段
    custom_fields = Column(JSON, comment="自定义字段")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    
    # 关系
    lead_scores = relationship("LeadScore", back_populates="lead", cascade="all, delete-orphan")
    interactions = relationship("LeadInteraction", back_populates="lead", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Lead(id={self.id}, name={self.name}, company={self.company}, status={self.status})>"


class LeadScore(Base):
    """线索评分模型"""
    __tablename__ = "lead_scores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads.id"), nullable=False, comment="线索ID")
    
    # 评分信息
    total_score = Column(Float, nullable=False, comment="总分")
    confidence = Column(Float, default=0.0, comment="置信度")
    
    # 评分因子 - 存储为JSON
    score_factors = Column(JSON, comment="评分因子详情")
    
    # 评分版本和算法
    algorithm_version = Column(String(50), default="v1.0", comment="算法版本")
    
    # 时间戳
    calculated_at = Column(DateTime, default=datetime.utcnow, comment="计算时间")
    
    # 关系
    lead = relationship("Lead", back_populates="lead_scores")

    def __repr__(self):
        return f"<LeadScore(id={self.id}, lead_id={self.lead_id}, total_score={self.total_score})>"


class ScoreFactor(Base):
    """评分因子模型"""
    __tablename__ = "score_factors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # 因子信息
    name = Column(String(100), nullable=False, comment="因子名称")
    category = Column(String(50), nullable=False, comment="因子类别")
    description = Column(Text, comment="因子描述")
    
    # 权重配置
    weight = Column(Float, nullable=False, comment="权重")
    max_score = Column(Float, default=100.0, comment="最大分值")
    min_score = Column(Float, default=0.0, comment="最小分值")
    
    # 计算规则 - 存储为JSON
    calculation_rules = Column(JSON, comment="计算规则")
    
    # 状态
    is_active = Column(String(10), default="true", comment="是否启用")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    def __repr__(self):
        return f"<ScoreFactor(id={self.id}, name={self.name}, weight={self.weight})>"


class LeadInteraction(Base):
    """线索互动记录模型"""
    __tablename__ = "lead_interactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads.id"), nullable=False, comment="线索ID")
    
    # 互动信息
    interaction_type = Column(String(50), nullable=False, comment="互动类型")
    channel = Column(String(50), comment="渠道")
    direction = Column(String(20), comment="方向(inbound/outbound)")
    
    # 内容
    subject = Column(String(200), comment="主题")
    content = Column(Text, comment="内容")
    
    # 结果
    outcome = Column(String(100), comment="结果")
    next_action = Column(String(200), comment="下一步行动")
    
    # 参与者
    participant = Column(String(100), comment="参与者")
    
    # 时间戳
    interaction_at = Column(DateTime, default=datetime.utcnow, comment="互动时间")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    
    # 关系
    lead = relationship("Lead", back_populates="interactions")

    def __repr__(self):
        return f"<LeadInteraction(id={self.id}, lead_id={self.lead_id}, type={self.interaction_type})>"
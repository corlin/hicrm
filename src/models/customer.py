"""
客户数据模型
"""

from sqlalchemy import Column, String, DateTime, Text, JSON, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from src.core.database import Base


class CompanySize(str, enum.Enum):
    """公司规模枚举"""
    STARTUP = "startup"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    ENTERPRISE = "enterprise"


class CustomerStatus(str, enum.Enum):
    """客户状态枚举"""
    PROSPECT = "prospect"
    QUALIFIED = "qualified"
    CUSTOMER = "customer"
    INACTIVE = "inactive"


class Customer(Base):
    """客户数据模型"""
    __tablename__ = "customers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, comment="客户姓名")
    company = Column(String(200), nullable=False, comment="公司名称")
    industry = Column(String(100), comment="行业")
    size = Column(SQLEnum(CompanySize), comment="公司规模")
    
    # 联系信息 - 存储为JSON
    contact = Column(JSON, comment="联系信息")
    
    # 客户画像 - 存储为JSON
    profile = Column(JSON, comment="客户画像")
    
    # 客户状态
    status = Column(SQLEnum(CustomerStatus), default=CustomerStatus.PROSPECT, comment="客户状态")
    
    # 标签
    tags = Column(JSON, comment="标签列表")
    
    # 自定义字段
    custom_fields = Column(JSON, comment="自定义字段")
    
    # 备注
    notes = Column(Text, comment="备注")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    
    # 关系
    opportunities = relationship("Opportunity", back_populates="customer", cascade="all, delete-orphan")
    # interactions = relationship("Interaction", back_populates="customer")

    def __repr__(self):
        return f"<Customer(id={self.id}, name={self.name}, company={self.company})>"
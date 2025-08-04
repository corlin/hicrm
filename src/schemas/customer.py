"""
客户Pydantic模式
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum

from src.models.customer import CompanySize, CustomerStatus


class ContactInfo(BaseModel):
    """联系信息模式"""
    phone: Optional[str] = Field(None, description="电话号码")
    email: Optional[str] = Field(None, description="邮箱地址")
    wechat: Optional[str] = Field(None, description="微信号")
    address: Optional[str] = Field(None, description="地址")
    website: Optional[str] = Field(None, description="网站")


class CustomerProfile(BaseModel):
    """客户画像模式"""
    decision_making_style: Optional[str] = Field(None, description="决策风格")
    communication_preference: Optional[str] = Field(None, description="沟通偏好")
    business_priorities: List[str] = Field(default_factory=list, description="业务优先级")
    pain_points: List[str] = Field(default_factory=list, description="痛点")
    budget: Optional[Dict[str, Any]] = Field(None, description="预算信息")
    timeline: Optional[str] = Field(None, description="时间线")
    influencers: List[str] = Field(default_factory=list, description="影响者")


class CustomerBase(BaseModel):
    """客户基础模式"""
    name: str = Field(..., description="客户姓名", min_length=1, max_length=100)
    company: str = Field(..., description="公司名称", min_length=1, max_length=200)
    industry: Optional[str] = Field(None, description="行业", max_length=100)
    size: Optional[CompanySize] = Field(None, description="公司规模")
    contact: Optional[ContactInfo] = Field(None, description="联系信息")
    profile: Optional[CustomerProfile] = Field(None, description="客户画像")
    status: Optional[CustomerStatus] = Field(CustomerStatus.PROSPECT, description="客户状态")
    tags: List[str] = Field(default_factory=list, description="标签列表")
    custom_fields: Dict[str, Any] = Field(default_factory=dict, description="自定义字段")
    notes: Optional[str] = Field(None, description="备注")


class CustomerCreate(CustomerBase):
    """创建客户模式"""
    pass


class CustomerUpdate(BaseModel):
    """更新客户模式"""
    name: Optional[str] = Field(None, description="客户姓名", min_length=1, max_length=100)
    company: Optional[str] = Field(None, description="公司名称", min_length=1, max_length=200)
    industry: Optional[str] = Field(None, description="行业", max_length=100)
    size: Optional[CompanySize] = Field(None, description="公司规模")
    contact: Optional[ContactInfo] = Field(None, description="联系信息")
    profile: Optional[CustomerProfile] = Field(None, description="客户画像")
    status: Optional[CustomerStatus] = Field(None, description="客户状态")
    tags: Optional[List[str]] = Field(None, description="标签列表")
    custom_fields: Optional[Dict[str, Any]] = Field(None, description="自定义字段")
    notes: Optional[str] = Field(None, description="备注")


class CustomerResponse(CustomerBase):
    """客户响应模式"""
    id: str = Field(..., description="客户ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    model_config = ConfigDict(from_attributes=True)


class CustomerListResponse(BaseModel):
    """客户列表响应模式"""
    customers: List[CustomerResponse] = Field(..., description="客户列表")
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页大小")
    pages: int = Field(..., description="总页数")
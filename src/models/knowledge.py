"""
知识库管理相关数据模型
Knowledge Management Data Models
"""

from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import uuid


class KnowledgeType(str, Enum):
    """知识类型枚举"""
    DOCUMENT = "document"
    CASE_STUDY = "case_study"
    BEST_PRACTICE = "best_practice"
    TEMPLATE = "template"
    FAQ = "faq"
    PROCESS = "process"
    RULE = "rule"


class KnowledgeStatus(str, Enum):
    """知识状态枚举"""
    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class QualityMetrics(BaseModel):
    """知识质量指标"""
    accuracy_score: float = Field(ge=0.0, le=1.0, description="准确性评分")
    completeness_score: float = Field(ge=0.0, le=1.0, description="完整性评分")
    relevance_score: float = Field(ge=0.0, le=1.0, description="相关性评分")
    freshness_score: float = Field(ge=0.0, le=1.0, description="时效性评分")
    usage_score: float = Field(ge=0.0, le=1.0, description="使用频率评分")
    overall_score: float = Field(ge=0.0, le=1.0, description="综合评分")
    last_evaluated: datetime = Field(description="最后评估时间")


class UsageStatistics(BaseModel):
    """使用统计"""
    view_count: int = Field(default=0, ge=0, description="查看次数")
    search_count: int = Field(default=0, ge=0, description="搜索命中次数")
    reference_count: int = Field(default=0, ge=0, description="被引用次数")
    feedback_count: int = Field(default=0, ge=0, description="反馈次数")
    positive_feedback: int = Field(default=0, ge=0, description="正面反馈数")
    negative_feedback: int = Field(default=0, ge=0, description="负面反馈数")
    last_accessed: Optional[datetime] = Field(default=None, description="最后访问时间")


class KnowledgeMetadata(BaseModel):
    """知识元数据"""
    source: str = Field(description="知识来源")
    author: str = Field(description="作者")
    domain: str = Field(description="领域分类")
    tags: List[str] = Field(default_factory=list, description="标签")
    language: str = Field(default="zh-CN", description="语言")
    version: str = Field(default="1.0", description="版本号")
    confidence: float = Field(default=0.8, ge=0.0, le=1.0, description="置信度")
    keywords: List[str] = Field(default_factory=list, description="关键词")


class KnowledgeChunk(BaseModel):
    """知识块"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="块ID")
    content: str = Field(description="块内容")
    chunk_index: int = Field(ge=0, description="块索引")
    start_position: int = Field(ge=0, description="起始位置")
    end_position: int = Field(ge=0, description="结束位置")
    embedding: Optional[List[float]] = Field(default=None, description="向量嵌入")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="块元数据")


class KnowledgeRelation(BaseModel):
    """知识关系"""
    related_id: str = Field(description="关联知识ID")
    relation_type: str = Field(description="关系类型")
    strength: float = Field(ge=0.0, le=1.0, description="关系强度")
    description: Optional[str] = Field(default=None, description="关系描述")


class Knowledge(BaseModel):
    """知识实体模型"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="知识ID")
    title: str = Field(description="标题")
    content: str = Field(description="内容")
    type: KnowledgeType = Field(description="知识类型")
    status: KnowledgeStatus = Field(default=KnowledgeStatus.DRAFT, description="状态")
    
    # 结构化信息
    chunks: List[KnowledgeChunk] = Field(default_factory=list, description="知识块")
    metadata: KnowledgeMetadata = Field(description="元数据")
    
    # 质量和使用统计
    quality: Optional[QualityMetrics] = Field(default=None, description="质量指标")
    usage: UsageStatistics = Field(default_factory=UsageStatistics, description="使用统计")
    
    # 关系和分类
    relationships: List[KnowledgeRelation] = Field(default_factory=list, description="知识关系")
    categories: List[str] = Field(default_factory=list, description="分类")
    
    # 时间戳
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
    published_at: Optional[datetime] = Field(default=None, description="发布时间")
    
    # 版本控制
    version_history: List[Dict[str, Any]] = Field(default_factory=list, description="版本历史")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class KnowledgeSearchFilter(BaseModel):
    """知识搜索过滤器"""
    types: Optional[List[KnowledgeType]] = Field(default=None, description="知识类型过滤")
    domains: Optional[List[str]] = Field(default=None, description="领域过滤")
    tags: Optional[List[str]] = Field(default=None, description="标签过滤")
    status: Optional[List[KnowledgeStatus]] = Field(default=None, description="状态过滤")
    min_quality_score: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="最小质量分数")
    date_range: Optional[Dict[str, datetime]] = Field(default=None, description="日期范围")
    author: Optional[str] = Field(default=None, description="作者过滤")


class KnowledgeSearchResult(BaseModel):
    """知识搜索结果"""
    knowledge: Knowledge = Field(description="知识实体")
    score: float = Field(ge=0.0, le=1.0, description="匹配分数")
    relevance: float = Field(ge=0.0, le=1.0, description="相关性分数")
    snippet: str = Field(description="内容摘要")
    matched_chunks: List[KnowledgeChunk] = Field(default_factory=list, description="匹配的知识块")
    highlight: Dict[str, List[str]] = Field(default_factory=dict, description="高亮信息")


class KnowledgeUpdateRequest(BaseModel):
    """知识更新请求"""
    title: Optional[str] = Field(default=None, description="标题")
    content: Optional[str] = Field(default=None, description="内容")
    metadata: Optional[KnowledgeMetadata] = Field(default=None, description="元数据")
    status: Optional[KnowledgeStatus] = Field(default=None, description="状态")
    categories: Optional[List[str]] = Field(default=None, description="分类")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
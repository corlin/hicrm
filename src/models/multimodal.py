# 多模态数据分析模型

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from enum import Enum
import numpy as np

class DataModalityType(str, Enum):
    """数据模态类型"""
    TEXT = "text"
    VOICE = "voice"
    BEHAVIOR = "behavior"
    INTERACTION = "interaction"
    DOCUMENT = "document"

class VoiceAnalysisResult(BaseModel):
    """语音分析结果"""
    transcript: str = Field(description="语音转文本结果")
    confidence: float = Field(ge=0.0, le=1.0, description="转录置信度")
    sentiment: str = Field(description="情感分析结果")
    emotion: str = Field(description="情绪识别结果")
    speaking_rate: float = Field(description="语速(词/分钟)")
    pause_frequency: float = Field(description="停顿频率")
    voice_quality: Dict[str, float] = Field(description="语音质量指标")
    keywords: List[str] = Field(description="关键词提取")
    intent: Optional[str] = Field(description="意图识别")

class BehaviorData(BaseModel):
    """客户行为数据"""
    customer_id: str = Field(description="客户ID")
    session_id: str = Field(description="会话ID")
    page_views: List[Dict[str, Any]] = Field(description="页面浏览记录")
    click_events: List[Dict[str, Any]] = Field(description="点击事件")
    time_spent: Dict[str, float] = Field(description="各页面停留时间")
    interaction_patterns: Dict[str, Any] = Field(description="交互模式")
    engagement_score: float = Field(ge=0.0, le=1.0, description="参与度评分")
    conversion_indicators: List[str] = Field(description="转化指标")
    timestamp: datetime = Field(description="数据时间戳")

class MultimodalDataPoint(BaseModel):
    """多模态数据点"""
    id: str = Field(description="数据点ID")
    customer_id: str = Field(description="客户ID")
    modality: DataModalityType = Field(description="数据模态类型")
    raw_data: Dict[str, Any] = Field(description="原始数据")
    processed_data: Dict[str, Any] = Field(description="处理后数据")
    features: List[float] = Field(description="特征向量")
    metadata: Dict[str, Any] = Field(description="元数据")
    quality_score: float = Field(ge=0.0, le=1.0, description="数据质量评分")
    timestamp: datetime = Field(description="数据时间戳")

class CustomerValueIndicator(BaseModel):
    """客户价值指标"""
    indicator_name: str = Field(description="指标名称")
    value: float = Field(description="指标值")
    weight: float = Field(ge=0.0, le=1.0, description="权重")
    confidence: float = Field(ge=0.0, le=1.0, description="置信度")
    source_modality: DataModalityType = Field(description="数据来源模态")
    calculation_method: str = Field(description="计算方法")

class HighValueCustomerProfile(BaseModel):
    """高价值客户画像"""
    customer_id: str = Field(description="客户ID")
    overall_score: float = Field(ge=0.0, le=1.0, description="综合评分")
    value_indicators: List[CustomerValueIndicator] = Field(description="价值指标列表")
    behavioral_patterns: Dict[str, Any] = Field(description="行为模式")
    communication_preferences: Dict[str, Any] = Field(description="沟通偏好")
    engagement_history: List[Dict[str, Any]] = Field(description="参与历史")
    predicted_value: float = Field(description="预测价值")
    risk_factors: List[str] = Field(description="风险因素")
    opportunities: List[str] = Field(description="机会点")
    recommended_actions: List[str] = Field(description="推荐行动")
    last_updated: datetime = Field(description="最后更新时间")

class DataFusionResult(BaseModel):
    """数据融合结果"""
    customer_id: str = Field(description="客户ID")
    fusion_timestamp: datetime = Field(description="融合时间戳")
    input_modalities: List[DataModalityType] = Field(description="输入模态类型")
    fused_features: List[float] = Field(description="融合后特征向量")
    confidence_scores: Dict[str, float] = Field(description="各模态置信度")
    fusion_quality: float = Field(ge=0.0, le=1.0, description="融合质量")
    insights: List[str] = Field(description="洞察结果")
    anomalies: List[str] = Field(description="异常检测结果")

class MultimodalAnalysisRequest(BaseModel):
    """多模态分析请求"""
    customer_id: str = Field(description="客户ID")
    analysis_type: str = Field(description="分析类型")
    modalities: List[DataModalityType] = Field(description="要分析的模态")
    time_range: Dict[str, datetime] = Field(description="时间范围")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="分析参数")
    priority: int = Field(ge=1, le=5, default=3, description="优先级")

class MultimodalAnalysisResult(BaseModel):
    """多模态分析结果"""
    request_id: str = Field(description="请求ID")
    customer_id: str = Field(description="客户ID")
    analysis_type: str = Field(description="分析类型")
    results: Dict[str, Any] = Field(description="分析结果")
    high_value_profile: Optional[HighValueCustomerProfile] = Field(description="高价值客户画像")
    recommendations: List[str] = Field(description="推荐建议")
    confidence: float = Field(ge=0.0, le=1.0, description="结果置信度")
    processing_time: float = Field(description="处理时间(秒)")
    created_at: datetime = Field(description="创建时间")
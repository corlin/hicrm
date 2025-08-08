# 数据模型模块

from .customer import Customer, CompanySize, CustomerStatus
from .lead import Lead, LeadScore, ScoreFactor, LeadInteraction, LeadStatus, LeadSource
from .conversation import Conversation, Message, ConversationState, ConversationStatus, MessageRole
from .knowledge import (
    Knowledge, KnowledgeChunk, KnowledgeType, KnowledgeStatus,
    QualityMetrics, UsageStatistics, KnowledgeMetadata,
    KnowledgeSearchFilter, KnowledgeSearchResult, KnowledgeUpdateRequest,
    KnowledgeRelation
)
from .multimodal import (
    DataModalityType, VoiceAnalysisResult, BehaviorData, MultimodalDataPoint,
    CustomerValueIndicator, HighValueCustomerProfile, DataFusionResult,
    MultimodalAnalysisRequest, MultimodalAnalysisResult
)

__all__ = [
    "Customer",
    "CompanySize", 
    "CustomerStatus",
    "Lead",
    "LeadScore",
    "ScoreFactor",
    "LeadInteraction",
    "LeadStatus",
    "LeadSource",
    "Conversation",
    "Message",
    "ConversationState",
    "ConversationStatus",
    "MessageRole",
    "Knowledge",
    "KnowledgeChunk",
    "KnowledgeType",
    "KnowledgeStatus",
    "QualityMetrics",
    "UsageStatistics",
    "KnowledgeMetadata",
    "KnowledgeSearchFilter",
    "KnowledgeSearchResult",
    "KnowledgeUpdateRequest",
    "KnowledgeRelation",
    "DataModalityType",
    "VoiceAnalysisResult",
    "BehaviorData",
    "MultimodalDataPoint",
    "CustomerValueIndicator",
    "HighValueCustomerProfile",
    "DataFusionResult",
    "MultimodalAnalysisRequest",
    "MultimodalAnalysisResult"
]
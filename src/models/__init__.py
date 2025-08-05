# 数据模型模块

from .customer import Customer, CompanySize, CustomerStatus
from .lead import Lead, LeadScore, ScoreFactor, LeadInteraction, LeadStatus, LeadSource
from .conversation import Conversation, Message, ConversationState, ConversationStatus, MessageRole

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
    "MessageRole"
]
/**
 * 前端类型定义
 */

export interface User {
  id: string;
  name: string;
  email: string;
  avatar?: string;
  role: string;
}

export interface Conversation {
  id: string;
  title: string;
  user_id: string;
  status: 'active' | 'archived' | 'paused';
  context: Record<string, any>;
  state: Record<string, any>;
  user_preferences: Record<string, any>;
  message_count: number;
  last_activity: string;
  created_at: string;
  updated_at: string;
}

export interface Message {
  id: string;
  conversation_id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  agent_type?: string;
  agent_id?: string;
  metadata: Record<string, any>;
  confidence?: Record<string, any>;
  processing_time?: number;
  tokens_used?: number;
  created_at: string;
}

export interface AgentInfo {
  id: string;
  name: string;
  specialty: string;
  status: 'idle' | 'busy' | 'error' | 'offline';
  capabilities: string[];
  avatar?: string;
  description?: string;
}

export interface WebSocketMessage {
  type: string;
  data: Record<string, any>;
  timestamp: string;
  message_id: string;
  conversation_id?: string;
  user_id?: string;
}

export interface AgentResponse {
  content: string;
  confidence: number;
  suggestions: string[];
  next_actions: string[];
  agent_id: string;
  processing_info?: {
    processing_time?: number;
    intent?: string;
    rag_used?: boolean;
  };
  metadata?: Record<string, any>;
}

export interface TypingIndicator {
  agent_id: string;
  is_typing: boolean;
  timestamp: string;
}

export interface AgentThinking {
  agent_id: string;
  message: string;
  progress?: number;
  timestamp: string;
}

export interface AgentCollaboration {
  collaborating_agents: string[];
  collaboration_type: string;
  status: string;
  timestamp: string;
}

export interface KnowledgeRetrieval {
  status: string;
  query: string;
  results_count?: number;
  confidence?: number;
  timestamp: string;
}

export interface SystemNotification {
  notification_type: 'info' | 'warning' | 'error' | 'success';
  title: string;
  message: string;
  data?: Record<string, any>;
  timestamp: string;
}

export interface ConversationState {
  active_agents: string[];
  current_intent?: string;
  conversation_mode: 'single_agent' | 'multi_agent' | 'auto_routing';
  routing_strategy: 'intent_based' | 'capability_based' | 'load_balanced' | 'round_robin';
  context_variables: Record<string, any>;
}

export interface ChatSettings {
  theme: 'light' | 'dark' | 'system';
  language: 'zh' | 'en';
  auto_scroll: boolean;
  show_timestamps: boolean;
  show_agent_info: boolean;
  enable_sound: boolean;
  typing_indicators: boolean;
  message_grouping: boolean;
}

export interface ConnectionStatus {
  connected: boolean;
  reconnecting: boolean;
  last_connected?: string;
  error?: string;
}

// WebSocket事件类型
export enum WebSocketEventType {
  CONNECTION_ACK = 'connection_ack',
  HEARTBEAT = 'heartbeat',
  HEARTBEAT_ACK = 'heartbeat_ack',
  USER_MESSAGE = 'user_message',
  AGENT_RESPONSE = 'agent_response',
  TYPING_INDICATOR = 'typing_indicator',
  CONVERSATION_STATE = 'conversation_state',
  AGENT_STATUS = 'agent_status',
  SYSTEM_STATUS = 'system_status',
  ERROR = 'error',
  NOTIFICATION = 'notification',
  WARNING = 'warning',
  AGENT_THINKING = 'agent_thinking',
  AGENT_COLLABORATION = 'agent_collaboration',
  KNOWLEDGE_RETRIEVAL = 'knowledge_retrieval'
}

// 消息状态
export enum MessageStatus {
  SENDING = 'sending',
  SENT = 'sent',
  DELIVERED = 'delivered',
  FAILED = 'failed'
}

// Agent状态
export enum AgentStatus {
  IDLE = 'idle',
  BUSY = 'busy',
  ERROR = 'error',
  OFFLINE = 'offline'
}

// 对话模式
export enum ConversationMode {
  SINGLE_AGENT = 'single_agent',
  MULTI_AGENT = 'multi_agent',
  AUTO_ROUTING = 'auto_routing'
}

// 路由策略
export enum RoutingStrategy {
  INTENT_BASED = 'intent_based',
  CAPABILITY_BASED = 'capability_based',
  LOAD_BALANCED = 'load_balanced',
  ROUND_ROBIN = 'round_robin'
}
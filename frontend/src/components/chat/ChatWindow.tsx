/**
 * 聊天窗口主组件
 */

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { cn, scrollToBottom, copyToClipboard } from '../../lib/utils';
import { useWebSocket } from '../../hooks/useWebSocket';
import { 
  Message, 
  AgentInfo, 
  AgentResponse,
  TypingIndicator as TypingIndicatorType,
  AgentThinking as AgentThinkingType,
  AgentCollaboration,
  KnowledgeRetrieval,
  SystemNotification,
  WebSocketEventType
} from '../../types';
import { MessageBubble } from './MessageBubble';
import { TypingIndicator } from './TypingIndicator';
import { AgentThinking } from './AgentThinking';
import { ChatInput } from './ChatInput';
import { Button } from '../ui/Button';
import { 
  Settings, 
  Users, 
  Wifi, 
  WifiOff, 
  AlertCircle,
  CheckCircle,
  Info,
  Search,
  UserCheck
} from 'lucide-react';

interface ChatWindowProps {
  conversationId: string;
  userId: string;
  messages: Message[];
  agentInfos?: Record<string, AgentInfo>;
  onSendMessage?: (message: string, attachments?: File[]) => void;
  onMessageFeedback?: (messageId: string, feedback: 'positive' | 'negative') => void;
  className?: string;
}

export const ChatWindow: React.FC<ChatWindowProps> = ({
  conversationId,
  userId,
  messages: initialMessages,
  agentInfos = {},
  onSendMessage,
  onMessageFeedback,
  className
}) => {
  const [messages, setMessages] = useState<Message[]>(initialMessages);
  const [notifications, setNotifications] = useState<SystemNotification[]>([]);
  const [currentCollaboration, setCurrentCollaboration] = useState<AgentCollaboration | null>(null);
  const [currentRetrieval, setCurrentRetrieval] = useState<KnowledgeRetrieval | null>(null);
  const [autoScroll, setAutoScroll] = useState(true);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);

  // WebSocket连接
  const {
    connectionStatus,
    typingAgents,
    thinkingAgents,
    sendUserMessage,
    isConnected
  } = useWebSocket(
    {
      userId,
      conversationId,
      autoConnect: true
    },
    {
      onAgentResponse: handleAgentResponse,
      onAgentCollaboration: handleAgentCollaboration,
      onKnowledgeRetrieval: handleKnowledgeRetrieval,
      onNotification: handleNotification,
      onError: handleError
    }
  );

  // 处理Agent响应
  function handleAgentResponse(response: AgentResponse) {
    const newMessage: Message = {
      id: `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      conversation_id: conversationId,
      role: 'assistant',
      content: response.content,
      agent_type: response.agent_id,
      agent_id: response.agent_id,
      metadata: {
        confidence: response.confidence,
        suggestions: response.suggestions,
        next_actions: response.next_actions,
        processing_time: response.processing_info?.processing_time,
        intent: response.processing_info?.intent,
        rag_used: response.processing_info?.rag_used,
        ...response.metadata
      },
      created_at: new Date().toISOString()
    };

    setMessages(prev => [...prev, newMessage]);
  }

  // 处理Agent协作
  function handleAgentCollaboration(collaboration: AgentCollaboration) {
    setCurrentCollaboration(collaboration);
    
    // 5秒后清除协作状态
    setTimeout(() => {
      setCurrentCollaboration(null);
    }, 5000);
  }

  // 处理知识检索
  function handleKnowledgeRetrieval(retrieval: KnowledgeRetrieval) {
    setCurrentRetrieval(retrieval);
    
    // 如果检索完成，3秒后清除状态
    if (retrieval.status === 'completed') {
      setTimeout(() => {
        setCurrentRetrieval(null);
      }, 3000);
    }
  }

  // 处理系统通知
  function handleNotification(notification: SystemNotification) {
    setNotifications(prev => [...prev, notification]);
    
    // 5秒后自动移除通知
    setTimeout(() => {
      setNotifications(prev => prev.filter(n => n.timestamp !== notification.timestamp));
    }, 5000);
  }

  // 处理错误
  function handleError(error: string) {
    const errorNotification: SystemNotification = {
      notification_type: 'error',
      title: '连接错误',
      message: error,
      timestamp: new Date().toISOString()
    };
    handleNotification(errorNotification);
  }

  // 发送消息
  const handleSendMessage = useCallback((message: string, attachments?: File[]) => {
    if (!message.trim() && (!attachments || attachments.length === 0)) return;

    // 添加用户消息到界面
    const userMessage: Message = {
      id: `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      conversation_id: conversationId,
      role: 'user',
      content: message,
      metadata: {
        attachments: attachments?.map(f => ({ name: f.name, size: f.size, type: f.type })) || []
      },
      created_at: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);

    // 通过WebSocket发送消息
    sendUserMessage(message, { attachments: attachments?.length || 0 });

    // 调用外部处理器
    onSendMessage?.(message, attachments);
  }, [conversationId, sendUserMessage, onSendMessage]);

  // 复制消息
  const handleCopyMessage = useCallback(async (content: string) => {
    const success = await copyToClipboard(content);
    if (success) {
      const notification: SystemNotification = {
        notification_type: 'success',
        title: '复制成功',
        message: '消息已复制到剪贴板',
        timestamp: new Date().toISOString()
      };
      handleNotification(notification);
    }
  }, []);

  // 自动滚动到底部
  useEffect(() => {
    if (autoScroll && messagesEndRef.current) {
      scrollToBottom(messagesEndRef.current.parentElement as HTMLElement);
    }
  }, [messages, typingAgents, thinkingAgents, autoScroll]);

  // 检测用户是否滚动到底部
  const handleScroll = useCallback(() => {
    const container = messagesContainerRef.current;
    if (container) {
      const isAtBottom = container.scrollHeight - container.scrollTop <= container.clientHeight + 100;
      setAutoScroll(isAtBottom);
    }
  }, []);

  // 渲染连接状态
  const renderConnectionStatus = () => {
    if (isConnected) {
      return (
        <div className="flex items-center gap-2 text-green-600">
          <Wifi className="h-4 w-4" />
          <span className="text-sm">已连接</span>
        </div>
      );
    }

    if (connectionStatus.reconnecting) {
      return (
        <div className="flex items-center gap-2 text-yellow-600">
          <div className="animate-spin rounded-full h-4 w-4 border-2 border-yellow-600 border-t-transparent" />
          <span className="text-sm">重连中...</span>
        </div>
      );
    }

    return (
      <div className="flex items-center gap-2 text-red-600">
        <WifiOff className="h-4 w-4" />
        <span className="text-sm">连接断开</span>
      </div>
    );
  };

  // 渲染系统通知
  const renderNotifications = () => {
    if (notifications.length === 0) return null;

    return (
      <div className="absolute top-4 right-4 z-50 space-y-2">
        {notifications.map((notification, index) => (
          <div
            key={`${notification.timestamp}_${index}`}
            className={cn(
              "flex items-center gap-2 px-4 py-2 rounded-lg shadow-lg max-w-sm",
              notification.notification_type === 'error' && "bg-red-100 text-red-800 border border-red-200",
              notification.notification_type === 'warning' && "bg-yellow-100 text-yellow-800 border border-yellow-200",
              notification.notification_type === 'success' && "bg-green-100 text-green-800 border border-green-200",
              notification.notification_type === 'info' && "bg-blue-100 text-blue-800 border border-blue-200"
            )}
          >
            {notification.notification_type === 'error' && <AlertCircle className="h-4 w-4" />}
            {notification.notification_type === 'warning' && <AlertCircle className="h-4 w-4" />}
            {notification.notification_type === 'success' && <CheckCircle className="h-4 w-4" />}
            {notification.notification_type === 'info' && <Info className="h-4 w-4" />}
            
            <div className="flex-1">
              <div className="font-medium text-sm">{notification.title}</div>
              <div className="text-xs">{notification.message}</div>
            </div>
          </div>
        ))}
      </div>
    );
  };

  // 渲染Agent协作状态
  const renderCollaborationStatus = () => {
    if (!currentCollaboration) return null;

    return (
      <div className="agent-collaboration border rounded-lg p-3 mb-4">
        <div className="flex items-center gap-2 mb-2">
          <Users className="h-4 w-4" />
          <span className="font-medium text-sm">Agent协作中</span>
        </div>
        <div className="text-sm">
          <div>协作类型: {currentCollaboration.collaboration_type}</div>
          <div>状态: {currentCollaboration.status}</div>
          <div>参与Agent: {currentCollaboration.collaborating_agents.join(', ')}</div>
        </div>
      </div>
    );
  };

  // 渲染知识检索状态
  const renderRetrievalStatus = () => {
    if (!currentRetrieval) return null;

    return (
      <div className="knowledge-retrieval border rounded-lg p-3 mb-4">
        <div className="flex items-center gap-2 mb-2">
          <Search className="h-4 w-4" />
          <span className="font-medium text-sm">知识检索</span>
        </div>
        <div className="text-sm">
          <div>查询: {currentRetrieval.query}</div>
          <div>状态: {currentRetrieval.status}</div>
          {currentRetrieval.results_count && (
            <div>找到结果: {currentRetrieval.results_count} 条</div>
          )}
          {currentRetrieval.confidence && (
            <div>置信度: {Math.round(currentRetrieval.confidence * 100)}%</div>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className={cn("flex flex-col h-full bg-background", className)}>
      {/* 头部 */}
      <div className="flex items-center justify-between p-4 border-b">
        <div className="flex items-center gap-3">
          <h2 className="font-semibold">对话助手</h2>
          <div className="flex items-center gap-2">
            {Object.keys(agentInfos).map(agentId => (
              <div
                key={agentId}
                className="agent-status-indicator online"
                title={agentInfos[agentId].name}
              >
                <UserCheck className="h-4 w-4" />
              </div>
            ))}
          </div>
        </div>
        
        <div className="flex items-center gap-3">
          {renderConnectionStatus()}
          <Button variant="ghost" size="icon">
            <Settings className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* 消息区域 */}
      <div 
        ref={messagesContainerRef}
        className="flex-1 overflow-y-auto p-4 space-y-4 custom-scrollbar"
        onScroll={handleScroll}
      >
        {renderCollaborationStatus()}
        {renderRetrievalStatus()}
        
        {messages.map((message) => (
          <MessageBubble
            key={message.id}
            message={message}
            agentInfo={message.agent_type ? agentInfos[message.agent_type] : undefined}
            onCopy={handleCopyMessage}
            onFeedback={onMessageFeedback}
          />
        ))}

        {/* 显示正在思考的Agent */}
        {Array.from(thinkingAgents.entries()).map(([agentId, thinking]) => (
          <AgentThinking
            key={agentId}
            thinking={thinking}
            agentInfo={agentInfos[agentId]}
          />
        ))}

        {/* 显示正在输入的Agent */}
        {typingAgents.size > 0 && (
          <TypingIndicator
            agentIds={Array.from(typingAgents)}
            agentInfos={agentInfos}
          />
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* 输入区域 */}
      <div className="p-4 border-t">
        <ChatInput
          onSendMessage={handleSendMessage}
          disabled={!isConnected}
          placeholder={isConnected ? "输入消息..." : "连接断开，无法发送消息"}
        />
      </div>

      {/* 通知 */}
      {renderNotifications()}
    </div>
  );
};
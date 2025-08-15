/**
 * WebSocket连接和消息处理Hook
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import { io, Socket } from 'socket.io-client';
import {
  WebSocketMessage,
  ConnectionStatus,
  WebSocketEventType,
  AgentResponse,
  TypingIndicator,
  AgentThinking,
  AgentCollaboration,
  KnowledgeRetrieval,
  SystemNotification
} from '../types';

interface UseWebSocketOptions {
  url?: string;
  userId?: string;
  conversationId?: string;
  autoConnect?: boolean;
  reconnectAttempts?: number;
  reconnectDelay?: number;
}

interface WebSocketEvents {
  onMessage?: (message: WebSocketMessage) => void;
  onAgentResponse?: (response: AgentResponse) => void;
  onTypingIndicator?: (indicator: TypingIndicator) => void;
  onAgentThinking?: (thinking: AgentThinking) => void;
  onAgentCollaboration?: (collaboration: AgentCollaboration) => void;
  onKnowledgeRetrieval?: (retrieval: KnowledgeRetrieval) => void;
  onNotification?: (notification: SystemNotification) => void;
  onError?: (error: string) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
}

export const useWebSocket = (
  options: UseWebSocketOptions = {},
  events: WebSocketEvents = {}
) => {
  const {
    url = process.env.REACT_APP_WS_URL || 'ws://localhost:8000/ws/connect',
    userId,
    conversationId,
    autoConnect = true,
    reconnectAttempts = 5,
    reconnectDelay = 1000
  } = options;

  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>({
    connected: false,
    reconnecting: false
  });

  const [messages, setMessages] = useState<WebSocketMessage[]>([]);
  const [typingAgents, setTypingAgents] = useState<Set<string>>(new Set());
  const [thinkingAgents, setThinkingAgents] = useState<Map<string, AgentThinking>>(new Map());

  const socketRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectCountRef = useRef(0);
  const heartbeatIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // 生成客户端ID
  const clientId = useRef(
    `client_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  );

  // 构建WebSocket URL
  const buildWebSocketUrl = useCallback(() => {
    const params = new URLSearchParams();
    if (userId) params.append('user_id', userId);
    if (conversationId) params.append('conversation_id', conversationId);
    params.append('client_id', clientId.current);
    
    return `${url}?${params.toString()}`;
  }, [url, userId, conversationId]);

  // 发送心跳
  const sendHeartbeat = useCallback(() => {
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      const heartbeatMessage = {
        type: WebSocketEventType.HEARTBEAT,
        data: {},
        message_id: `heartbeat_${Date.now()}`,
        timestamp: new Date().toISOString()
      };
      socketRef.current.send(JSON.stringify(heartbeatMessage));
    }
  }, []);

  // 启动心跳
  const startHeartbeat = useCallback((interval: number = 30000) => {
    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current);
    }
    heartbeatIntervalRef.current = setInterval(sendHeartbeat, interval);
  }, [sendHeartbeat]);

  // 停止心跳
  const stopHeartbeat = useCallback(() => {
    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current);
      heartbeatIntervalRef.current = null;
    }
  }, []);

  // 处理WebSocket消息
  const handleMessage = useCallback((event: MessageEvent) => {
    try {
      const message: WebSocketMessage = JSON.parse(event.data);
      
      // 添加到消息列表
      setMessages(prev => [...prev, message]);

      // 调用通用消息处理器
      events.onMessage?.(message);

      // 根据消息类型调用特定处理器
      switch (message.type) {
        case WebSocketEventType.CONNECTION_ACK:
          setConnectionStatus(prev => ({
            ...prev,
            connected: true,
            reconnecting: false,
            last_connected: new Date().toISOString()
          }));
          reconnectCountRef.current = 0;
          
          // 启动心跳
          const heartbeatInterval = message.data.heartbeat_interval || 30000;
          startHeartbeat(heartbeatInterval);
          
          events.onConnect?.();
          break;

        case WebSocketEventType.HEARTBEAT_ACK:
          // 心跳确认，更新连接状态
          setConnectionStatus(prev => ({
            ...prev,
            last_connected: new Date().toISOString()
          }));
          break;

        case WebSocketEventType.AGENT_RESPONSE:
          const agentResponse: AgentResponse = {
            content: message.data.content,
            confidence: message.data.confidence,
            suggestions: message.data.suggestions || [],
            next_actions: message.data.next_actions || [],
            agent_id: message.data.agent_id,
            processing_info: message.data.processing_info,
            metadata: message.data.metadata
          };
          events.onAgentResponse?.(agentResponse);
          break;

        case WebSocketEventType.TYPING_INDICATOR:
          const typingIndicator: TypingIndicator = {
            agent_id: message.data.agent_id,
            is_typing: message.data.is_typing,
            timestamp: message.data.timestamp
          };
          
          setTypingAgents(prev => {
            const newSet = new Set(prev);
            if (typingIndicator.is_typing) {
              newSet.add(typingIndicator.agent_id);
            } else {
              newSet.delete(typingIndicator.agent_id);
            }
            return newSet;
          });
          
          events.onTypingIndicator?.(typingIndicator);
          break;

        case WebSocketEventType.AGENT_THINKING:
          const agentThinking: AgentThinking = {
            agent_id: message.data.agent_id,
            message: message.data.message,
            progress: message.data.progress,
            timestamp: message.data.timestamp
          };
          
          setThinkingAgents(prev => {
            const newMap = new Map(prev);
            newMap.set(agentThinking.agent_id, agentThinking);
            return newMap;
          });
          
          events.onAgentThinking?.(agentThinking);
          break;

        case WebSocketEventType.AGENT_COLLABORATION:
          const collaboration: AgentCollaboration = {
            collaborating_agents: message.data.collaborating_agents,
            collaboration_type: message.data.collaboration_type,
            status: message.data.status,
            timestamp: message.data.timestamp
          };
          events.onAgentCollaboration?.(collaboration);
          break;

        case WebSocketEventType.KNOWLEDGE_RETRIEVAL:
          const retrieval: KnowledgeRetrieval = {
            status: message.data.status,
            query: message.data.query,
            results_count: message.data.results_count,
            confidence: message.data.confidence,
            timestamp: message.data.timestamp
          };
          events.onKnowledgeRetrieval?.(retrieval);
          break;

        case WebSocketEventType.NOTIFICATION:
          const notification: SystemNotification = {
            notification_type: message.data.notification_type,
            title: message.data.title,
            message: message.data.message,
            data: message.data.data,
            timestamp: message.data.timestamp
          };
          events.onNotification?.(notification);
          break;

        case WebSocketEventType.ERROR:
          const errorMessage = message.data.error || '未知错误';
          setConnectionStatus(prev => ({
            ...prev,
            error: errorMessage
          }));
          events.onError?.(errorMessage);
          break;

        default:
          console.log('未处理的WebSocket消息类型:', message.type);
      }
    } catch (error) {
      console.error('解析WebSocket消息失败:', error);
      events.onError?.('消息解析失败');
    }
  }, [events, startHeartbeat]);

  // 连接WebSocket
  const connect = useCallback(() => {
    if (socketRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    try {
      const wsUrl = buildWebSocketUrl();
      socketRef.current = new WebSocket(wsUrl);

      socketRef.current.onopen = () => {
        console.log('WebSocket连接已建立');
      };

      socketRef.current.onmessage = handleMessage;

      socketRef.current.onclose = (event) => {
        console.log('WebSocket连接已关闭:', event.code, event.reason);
        
        setConnectionStatus(prev => ({
          ...prev,
          connected: false,
          error: event.reason || '连接已关闭'
        }));

        stopHeartbeat();
        setTypingAgents(new Set());
        setThinkingAgents(new Map());
        
        events.onDisconnect?.();

        // 自动重连
        if (reconnectCountRef.current < reconnectAttempts) {
          setConnectionStatus(prev => ({
            ...prev,
            reconnecting: true
          }));

          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectCountRef.current++;
            connect();
          }, reconnectDelay * Math.pow(2, reconnectCountRef.current));
        }
      };

      socketRef.current.onerror = (error) => {
        console.error('WebSocket错误:', error);
        events.onError?.('连接错误');
      };

    } catch (error) {
      console.error('创建WebSocket连接失败:', error);
      events.onError?.('创建连接失败');
    }
  }, [buildWebSocketUrl, handleMessage, events, reconnectAttempts, reconnectDelay, stopHeartbeat]);

  // 断开连接
  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    stopHeartbeat();

    if (socketRef.current) {
      socketRef.current.close(1000, '用户主动断开');
      socketRef.current = null;
    }

    setConnectionStatus({
      connected: false,
      reconnecting: false
    });

    setTypingAgents(new Set());
    setThinkingAgents(new Map());
  }, [stopHeartbeat]);

  // 发送消息
  const sendMessage = useCallback((
    type: WebSocketEventType,
    data: Record<string, any>,
    messageId?: string
  ) => {
    if (!socketRef.current || socketRef.current.readyState !== WebSocket.OPEN) {
      events.onError?.('连接未建立');
      return false;
    }

    try {
      const message: WebSocketMessage = {
        type,
        data,
        timestamp: new Date().toISOString(),
        message_id: messageId || `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        conversation_id: conversationId,
        user_id: userId
      };

      socketRef.current.send(JSON.stringify(message));
      return true;
    } catch (error) {
      console.error('发送WebSocket消息失败:', error);
      events.onError?.('发送消息失败');
      return false;
    }
  }, [conversationId, userId, events]);

  // 发送用户消息
  const sendUserMessage = useCallback((content: string, context?: Record<string, any>) => {
    return sendMessage(WebSocketEventType.USER_MESSAGE, {
      content,
      context: context || {}
    });
  }, [sendMessage]);

  // 加入对话
  const joinConversation = useCallback((newConversationId: string) => {
    return sendMessage(WebSocketEventType.CONVERSATION_STATE, {
      action: 'join',
      conversation_id: newConversationId
    });
  }, [sendMessage]);

  // 订阅事件
  const subscribe = useCallback((eventTypes: string[]) => {
    return sendMessage(WebSocketEventType.NOTIFICATION, {
      action: 'subscribe',
      event_types: eventTypes
    });
  }, [sendMessage]);

  // 自动连接
  useEffect(() => {
    if (autoConnect) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [autoConnect, connect, disconnect]);

  // 清理定时器
  useEffect(() => {
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (heartbeatIntervalRef.current) {
        clearInterval(heartbeatIntervalRef.current);
      }
    };
  }, []);

  return {
    connectionStatus,
    messages,
    typingAgents,
    thinkingAgents,
    connect,
    disconnect,
    sendMessage,
    sendUserMessage,
    joinConversation,
    subscribe,
    isConnected: connectionStatus.connected,
    isReconnecting: connectionStatus.reconnecting
  };
};
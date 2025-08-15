/**
 * ChatWindow组件测试
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { ChatWindow } from '../ChatWindow';
import { Message, AgentInfo } from '../../../types';

// Mock WebSocket hook
jest.mock('../../../hooks/useWebSocket', () => ({
  useWebSocket: () => ({
    connectionStatus: { connected: true, reconnecting: false },
    typingAgents: new Set(),
    thinkingAgents: new Map(),
    sendUserMessage: jest.fn(),
    isConnected: true
  })
}));

const mockMessages: Message[] = [
  {
    id: 'msg_1',
    conversation_id: 'conv_123',
    role: 'assistant',
    content: '您好！我是您的CRM助手。',
    agent_type: 'crm_expert_agent',
    agent_id: 'crm_expert_agent',
    metadata: {
      confidence: 0.9,
      suggestions: ['查看客户', '创建线索']
    },
    created_at: '2024-01-01T10:00:00Z'
  },
  {
    id: 'msg_2',
    conversation_id: 'conv_123',
    role: 'user',
    content: '帮我查找一些客户',
    metadata: {},
    created_at: '2024-01-01T10:01:00Z'
  }
];

const mockAgentInfos: Record<string, AgentInfo> = {
  'crm_expert_agent': {
    id: 'crm_expert_agent',
    name: 'CRM专家',
    specialty: 'CRM最佳实践',
    status: 'idle',
    capabilities: ['best_practices'],
    avatar: '🎓'
  }
};

describe('ChatWindow', () => {
  const defaultProps = {
    conversationId: 'conv_123',
    userId: 'user_456',
    messages: mockMessages,
    agentInfos: mockAgentInfos
  };

  beforeEach(() => {
    // 清除所有mock
    jest.clearAllMocks();
  });

  test('渲染聊天窗口', () => {
    render(<ChatWindow {...defaultProps} />);
    
    // 检查标题
    expect(screen.getByText('对话助手')).toBeInTheDocument();
    
    // 检查连接状态
    expect(screen.getByText('已连接')).toBeInTheDocument();
    
    // 检查消息
    expect(screen.getByText('您好！我是您的CRM助手。')).toBeInTheDocument();
    expect(screen.getByText('帮我查找一些客户')).toBeInTheDocument();
  });

  test('显示Agent信息', () => {
    render(<ChatWindow {...defaultProps} />);
    
    // 检查Agent名称
    expect(screen.getByText('CRM专家')).toBeInTheDocument();
    
    // 检查置信度
    expect(screen.getByText('置信度: 90%')).toBeInTheDocument();
  });

  test('显示消息建议', () => {
    render(<ChatWindow {...defaultProps} />);
    
    // 检查建议按钮
    expect(screen.getByText('查看客户')).toBeInTheDocument();
    expect(screen.getByText('创建线索')).toBeInTheDocument();
  });

  test('发送消息', async () => {
    const mockOnSendMessage = jest.fn();
    
    render(
      <ChatWindow 
        {...defaultProps} 
        onSendMessage={mockOnSendMessage}
      />
    );
    
    // 找到输入框
    const input = screen.getByPlaceholderText('输入消息...');
    const sendButton = screen.getByRole('button', { name: /send/i });
    
    // 输入消息
    fireEvent.change(input, { target: { value: '测试消息' } });
    
    // 点击发送
    fireEvent.click(sendButton);
    
    // 验证回调被调用
    await waitFor(() => {
      expect(mockOnSendMessage).toHaveBeenCalledWith('测试消息', undefined);
    });
  });

  test('复制消息', async () => {
    // Mock clipboard API
    Object.assign(navigator, {
      clipboard: {
        writeText: jest.fn().mockResolvedValue(undefined)
      }
    });

    render(<ChatWindow {...defaultProps} />);
    
    // 找到复制按钮（需要hover才显示）
    const messageElement = screen.getByText('您好！我是您的CRM助手。').closest('.group');
    
    if (messageElement) {
      fireEvent.mouseEnter(messageElement);
      
      const copyButton = screen.getByTitle('复制消息');
      fireEvent.click(copyButton);
      
      await waitFor(() => {
        expect(navigator.clipboard.writeText).toHaveBeenCalledWith('您好！我是您的CRM助手。');
      });
    }
  });

  test('消息反馈', () => {
    const mockOnMessageFeedback = jest.fn();
    
    render(
      <ChatWindow 
        {...defaultProps} 
        onMessageFeedback={mockOnMessageFeedback}
      />
    );
    
    // 找到Assistant消息的反馈按钮
    const messageElement = screen.getByText('您好！我是您的CRM助手。').closest('.group');
    
    if (messageElement) {
      fireEvent.mouseEnter(messageElement);
      
      const thumbsUpButton = screen.getByTitle('有用');
      fireEvent.click(thumbsUpButton);
      
      expect(mockOnMessageFeedback).toHaveBeenCalledWith('msg_1', 'positive');
    }
  });

  test('显示断开连接状态', () => {
    // Mock断开连接的WebSocket状态
    jest.doMock('../../../hooks/useWebSocket', () => ({
      useWebSocket: () => ({
        connectionStatus: { connected: false, reconnecting: false },
        typingAgents: new Set(),
        thinkingAgents: new Map(),
        sendUserMessage: jest.fn(),
        isConnected: false
      })
    }));

    render(<ChatWindow {...defaultProps} />);
    
    expect(screen.getByText('连接断开')).toBeInTheDocument();
  });

  test('显示重连状态', () => {
    // Mock重连中的WebSocket状态
    jest.doMock('../../../hooks/useWebSocket', () => ({
      useWebSocket: () => ({
        connectionStatus: { connected: false, reconnecting: true },
        typingAgents: new Set(),
        thinkingAgents: new Map(),
        sendUserMessage: jest.fn(),
        isConnected: false
      })
    }));

    render(<ChatWindow {...defaultProps} />);
    
    expect(screen.getByText('重连中...')).toBeInTheDocument();
  });

  test('键盘快捷键发送消息', async () => {
    const mockOnSendMessage = jest.fn();
    
    render(
      <ChatWindow 
        {...defaultProps} 
        onSendMessage={mockOnSendMessage}
      />
    );
    
    const input = screen.getByPlaceholderText('输入消息...');
    
    // 输入消息
    fireEvent.change(input, { target: { value: '快捷键测试' } });
    
    // 按Enter发送
    fireEvent.keyDown(input, { key: 'Enter', code: 'Enter' });
    
    await waitFor(() => {
      expect(mockOnSendMessage).toHaveBeenCalledWith('快捷键测试', undefined);
    });
  });

  test('Shift+Enter换行', () => {
    render(<ChatWindow {...defaultProps} />);
    
    const input = screen.getByPlaceholderText('输入消息...');
    
    // 输入消息
    fireEvent.change(input, { target: { value: '第一行' } });
    
    // 按Shift+Enter换行
    fireEvent.keyDown(input, { 
      key: 'Enter', 
      code: 'Enter', 
      shiftKey: true 
    });
    
    // 消息不应该被发送，输入框应该还有内容
    expect(input).toHaveValue('第一行');
  });
});
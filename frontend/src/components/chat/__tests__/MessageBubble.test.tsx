/**
 * MessageBubble组件测试
 */

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { MessageBubble } from '../MessageBubble';
import { Message, AgentInfo } from '../../../types';

const mockUserMessage: Message = {
  id: 'msg_user',
  conversation_id: 'conv_123',
  role: 'user',
  content: '这是用户消息',
  metadata: {},
  created_at: '2024-01-01T10:00:00Z'
};

const mockAgentMessage: Message = {
  id: 'msg_agent',
  conversation_id: 'conv_123',
  role: 'assistant',
  content: '这是Agent响应',
  agent_type: 'sales_agent',
  agent_id: 'sales_agent',
  metadata: {
    confidence: 0.85,
    suggestions: ['查看详情', '创建任务'],
    processing_time: 1.2,
    intent: 'customer_search',
    rag_used: true
  },
  created_at: '2024-01-01T10:01:00Z'
};

const mockAgentInfo: AgentInfo = {
  id: 'sales_agent',
  name: '销售助手',
  specialty: '客户管理',
  status: 'idle',
  capabilities: ['customer_management'],
  avatar: '👨‍💼'
};

describe('MessageBubble', () => {
  test('渲染用户消息', () => {
    render(<MessageBubble message={mockUserMessage} />);
    
    expect(screen.getByText('这是用户消息')).toBeInTheDocument();
    
    // 用户消息应该在右侧
    const bubble = screen.getByText('这是用户消息').closest('.message-bubble');
    expect(bubble).toHaveClass('user');
  });

  test('渲染Agent消息', () => {
    render(
      <MessageBubble 
        message={mockAgentMessage} 
        agentInfo={mockAgentInfo}
      />
    );
    
    expect(screen.getByText('这是Agent响应')).toBeInTheDocument();
    
    // Agent消息应该在左侧
    const bubble = screen.getByText('这是Agent响应').closest('.message-bubble');
    expect(bubble).toHaveClass('agent');
  });

  test('显示Agent信息', () => {
    render(
      <MessageBubble 
        message={mockAgentMessage} 
        agentInfo={mockAgentInfo}
        showAgentInfo={true}
      />
    );
    
    expect(screen.getByText('销售助手')).toBeInTheDocument();
    expect(screen.getByText('置信度: 85%')).toBeInTheDocument();
  });

  test('显示处理信息', () => {
    render(<MessageBubble message={mockAgentMessage} />);
    
    expect(screen.getByText('处理时间: 1.20s')).toBeInTheDocument();
    expect(screen.getByText('意图: customer_search')).toBeInTheDocument();
    expect(screen.getByText('🔍 使用了知识库')).toBeInTheDocument();
  });

  test('显示建议操作', () => {
    render(<MessageBubble message={mockAgentMessage} />);
    
    expect(screen.getByText('建议操作:')).toBeInTheDocument();
    expect(screen.getByText('查看详情')).toBeInTheDocument();
    expect(screen.getByText('创建任务')).toBeInTheDocument();
  });

  test('显示时间戳', () => {
    render(<MessageBubble message={mockUserMessage} showTimestamp={true} />);
    
    // 时间戳应该显示（具体格式取决于formatRelativeTime函数）
    const timestampElement = screen.getByText(/\d+:\d+/);
    expect(timestampElement).toBeInTheDocument();
  });

  test('隐藏时间戳', () => {
    render(<MessageBubble message={mockUserMessage} showTimestamp={false} />);
    
    // 不应该有时间戳
    const timestampElements = screen.queryAllByText(/\d+:\d+/);
    expect(timestampElements).toHaveLength(0);
  });

  test('复制消息功能', () => {
    const mockOnCopy = jest.fn();
    
    render(
      <MessageBubble 
        message={mockUserMessage} 
        onCopy={mockOnCopy}
      />
    );
    
    // 需要hover才能看到操作按钮
    const messageElement = screen.getByText('这是用户消息').closest('.group');
    fireEvent.mouseEnter(messageElement!);
    
    const copyButton = screen.getByTitle('复制消息');
    fireEvent.click(copyButton);
    
    expect(mockOnCopy).toHaveBeenCalledWith('这是用户消息');
  });

  test('消息反馈功能', () => {
    const mockOnFeedback = jest.fn();
    
    render(
      <MessageBubble 
        message={mockAgentMessage} 
        onFeedback={mockOnFeedback}
      />
    );
    
    // 需要hover才能看到操作按钮
    const messageElement = screen.getByText('这是Agent响应').closest('.group');
    fireEvent.mouseEnter(messageElement!);
    
    const thumbsUpButton = screen.getByTitle('有用');
    const thumbsDownButton = screen.getByTitle('无用');
    
    fireEvent.click(thumbsUpButton);
    expect(mockOnFeedback).toHaveBeenCalledWith('msg_agent', 'positive');
    
    fireEvent.click(thumbsDownButton);
    expect(mockOnFeedback).toHaveBeenCalledWith('msg_agent', 'negative');
  });

  test('建议操作点击', () => {
    const consoleSpy = jest.spyOn(console, 'log').mockImplementation();
    
    render(<MessageBubble message={mockAgentMessage} />);
    
    const suggestionButton = screen.getByText('查看详情');
    fireEvent.click(suggestionButton);
    
    expect(consoleSpy).toHaveBeenCalledWith('执行建议:', '查看详情');
    
    consoleSpy.mockRestore();
  });

  test('系统消息样式', () => {
    const systemMessage: Message = {
      ...mockUserMessage,
      role: 'system',
      content: '系统消息'
    };
    
    render(<MessageBubble message={systemMessage} />);
    
    const bubble = screen.getByText('系统消息').closest('.message-bubble');
    expect(bubble).toHaveClass('bg-yellow-50');
  });

  test('用户消息不显示反馈按钮', () => {
    render(<MessageBubble message={mockUserMessage} />);
    
    const messageElement = screen.getByText('这是用户消息').closest('.group');
    fireEvent.mouseEnter(messageElement!);
    
    // 用户消息不应该有反馈按钮
    expect(screen.queryByTitle('有用')).not.toBeInTheDocument();
    expect(screen.queryByTitle('无用')).not.toBeInTheDocument();
  });

  test('长消息换行', () => {
    const longMessage: Message = {
      ...mockUserMessage,
      content: '这是一条非常长的消息，应该会自动换行显示，测试文本换行功能是否正常工作。'.repeat(5)
    };
    
    render(<MessageBubble message={longMessage} />);
    
    const bubble = screen.getByText(longMessage.content).closest('.message-bubble');
    expect(bubble).toHaveClass('break-words');
  });
});
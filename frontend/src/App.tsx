/**
 * 主应用组件
 */

import React, { useState, useEffect } from 'react';
import { ChatWindow } from './components/chat/ChatWindow';
import { AgentInfo, Message } from './types';
import './index.css';

// 模拟Agent信息
const mockAgentInfos: Record<string, AgentInfo> = {
  'sales_agent': {
    id: 'sales_agent',
    name: '销售助手',
    specialty: '客户管理和销售流程',
    status: 'idle',
    capabilities: ['customer_management', 'sales_process', 'negotiation'],
    avatar: '👨‍💼',
    description: '专业的销售顾问，帮助您管理客户关系和推进销售流程'
  },
  'market_agent': {
    id: 'market_agent',
    name: '市场分析师',
    specialty: '市场分析和线索管理',
    status: 'idle',
    capabilities: ['market_analysis', 'lead_management', 'competitive_analysis'],
    avatar: '📊',
    description: '市场分析专家，提供市场洞察和线索评估'
  },
  'product_agent': {
    id: 'product_agent',
    name: '产品顾问',
    specialty: '产品匹配和技术方案',
    status: 'idle',
    capabilities: ['product_matching', 'technical_solution', 'implementation'],
    avatar: '🔧',
    description: '产品专家，帮助匹配最适合的产品方案'
  },
  'crm_expert_agent': {
    id: 'crm_expert_agent',
    name: 'CRM专家',
    specialty: 'CRM最佳实践和流程优化',
    status: 'idle',
    capabilities: ['best_practices', 'process_optimization', 'knowledge_management'],
    avatar: '🎓',
    description: 'CRM领域专家，提供最佳实践指导'
  }
};

// 模拟初始消息
const mockMessages: Message[] = [
  {
    id: 'msg_1',
    conversation_id: 'conv_123',
    role: 'assistant',
    content: '您好！我是您的CRM智能助手。我可以帮助您管理客户关系、分析销售数据、优化业务流程等。请告诉我您需要什么帮助？',
    agent_type: 'crm_expert_agent',
    agent_id: 'crm_expert_agent',
    metadata: {
      confidence: 1.0,
      suggestions: ['查看客户列表', '分析销售数据', '创建新线索', '查看今日任务'],
      processing_time: 0.1
    },
    created_at: new Date().toISOString()
  }
];

function App() {
  const [conversationId] = useState('conv_123');
  const [userId] = useState('user_456');
  const [messages, setMessages] = useState<Message[]>(mockMessages);

  // 处理发送消息
  const handleSendMessage = (message: string, attachments?: File[]) => {
    console.log('发送消息:', message, attachments);
    
    // 这里可以调用API发送消息到后端
    // 实际实现中，消息会通过WebSocket发送到后端，然后Agent处理后返回响应
  };

  // 处理消息反馈
  const handleMessageFeedback = (messageId: string, feedback: 'positive' | 'negative') => {
    console.log('消息反馈:', messageId, feedback);
    
    // 这里可以调用API记录用户反馈
  };

  return (
    <div className="h-screen w-screen bg-background">
      <ChatWindow
        conversationId={conversationId}
        userId={userId}
        messages={messages}
        agentInfos={mockAgentInfos}
        onSendMessage={handleSendMessage}
        onMessageFeedback={handleMessageFeedback}
        className="h-full"
      />
    </div>
  );
}

export default App;
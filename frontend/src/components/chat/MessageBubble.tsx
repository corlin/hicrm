/**
 * 消息气泡组件
 */

import React from 'react';
import { cn, formatRelativeTime, getAgentColor, getAgentAvatar } from '../../lib/utils';
import { Message, AgentInfo } from '../../types';
import { Button } from '../ui/Button';
import { Copy, ThumbsUp, ThumbsDown, MoreHorizontal } from 'lucide-react';

interface MessageBubbleProps {
  message: Message;
  agentInfo?: AgentInfo;
  showTimestamp?: boolean;
  showAgentInfo?: boolean;
  onCopy?: (content: string) => void;
  onFeedback?: (messageId: string, feedback: 'positive' | 'negative') => void;
  className?: string;
}

export const MessageBubble: React.FC<MessageBubbleProps> = ({
  message,
  agentInfo,
  showTimestamp = true,
  showAgentInfo = true,
  onCopy,
  onFeedback,
  className
}) => {
  const isUser = message.role === 'user';
  const isSystem = message.role === 'system';

  const handleCopy = () => {
    onCopy?.(message.content);
  };

  const handleFeedback = (feedback: 'positive' | 'negative') => {
    onFeedback?.(message.id, feedback);
  };

  const renderAgentInfo = () => {
    if (isUser || !showAgentInfo || !message.agent_type) return null;

    const agentName = agentInfo?.name || message.agent_type;
    const agentAvatar = agentInfo?.avatar || getAgentAvatar(message.agent_type);
    const agentColor = getAgentColor(message.agent_type);

    return (
      <div className="flex items-center gap-2 mb-2">
        <div className={cn(
          "w-6 h-6 rounded-full flex items-center justify-center text-white text-xs",
          agentColor
        )}>
          {agentAvatar}
        </div>
        <span className="text-sm font-medium text-muted-foreground">
          {agentName}
        </span>
        {message.metadata?.confidence && (
          <span className="text-xs text-muted-foreground">
            置信度: {Math.round(message.metadata.confidence * 100)}%
          </span>
        )}
      </div>
    );
  };

  const renderProcessingInfo = () => {
    if (isUser || !message.metadata?.processing_time) return null;

    return (
      <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
        <span>
          处理时间: {message.metadata.processing_time.toFixed(2)}s
        </span>
        {message.metadata?.intent && (
          <span>
            意图: {message.metadata.intent}
          </span>
        )}
        {message.metadata?.rag_used && (
          <span className="text-blue-600">
            🔍 使用了知识库
          </span>
        )}
      </div>
    );
  };

  const renderSuggestions = () => {
    const suggestions = message.metadata?.suggestions;
    if (!suggestions || suggestions.length === 0) return null;

    return (
      <div className="mt-3 space-y-2">
        <div className="text-sm font-medium text-muted-foreground">
          建议操作:
        </div>
        <div className="flex flex-wrap gap-2">
          {suggestions.map((suggestion: string, index: number) => (
            <Button
              key={index}
              variant="outline"
              size="sm"
              className="text-xs"
              onClick={() => {
                // 这里可以触发建议操作
                console.log('执行建议:', suggestion);
              }}
            >
              {suggestion}
            </Button>
          ))}
        </div>
      </div>
    );
  };

  const renderActions = () => {
    if (isSystem) return null;

    return (
      <div className="flex items-center gap-1 mt-2 opacity-0 group-hover:opacity-100 transition-opacity">
        <Button
          variant="ghost"
          size="icon"
          className="h-6 w-6"
          onClick={handleCopy}
          title="复制消息"
        >
          <Copy className="h-3 w-3" />
        </Button>
        
        {!isUser && (
          <>
            <Button
              variant="ghost"
              size="icon"
              className="h-6 w-6"
              onClick={() => handleFeedback('positive')}
              title="有用"
            >
              <ThumbsUp className="h-3 w-3" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              className="h-6 w-6"
              onClick={() => handleFeedback('negative')}
              title="无用"
            >
              <ThumbsDown className="h-3 w-3" />
            </Button>
          </>
        )}
        
        <Button
          variant="ghost"
          size="icon"
          className="h-6 w-6"
          title="更多操作"
        >
          <MoreHorizontal className="h-3 w-3" />
        </Button>
      </div>
    );
  };

  return (
    <div className={cn(
      "group flex flex-col gap-1 max-w-[80%]",
      isUser ? "ml-auto items-end" : "mr-auto items-start",
      className
    )}>
      {renderAgentInfo()}
      
      <div className={cn(
        "message-bubble rounded-lg px-4 py-2 relative",
        isUser && "user",
        !isUser && "agent",
        isSystem && "bg-yellow-50 border border-yellow-200 text-yellow-800 dark:bg-yellow-950 dark:border-yellow-800 dark:text-yellow-200"
      )}>
        <div className="whitespace-pre-wrap break-words">
          {message.content}
        </div>
        
        {renderProcessingInfo()}
        {renderSuggestions()}
        {renderActions()}
      </div>
      
      {showTimestamp && (
        <div className={cn(
          "text-xs text-muted-foreground px-2",
          isUser ? "text-right" : "text-left"
        )}>
          {formatRelativeTime(message.created_at)}
        </div>
      )}
    </div>
  );
};
/**
 * 打字指示器组件
 */

import React from 'react';
import { cn, getAgentColor, getAgentAvatar } from '../../lib/utils';
import { AgentInfo } from '../../types';

interface TypingIndicatorProps {
  agentIds: string[];
  agentInfos?: Record<string, AgentInfo>;
  className?: string;
}

export const TypingIndicator: React.FC<TypingIndicatorProps> = ({
  agentIds,
  agentInfos = {},
  className
}) => {
  if (agentIds.length === 0) return null;

  const renderAgentTyping = (agentId: string) => {
    const agentInfo = agentInfos[agentId];
    const agentName = agentInfo?.name || agentId;
    const agentAvatar = agentInfo?.avatar || getAgentAvatar(agentId);
    const agentColor = getAgentColor(agentId);

    return (
      <div key={agentId} className="flex items-center gap-2">
        <div className={cn(
          "w-6 h-6 rounded-full flex items-center justify-center text-white text-xs",
          agentColor
        )}>
          {agentAvatar}
        </div>
        <span className="text-sm text-muted-foreground">
          {agentName}
        </span>
      </div>
    );
  };

  return (
    <div className={cn(
      "flex flex-col gap-2 max-w-[80%] mr-auto items-start",
      className
    )}>
      {agentIds.map(renderAgentTyping)}
      
      <div className="bg-muted text-muted-foreground rounded-lg px-4 py-3 relative">
        <div className="flex items-center gap-2">
          <div className="typing-dots">
            <span></span>
            <span></span>
            <span></span>
          </div>
          <span className="text-sm">正在输入...</span>
        </div>
      </div>
    </div>
  );
};
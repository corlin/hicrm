/**
 * Agent思考状态组件
 */

import React from 'react';
import { cn, getAgentColor, getAgentAvatar } from '../../lib/utils';
import { AgentThinking as AgentThinkingType, AgentInfo } from '../../types';
import { Brain, Loader2 } from 'lucide-react';

interface AgentThinkingProps {
  thinking: AgentThinkingType;
  agentInfo?: AgentInfo;
  className?: string;
}

export const AgentThinking: React.FC<AgentThinkingProps> = ({
  thinking,
  agentInfo,
  className
}) => {
  const agentName = agentInfo?.name || thinking.agent_id;
  const agentAvatar = agentInfo?.avatar || getAgentAvatar(thinking.agent_id);
  const agentColor = getAgentColor(thinking.agent_id);

  return (
    <div className={cn(
      "flex flex-col gap-2 max-w-[80%] mr-auto items-start",
      className
    )}>
      <div className="flex items-center gap-2">
        <div className={cn(
          "w-6 h-6 rounded-full flex items-center justify-center text-white text-xs",
          agentColor
        )}>
          {agentAvatar}
        </div>
        <span className="text-sm font-medium text-muted-foreground">
          {agentName}
        </span>
      </div>
      
      <div className="bg-blue-50 border border-blue-200 text-blue-800 dark:bg-blue-950 dark:border-blue-800 dark:text-blue-200 rounded-lg px-4 py-3 relative">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <Brain className="h-4 w-4 animate-pulse-slow" />
            <Loader2 className="h-3 w-3 animate-spin" />
          </div>
          
          <div className="flex-1">
            <div className="text-sm font-medium">
              {thinking.message}
            </div>
            
            {thinking.progress !== undefined && (
              <div className="mt-2">
                <div className="flex items-center justify-between text-xs mb-1">
                  <span>进度</span>
                  <span>{Math.round(thinking.progress * 100)}%</span>
                </div>
                <div className="w-full bg-blue-200 dark:bg-blue-800 rounded-full h-1.5">
                  <div 
                    className="bg-blue-600 dark:bg-blue-400 h-1.5 rounded-full transition-all duration-300"
                    style={{ width: `${thinking.progress * 100}%` }}
                  />
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
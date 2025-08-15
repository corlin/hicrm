/**
 * 聊天输入组件
 */

import React, { useState, useRef, useCallback, useEffect } from 'react';
import { cn } from '../../lib/utils';
import { Button } from '../ui/Button';
import { Send, Paperclip, Mic, MicOff, Smile } from 'lucide-react';

interface ChatInputProps {
  onSendMessage: (message: string, attachments?: File[]) => void;
  disabled?: boolean;
  placeholder?: string;
  maxLength?: number;
  showAttachments?: boolean;
  showVoice?: boolean;
  showEmoji?: boolean;
  className?: string;
}

export const ChatInput: React.FC<ChatInputProps> = ({
  onSendMessage,
  disabled = false,
  placeholder = "输入消息...",
  maxLength = 1000,
  showAttachments = true,
  showVoice = true,
  showEmoji = true,
  className
}) => {
  const [message, setMessage] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [attachments, setAttachments] = useState<File[]>([]);
  
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);

  // 自动调整文本框高度
  const adjustTextareaHeight = useCallback(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = `${Math.min(textarea.scrollHeight, 120)}px`;
    }
  }, []);

  // 处理输入变化
  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const value = e.target.value;
    if (value.length <= maxLength) {
      setMessage(value);
    }
  };

  // 处理键盘事件
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  // 发送消息
  const handleSendMessage = () => {
    const trimmedMessage = message.trim();
    if (trimmedMessage || attachments.length > 0) {
      onSendMessage(trimmedMessage, attachments);
      setMessage('');
      setAttachments([]);
      
      // 重置文本框高度
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };

  // 处理文件选择
  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    setAttachments(prev => [...prev, ...files]);
    
    // 清空input以允许重复选择同一文件
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  // 移除附件
  const removeAttachment = (index: number) => {
    setAttachments(prev => prev.filter((_, i) => i !== index));
  };

  // 开始录音
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      
      const chunks: Blob[] = [];
      
      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          chunks.push(e.data);
        }
      };
      
      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(chunks, { type: 'audio/webm' });
        const audioFile = new File([audioBlob], `recording_${Date.now()}.webm`, {
          type: 'audio/webm'
        });
        setAttachments(prev => [...prev, audioFile]);
        
        // 停止所有音频轨道
        stream.getTracks().forEach(track => track.stop());
      };
      
      mediaRecorder.start();
      setIsRecording(true);
    } catch (error) {
      console.error('无法访问麦克风:', error);
    }
  };

  // 停止录音
  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  // 处理语音按钮点击
  const handleVoiceClick = () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  // 自动调整高度
  useEffect(() => {
    adjustTextareaHeight();
  }, [message, adjustTextareaHeight]);

  // 渲染附件预览
  const renderAttachments = () => {
    if (attachments.length === 0) return null;

    return (
      <div className="flex flex-wrap gap-2 p-2 border-t">
        {attachments.map((file, index) => (
          <div
            key={index}
            className="flex items-center gap-2 bg-muted rounded px-2 py-1 text-sm"
          >
            <span className="truncate max-w-[100px]">
              {file.name}
            </span>
            <button
              onClick={() => removeAttachment(index)}
              className="text-muted-foreground hover:text-foreground"
            >
              ×
            </button>
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className={cn("border rounded-lg bg-background", className)}>
      {renderAttachments()}
      
      <div className="flex items-end gap-2 p-3">
        {/* 附件按钮 */}
        {showAttachments && (
          <Button
            variant="ghost"
            size="icon"
            onClick={() => fileInputRef.current?.click()}
            disabled={disabled}
            className="shrink-0"
          >
            <Paperclip className="h-4 w-4" />
          </Button>
        )}

        {/* 文本输入区域 */}
        <div className="flex-1 relative">
          <textarea
            ref={textareaRef}
            value={message}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            disabled={disabled}
            className={cn(
              "w-full resize-none border-0 bg-transparent px-3 py-2 text-sm",
              "placeholder:text-muted-foreground",
              "focus-visible:outline-none",
              "min-h-[40px] max-h-[120px]"
            )}
            rows={1}
          />
          
          {/* 字符计数 */}
          {message.length > maxLength * 0.8 && (
            <div className="absolute bottom-1 right-1 text-xs text-muted-foreground">
              {message.length}/{maxLength}
            </div>
          )}
        </div>

        {/* 表情按钮 */}
        {showEmoji && (
          <Button
            variant="ghost"
            size="icon"
            disabled={disabled}
            className="shrink-0"
          >
            <Smile className="h-4 w-4" />
          </Button>
        )}

        {/* 语音按钮 */}
        {showVoice && (
          <Button
            variant="ghost"
            size="icon"
            onClick={handleVoiceClick}
            disabled={disabled}
            className={cn(
              "shrink-0",
              isRecording && "text-red-500 animate-pulse"
            )}
          >
            {isRecording ? (
              <MicOff className="h-4 w-4" />
            ) : (
              <Mic className="h-4 w-4" />
            )}
          </Button>
        )}

        {/* 发送按钮 */}
        <Button
          onClick={handleSendMessage}
          disabled={disabled || (!message.trim() && attachments.length === 0)}
          size="icon"
          className="shrink-0"
        >
          <Send className="h-4 w-4" />
        </Button>
      </div>

      {/* 隐藏的文件输入 */}
      <input
        ref={fileInputRef}
        type="file"
        multiple
        onChange={handleFileSelect}
        className="hidden"
        accept="image/*,audio/*,video/*,.pdf,.doc,.docx,.txt"
      />
    </div>
  );
};
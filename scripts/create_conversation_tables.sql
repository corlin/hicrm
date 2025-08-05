-- 创建对话相关表的SQL脚本

-- 对话状态枚举类型
CREATE TYPE conversation_status AS ENUM ('active', 'paused', 'completed', 'archived');
CREATE TYPE message_role AS ENUM ('user', 'assistant', 'system', 'agent');

-- 对话表
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    title VARCHAR(500),
    status conversation_status DEFAULT 'active',
    
    -- 对话上下文和状态
    context JSONB DEFAULT '{}',
    state JSONB DEFAULT '{}',
    meta_data JSONB DEFAULT '{}',
    
    -- 用户偏好和学习数据
    user_preferences JSONB DEFAULT '{}',
    learned_patterns JSONB DEFAULT '{}',
    
    -- 统计信息
    message_count INTEGER DEFAULT 0,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 消息表
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    
    role message_role NOT NULL,
    content TEXT NOT NULL,
    
    -- Agent相关信息
    agent_type VARCHAR(100),
    agent_id VARCHAR(255),
    
    -- 消息元数据
    meta_data JSONB DEFAULT '{}',
    confidence JSONB DEFAULT '{}',
    
    -- 处理信息
    processing_time INTEGER,
    tokens_used INTEGER,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 对话状态跟踪表
CREATE TABLE IF NOT EXISTS conversation_states (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    
    -- 状态信息
    current_task VARCHAR(255),
    current_agent VARCHAR(100),
    context_variables JSONB DEFAULT '{}',
    
    -- 对话流程状态
    flow_state VARCHAR(100),
    step_history JSONB DEFAULT '[]',
    
    -- 用户意图和实体
    last_intent VARCHAR(100),
    entities JSONB DEFAULT '{}',
    
    -- 会话记忆
    short_term_memory JSONB DEFAULT '{}',
    long_term_memory JSONB DEFAULT '{}',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_status ON conversations(status);
CREATE INDEX IF NOT EXISTS idx_conversations_last_activity ON conversations(last_activity);

CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_messages_role ON messages(role);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at);

CREATE INDEX IF NOT EXISTS idx_conversation_states_conversation_id ON conversation_states(conversation_id);
CREATE INDEX IF NOT EXISTS idx_conversation_states_current_agent ON conversation_states(current_agent);
CREATE INDEX IF NOT EXISTS idx_conversation_states_flow_state ON conversation_states(flow_state);

-- 创建更新时间戳的触发器
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_conversations_updated_at 
    BEFORE UPDATE ON conversations 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_conversation_states_updated_at 
    BEFORE UPDATE ON conversation_states 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 添加注释
COMMENT ON TABLE conversations IS '对话表，存储用户对话的基本信息和状态';
COMMENT ON TABLE messages IS '消息表，存储对话中的所有消息';
COMMENT ON TABLE conversation_states IS '对话状态跟踪表，存储对话的详细状态信息';

COMMENT ON COLUMN conversations.context IS '对话上下文信息';
COMMENT ON COLUMN conversations.state IS '对话状态信息';
COMMENT ON COLUMN conversations.user_preferences IS '用户偏好设置';
COMMENT ON COLUMN conversations.learned_patterns IS '学习到的用户模式';

COMMENT ON COLUMN messages.meta_data IS '消息元数据';
COMMENT ON COLUMN messages.confidence IS '置信度信息';
COMMENT ON COLUMN messages.processing_time IS '处理时间(毫秒)';
COMMENT ON COLUMN messages.tokens_used IS '使用的token数量';

COMMENT ON COLUMN conversation_states.context_variables IS '上下文变量';
COMMENT ON COLUMN conversation_states.step_history IS '步骤历史记录';
COMMENT ON COLUMN conversation_states.short_term_memory IS '短期记忆';
COMMENT ON COLUMN conversation_states.long_term_memory IS '长期记忆';
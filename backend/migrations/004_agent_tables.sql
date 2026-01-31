-- Agent Conversation Tables
-- Migration: 004_agent_tables.sql
-- Created: January 2026

-- ============================================================
-- AGENT CONVERSATIONS TABLE
-- Stores conversation sessions for the AI health assistant
-- ============================================================

CREATE TABLE IF NOT EXISTS agent_conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    title TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_agent_conversations_user_id ON agent_conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_agent_conversations_updated ON agent_conversations(user_id, updated_at DESC);

-- RLS Policy
ALTER TABLE agent_conversations ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own conversations"
    ON agent_conversations FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own conversations"
    ON agent_conversations FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own conversations"
    ON agent_conversations FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own conversations"
    ON agent_conversations FOR DELETE
    USING (auth.uid() = user_id);


-- ============================================================
-- AGENT MESSAGES TABLE
-- Stores individual messages within conversations
-- ============================================================

CREATE TABLE IF NOT EXISTS agent_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES agent_conversations(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_agent_messages_conversation ON agent_messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_agent_messages_created ON agent_messages(conversation_id, created_at);

-- RLS Policy
ALTER TABLE agent_messages ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view messages in their conversations"
    ON agent_messages FOR SELECT
    USING (EXISTS (
        SELECT 1 FROM agent_conversations
        WHERE id = agent_messages.conversation_id AND user_id = auth.uid()
    ));

CREATE POLICY "Users can insert messages in their conversations"
    ON agent_messages FOR INSERT
    WITH CHECK (EXISTS (
        SELECT 1 FROM agent_conversations
        WHERE id = agent_messages.conversation_id AND user_id = auth.uid()
    ));

CREATE POLICY "Users can delete messages in their conversations"
    ON agent_messages FOR DELETE
    USING (EXISTS (
        SELECT 1 FROM agent_conversations
        WHERE id = agent_messages.conversation_id AND user_id = auth.uid()
    ));

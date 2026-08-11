## Purpose

提供受限的多轮问答上下文，使用户能够在同一会话中引用前文，同时保证每轮回答仍然只能依赖当前检索到的知识库证据。

## ADDED Requirements

### Requirement: Bounded conversation context

系统 SHALL 支持可选 session_id，并限制会话保留的轮数、字符数和单轮消息长度；超过限制时按明确策略截断最旧上下文。

#### Scenario: Continue a session
- **WHEN** 客户端使用已存在 session_id 发送后续问题
- **THEN** 系统使用限制内的历史上下文辅助查询理解，并返回同一 session_id

### Requirement: Evidence still required

系统 SHALL 不得仅依据会话历史生成事实性回答；每轮回答都必须通过当前知识库检索的相关性判断。

#### Scenario: History contains an answer but retrieval is empty
- **WHEN** 当前问题检索不到可靠证据但历史消息中存在类似答案
- **THEN** 系统仍返回知识库证据不足的拒答，不复用历史答案作为事实

### Requirement: Session cleanup

系统 SHALL 提供删除会话上下文的能力，删除后该 session_id 的历史消息不得继续影响后续问答。

#### Scenario: Delete a session
- **WHEN** 客户端删除已存在 session_id
- **THEN** 系统清除该会话上下文并返回成功状态

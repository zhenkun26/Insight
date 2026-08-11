## Context

当前服务在 `app/main.py` 中组装 catalog、BM25、Milvus、Ollama、检索器和问答服务；文档上传与重建在 HTTP 请求内同步完成，SQLite 只有 documents/chunks 两张基础表，`HybridRetriever` 只接受 query/top_k，问答服务也没有持久化会话或阶段事件。完整需求见 `proposal.md` 及本变更下的 delta specs。

## Goals / Non-Goals

**Goals:**

- 保持现有 MVP 端点兼容，同时让长任务返回 job_id 并可查询进度。
- 让 SQLite 成为本地任务、文档元数据、索引版本和会话状态的唯一轻量控制面。
- 为检索和问答引入统一的 trace/stage 数据结构，既可用于 API 响应也可用于脱敏日志。
- 在没有 Ollama、Milvus 或外部 API 的情况下继续测试核心行为。
- 让 Docker 重启后恢复 catalog、任务、BM25 和 Milvus Lite/远程向量数据配置。

**Non-Goals:**

- 不在本阶段加入用户认证、远程多租户、分布式任务队列或云存储。
- 不默认引入前端框架；先提供稳定 API、SSE 流式协议和可复用的 OpenAPI 文档。
- 不把会话历史作为知识来源，也不为了展示技术栈强制引入 LangGraph；显式可测试的工作流状态对象优先。

## Decisions

### 1. 使用标准库线程执行器承载本地索引任务

索引任务由受控 `ThreadPoolExecutor` 执行，任务状态和进度写入 SQLite；HTTP 请求只负责创建/查询任务。选择它是因为当前部署是单进程 local-first，避免 Celery/Redis 等额外运行时依赖。任务函数保持幂等，进程重启时将 running 任务标记为 failed/retryable，而不是假装恢复。

### 2. 通过 SQLite 增量迁移扩展现有 catalog

启动时使用 `PRAGMA user_version` 和幂等 `ALTER TABLE`/`CREATE TABLE` 补充 metadata、index_jobs、sessions、session_messages 表。所有数据库连接按调用创建，兼容现有测试中的临时数据库，并开启外键约束。

### 3. 用显式 WorkflowState 表达 RAG 阶段

新增工作流服务负责 query_analysis、retrieval、rerank、relevance_check、generation/fallback，返回 `trace_id`、stage_events、retrieval_status 和降级原因。相比直接引入 LangGraph，这种实现更少依赖、更容易在 CI 中 fake 每个节点；未来可把同一状态对象接入 LangGraph，不改变 API 契约。

### 4. 过滤条件在两路召回前统一下发

BM25 索引和向量存储都接受 `document_ids`、`source`、`tags` 过滤参数；无法由底层过滤时在 catalog 侧构建允许的 chunk_id 集合并在融合前过滤，确保关键词和向量不会产生不同的数据边界。分页在融合和阈值过滤之后执行，排序键保持稳定。

### 5. 流式接口采用 SSE 事件

`/chat/stream` 返回 `text/event-stream`，事件类型固定为 `start`、`retrieval`、`source`、`token`、`complete` 或 `error`。当前 Ollama adapter 可以先以单次生成结果拆分为 token 事件，同时保留后续接入真正 Ollama streaming 的边界；客户端不需要依赖纯文本响应。

### 6. 会话只保存短期上下文并与检索严格分离

会话消息保存角色、截断后的内容和时间戳，读取时按字符/轮数预算组装为 query-analysis 辅助上下文。生成 prompt 明确区分 HISTORY 与 CONTEXT，只有 CONTEXT 可作为事实依据；会话默认关闭，删除接口立即清理记录。

### 7. 统一结构化响应而不暴露正文日志

请求中使用或生成 `trace_id`，响应统一携带；日志只写路由、状态、耗时、阶段、结果数量和错误类型。query、正文、Authorization、模型密钥永不进入默认日志。错误响应保留现有 `detail` 兼容形态，并增加稳定的 `error_code`/`trace_id` 字段。

## Risks / Trade-offs

- [线程任务在进程重启时无法继续执行] → 启动恢复 running 任务为 retryable failed，并在 API/README 中说明单进程限制。
- [SQLite 并发写入冲突] → 每次操作短事务、设置 busy timeout、限制 worker 数量，并用并发任务测试验证。
- [向量数据库不支持同等过滤表达式] → 先用 catalog 允许集合做结果过滤，并将过滤降级状态记录到 retrieval stage。
- [SSE 客户端断开后生成仍可能继续] → 第一版只保证结果可终止和错误可表达，后续再增加可取消的 Ollama 请求。
- [旧数据没有新列] → 启动迁移为旧记录提供默认值，切换 embedding 模型时显式标记 `reindex_required`。
- [token 拆分不等于真实模型流式] → 事件协议先稳定下来，并在 adapter 层替换为真正流式实现，不把拆分结果宣传为模型实时输出。

## Migration Plan

1. 发布包含幂等 SQLite 迁移和新字段的版本，旧 documents/chunks 数据自动保留。
2. 首次启动将旧的 `processing` 文档和运行中任务标记为可重试失败，并允许调用 `/documents/reindex` 创建新任务。
3. 先运行 BM25-only 验证，再配置 Ollama/Milvus 重建向量索引；模型变更时不复用旧向量。
4. 回滚时保留数据库备份和现有 API，移除新 worker 启动不会删除已有文档；恢复前一版本后可继续使用 MVP 同步路径。

## Open Questions

无。前端、认证、分布式队列和真实跨编码器模型留作后续独立变更。

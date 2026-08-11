## MODIFIED Requirements

### Requirement: Document management API
系统 SHALL 提供文档上传、列表、删除和重建索引接口，并对非法文件、未知文档和索引失败返回结构化错误；上传和重建 SHALL 返回可查询的任务标识。

#### Scenario: Upload document through API
- **WHEN** 客户端向 `POST /documents/upload` 提交有效文档
- **THEN** API 返回成功状态、文档标识、文件名、块数量和索引状态

#### Scenario: List and delete documents
- **WHEN** 客户端请求 `GET /documents` 或 `DELETE /documents/{document_id}`
- **THEN** API 返回文档状态或删除结果，并使用一致的 JSON 错误结构处理未知标识

#### Scenario: Query an indexing task
- **WHEN** 客户端请求 `GET /jobs/{job_id}`
- **THEN** API 返回任务状态、进度、关联文档、时间戳和可重试信息

### Requirement: Search and chat API
系统 SHALL 提供 `POST /search`、`POST /chat` 和 `POST /chat/stream`，响应至少包含 query、answer（问答时）、sources、retrieval_results 和 latency_ms；搜索 SHALL 支持过滤与分页，问答 SHALL 支持可选 session_id 和 trace_id。

#### Scenario: Search request
- **WHEN** 客户端提交非空 query 到 `/search`
- **THEN** API 返回按相关性排序的检索结果及来源元数据

#### Scenario: Chat request
- **WHEN** 客户端提交非空 query 到 `/chat`
- **THEN** API 返回受上下文约束的 answer、来源、检索结果、原始 query 和毫秒级延迟

#### Scenario: Invalid request error
- **WHEN** 客户端提交空 query、非法分页或不支持的过滤值
- **THEN** API 返回统一结构化 4xx 错误，不触发模型调用

### Requirement: Health endpoint
系统 SHALL 提供 `GET /health`，返回应用状态以及可配置的依赖检查结果，不得因测试环境没有真实模型而伪报依赖健康。

#### Scenario: Health check
- **WHEN** 客户端请求 `/health`
- **THEN** API 返回服务状态、版本或运行信息，以及依赖状态字段

### Requirement: Session and metadata API
系统 SHALL 提供文档元数据更新、会话删除和任务状态查询接口，并为每个请求返回或透传 trace_id。

#### Scenario: Delete conversation session
- **WHEN** 客户端请求 `DELETE /sessions/{session_id}`
- **THEN** API 清除会话上下文并返回成功状态，后续请求不再读取该历史

## MODIFIED Requirements

### Requirement: Search and chat API
系统 SHALL 提供 `POST /search`、`POST /chat` 和 `POST /chat/stream`，响应至少包含 query、answer（问答时）、sources、retrieval_results 和 latency_ms；搜索 SHALL 支持过滤与分页，问答 SHALL 支持可选 session_id 和 trace_id。`/search` 响应 SHALL 额外返回每个检索阶段的真实耗时和状态，未启用阶段必须明确标记为 disabled 或以 null 表示未执行。

#### Scenario: Search request
- **WHEN** 客户端提交非空 query 到 `/search`
- **THEN** API 返回按相关性排序的检索结果及来源元数据，并返回关键词、向量、融合、重排和总耗时阶段信息

#### Scenario: Search stage fallback
- **WHEN** 向量服务不可用但关键词检索完成
- **THEN** `/search` 返回关键词结果、向量阶段的降级状态和实际阶段耗时，不伪造向量分数或零耗时

#### Scenario: Chat request
- **WHEN** 客户端提交非空 query 到 `/chat`
- **THEN** API 返回受上下文约束的 answer、来源、检索结果、原始 query 和毫秒级延迟

#### Scenario: Native streaming request
- **WHEN** 客户端提交请求到 `/chat/stream`
- **THEN** API 以 SSE 返回 start、retrieval、source、token、complete 事件，并在 token 事件中转发可用的模型片段

#### Scenario: Invalid request error
- **WHEN** 客户端提交空 query、非法分页或不支持的过滤值
- **THEN** API 返回统一结构化 4xx 错误，不触发模型调用

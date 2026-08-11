## Context

当前 `IndexJobService` 使用 `ThreadPoolExecutor` 创建任务，但没有保留 future，也没有取消 API。`OllamaClient.generate` 使用 `stream: false`，路由只能把完整回答放入一个 SSE token 事件。现有 SSE 事件契约和 MVP 非流式 `/chat` 需要保持兼容。

## Goals / Non-Goals

**Goals:**

- 取消尚未开始执行的本地任务，并让 running 任务的不可取消语义清晰可验证。
- 通过 Ollama NDJSON 响应实时转发模型片段，保留来源先行、complete 收尾的 SSE 顺序。
- 对流式连接异常提供安全 fallback，不重复调用 LLM，不泄露错误正文。
- 让 fake/mock 模型可以在 CI 中产生确定性的多片段流。

**Non-Goals:**

- 不强杀正在执行的 Python 线程或远程请求；不引入分布式取消协议。
- 不改变 `/chat` 的 JSON 响应，不承诺所有模型都支持原生流式。
- 不实现浏览器前端或 WebSocket。

## Decisions

### 1. 仅允许取消 queued 任务

任务服务保存 `Future` 引用。queued future 可以调用 `future.cancel()`，成功后更新 cancelled；running future 不调用强制终止，API 返回 409。这样不会留下半写入的 BM25/Milvus 状态。

### 2. Ollama adapter 使用 `httpx.stream`

流式请求发送 `stream: true`，逐行解析 JSON 的 `response` 字段，忽略无效空行并在 `done` 时结束。非流式生成继续使用现有方法；不增加依赖。连接或解析失败由 QA 层转为安全 fallback。

### 3. QA 暴露独立的 stream 结果迭代器

先执行一次检索和相关性判断，再通过 `stream_answer` 产出阶段、来源和文本片段，避免 `/chat/stream` 先生成完整答案后重复调用。不能流式的 fake/adapter 使用单片段 fallback，并标记 `stream_mode`。

### 4. SSE 使用稳定事件字段

`start` 增加 `stream_mode`，`token` 包含 `text` 和累计片段序号，`complete` 包含状态与首片段延迟。已有客户端只读取 `text` 时保持兼容。

## Risks / Trade-offs

- [取消请求到达时任务已从 queued 切换为 running] → 返回 409 并保留原任务执行，测试竞态边界。
- [Ollama 返回非 JSON 行或连接中断] → 记录错误类别，发送一个安全完整回答或 error/complete 事件，不输出原始响应。
- [模型首片段很慢] → API 返回 start/retrieval/source 事件，让客户端显示阶段进度；真实首 token 时间由事件记录。
- [客户端断开 SSE] → 生成器停止迭代；第一版不保证取消远程 Ollama 请求，后续可增加 request cancellation。

## Migration Plan

1. 新增 `POST /jobs/{job_id}/cancel`，旧任务记录无需迁移，未完成任务仍按原恢复策略处理。
2. 更新 Ollama adapter 与 SSE 路由；`/chat` 和不支持 stream 的 fake 保持原有行为。
3. 使用 mock 流和本地 Ollama 分别验证成功、异常 fallback 和取消任务。
4. 若回滚，仅移除新取消路由和 stream adapter，原有非流式接口及任务轮询仍可使用。

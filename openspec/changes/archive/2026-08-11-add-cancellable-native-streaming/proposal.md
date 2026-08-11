## Why

完整版自检确认核心链路稳定，但两个用户可见的体验缺口仍然存在：索引任务只能等待或重试，无法取消排队任务；`/chat/stream` 目前只是把完整回答作为一个事件发送，不能降低首 token 等待时间。现在补齐这两个能力，提升本地长任务和交互式问答的可控性。

## What Changes

- 增加索引任务取消接口和 cancelled 状态，明确区分可取消的 queued 任务与已经开始执行的 running 任务。
- 为任务执行器保存 future 引用，取消成功时不执行索引回调，任务状态可审计。
- 为 Ollama 增加原生 NDJSON 流式生成 adapter，并将模型片段按 token 事件转发到 SSE。
- 当模型不支持流式调用或流式连接失败时，保留安全的单事件 fallback，并在工作流状态中标记原因。
- 扩展 SSE 事件结构，增加首片段时间和 stream/fallback 状态；保持 `/chat` 非流式接口兼容。

## Capabilities

### New Capabilities

- 无。

### Modified Capabilities

- `indexing-jobs`: 增加 queued 任务取消和取消结果语义。
- `grounded-question-answering`: 增加原生模型片段流式输出和流式失败 fallback。
- `http-api`: 增加任务取消接口，扩展 `/chat/stream` 事件契约。

## Impact

- 影响 `app/services/jobs.py`、`app/services/ollama.py`、`app/services/qa.py`、`app/api/routes.py`、API schemas 和测试。
- 不增加运行时依赖；继续使用现有 httpx、FastAPI 和线程执行器。
- 需要更新 README 的流式说明、环境变量和已知限制，并同步 OpenSpec 主规格。

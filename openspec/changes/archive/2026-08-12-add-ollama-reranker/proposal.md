## Why

Insight 已有可解释的 RRF 和确定性关键词重排，但 `RERANKER_MODEL` 配置尚未真正接入模型调用，导致用户无法在保持本地部署的前提下使用模型做候选相关性判断。补上这条链路可以让“启用模型、模型失败自动回退”的行为成为可验证的真实能力。

## What Changes

- 增加基于 Ollama `/api/generate` 的可选模型重排器。
- 在 `ENABLE_RERANK=true` 且设置 `RERANKER_MODEL` 时选择模型重排；未设置时继续使用确定性关键词重排。
- 将候选文本和用户问题转换为严格的数值评分请求，解析并限制在 `0..1`。
- 模型不可用、返回非法评分或调用失败时保留原 RRF 顺序，并在检索状态中记录 fallback。
- 扩展 Ollama 客户端以支持指定生成模型，同时不改变问答默认模型。
- 更新 README、环境变量示例和检索测试。

## Capabilities

### New Capabilities

<!-- No new top-level capability; this is an extension of hybrid retrieval. -->

### Modified Capabilities

- `hybrid-retrieval`: 让 `RERANKER_MODEL` 配置实际驱动 Ollama 模型重排，并定义严格评分解析与 fallback 行为。

## Impact

- Affected code: reranker service, Ollama client, service factory, hybrid retrieval tests and documentation.
- Runtime: no new Python dependency; enabled model reranking adds one local Ollama generation request per candidate.
- Compatibility: default `ENABLE_RERANK=false` is unchanged; `ENABLE_RERANK=true` without `RERANKER_MODEL` keeps deterministic keyword reranking.
- External dependency: Ollama must expose the configured model; all failures remain local and do not prevent keyword/vector retrieval from completing.

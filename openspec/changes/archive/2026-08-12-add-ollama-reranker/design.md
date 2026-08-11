## Context

当前混合检索已经支持可选 `SimpleKeywordReranker`，但 `RERANKER_MODEL` 只存在于配置和文档示例，服务工厂没有使用它。Ollama 客户端已有同步生成请求，可复用同一 HTTP 连接配置并通过指定 model 参数调用本地重排模型。

## Goals / Non-Goals

**Goals:**

- 在模型名配置存在时使用本地 Ollama 生成接口为候选片段评分。
- 约束模型输出为单个可解析的 `0..1` 数值，并将解析结果写入 `rerank_score`。
- 将所有候选评分完成后再提交排序，任何单候选失败都回退到调用前结果。
- 不改变默认关闭、关键词重排和向量/关键词融合路径。

**Non-Goals:**

- 不引入第三方 CrossEncoder 或新的 Python 依赖。
- 不把重排模型调用改造成流式生成，也不让模型生成最终回答。
- 不在检索请求失败时重试多次，避免候选数量放大外部调用成本。

## Decisions

### Reuse Ollama generate with an explicit model

扩展 `OllamaClient.generate` 接收可选模型名；问答继续使用客户端默认 LLM，重排器传入 `RERANKER_MODEL`。这样复用现有 HTTP、超时和响应校验代码，而不是新建第二套 Ollama adapter。

### One candidate, one bounded score

每个候选使用一个短 prompt 请求，要求只返回 `0..1` 分数。实现用严格正则从响应中提取单个数值并拒绝额外自然语言或越界值。候选数量已经受 `CANDIDATE_K` 限制，便于控制本地延迟和显存压力。

### Atomic rerank application

先在局部列表中保存 `(result, score)`，全部成功后才修改 `score`、`rerank_score` 并排序。异常直接交给 `HybridRetriever` 的既有 fallback 捕获，确保没有半重排列表。

### Factory selection order

`ENABLE_RERANK=false` 时不创建重排器；开启且 `RERANKER_MODEL` 为空时创建关键词重排器；开启且模型名非空时创建 Ollama 重排器。该顺序保持现有配置兼容，并让 `RERANKER_MODEL` 成为明确的能力开关。

## Risks / Trade-offs

- [Risk] 每个候选增加一次 Ollama 调用 → 使用已有请求超时、候选上限和 opt-in 配置，并在 README 标明延迟成本。
- [Risk] 小模型返回解释文本而非数字 → 严格解析失败即整体回退，不污染原始排序。
- [Risk] 重排模型与生成模型资源竞争 → 默认关闭，用户自行选择模型和候选数量。
- [Risk] Ollama 不可用时难以做真实 CI 验证 → mock 请求/响应契约、失败路径和 fallback 单测；本机 Ollama 探测单独标记结果。

## Migration Plan

1. 默认配置无需迁移；设置 `ENABLE_RERANK=true` 可继续使用关键词重排。
2. 设置 `RERANKER_MODEL=<本地模型>` 后重启服务，新的搜索请求使用模型重排。
3. 若模型响应不稳定或延迟不可接受，清空 `RERANKER_MODEL` 即回退到确定性关键词重排。
4. 不涉及数据库、向量集合或文档重建索引。

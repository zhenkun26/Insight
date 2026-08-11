## ADDED Requirements

### Requirement: Model-backed local reranking
系统 SHALL 在启用重排且配置 `RERANKER_MODEL` 时使用本地模型对每个候选文本相对于查询进行 `0..1` 相关性评分；模型响应不能解析为合法分数时 SHALL 按重排不可用处理。

#### Scenario: Use configured reranker model
- **WHEN** `ENABLE_RERANK=true` 且 `RERANKER_MODEL` 非空，Ollama 返回合法评分
- **THEN** 系统按模型评分重新排序候选，并在结果中保留 `rerank_score`

#### Scenario: Keep deterministic fallback without model name
- **WHEN** `ENABLE_RERANK=true` 但 `RERANKER_MODEL` 为空
- **THEN** 系统使用现有确定性关键词重排，不发起模型请求

#### Scenario: Fallback on model failure
- **WHEN** 模型请求失败、超时或返回无法解析为 `0..1` 的内容
- **THEN** 系统保留进入重排前的候选顺序，并在检索状态中记录 `fallback`，请求仍然成功返回

#### Scenario: Isolate candidate scoring failures
- **WHEN** 某个候选的模型评分失败
- **THEN** 系统不提交部分重排结果，不污染候选原有分数，并按整体重排失败回退

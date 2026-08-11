# hybrid-retrieval Specification

## Purpose

为气象业务问题提供可解释的关键词与语义联合召回，使搜索结果既能匹配专业术语，也能覆盖表达不同但含义相近的资料内容。

## Requirements

### Requirement: Hybrid candidate retrieval
系统 SHALL 对查询分别执行关键词召回和向量召回，并为每个候选结果保留文本块标识、来源元数据和各路检索分数；两路召回 SHALL 接受一致的文档过滤条件。

#### Scenario: Retrieve candidates from both indexes
- **WHEN** 用户提交非空搜索查询且两个索引均可用
- **THEN** 系统合并两路候选结果并返回可解释的分数与来源字段

#### Scenario: Vector service unavailable
- **WHEN** 向量服务不可用但关键词索引可用
- **THEN** 系统按明确的降级策略返回关键词结果，并标记向量召回不可用

### Requirement: Explicit retrieval mode selection
系统 SHALL 支持显式选择 `bm25`、`vector` 或 `hybrid` 检索模式；`bm25` SHALL 只执行关键词召回，`vector` SHALL 只执行向量召回，`hybrid` SHALL 执行两路召回并按既有融合规则合并结果。

#### Scenario: BM25 mode preserves the offline path
- **WHEN** 调用方选择 `bm25` 模式
- **THEN** 系统不调用 Embedding 或向量存储，并返回与现有关键词路径一致的结果和状态

#### Scenario: Vector-only mode disables keyword retrieval
- **WHEN** 调用方选择 `vector` 模式且向量依赖可用
- **THEN** 系统不执行关键词召回，只返回向量候选及其向量分数

#### Scenario: Hybrid mode combines both sources
- **WHEN** 调用方选择 `hybrid` 模式且两路依赖可用
- **THEN** 系统执行关键词和向量召回，并使用既有 RRF 去重、排序、阈值和分页行为

#### Scenario: Invalid mode is rejected
- **WHEN** 调用方提供未支持的检索模式
- **THEN** 系统快速返回配置错误，不执行任何外部模型或向量存储调用

### Requirement: Rank fusion and filtering
系统 SHALL 对两路结果按文本块去重，使用可配置的 RRF 或等价融合规则排序，应用 Top-K 和最低相关性阈值，并支持稳定的 offset/limit 分页。

#### Scenario: Fuse duplicate candidates
- **WHEN** 同一文本块同时命中关键词和向量召回
- **THEN** 结果中只出现一次该文本块，并使用融合后的排序分数

#### Scenario: Filter low relevance results
- **WHEN** 候选结果的融合相关性低于配置阈值
- **THEN** 该结果不得进入最终上下文，并且响应能够表示没有足够相关结果

#### Scenario: Filter by document metadata
- **WHEN** 搜索请求带有文档、来源或标签过滤
- **THEN** 关键词和向量结果都只保留匹配过滤条件的候选

### Requirement: Optional reranking
系统 SHALL 支持通过配置启用或关闭重排序；启用但模型不可用时 SHALL 使用明确记录的候选排序 fallback，而不是伪造重排结果。

#### Scenario: Rerank enabled
- **WHEN** Rerank 已启用且模型可用
- **THEN** 系统使用查询和候选文本计算重排序，并返回更新后的排序结果

#### Scenario: Rerank unavailable
- **WHEN** Rerank 已启用但模型加载或调用失败
- **THEN** 系统保留混合检索顺序，返回可观测的 fallback 状态，并继续完成请求

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

### Requirement: Calibrated vector relevance filtering
向量召回结果 SHALL expose a normalized relevance score in the inclusive `[0, 1]` range. Vector and hybrid retrieval SHALL support an independently configurable vector score threshold; when configured, candidates below that threshold MUST be removed before rank fusion. BM25-only retrieval MUST remain unaffected by this threshold.

#### Scenario: Normalize vector scores
- **WHEN** a vector backend returns a score below `0` or above `1`
- **THEN** the response clamps the exposed vector score into `[0, 1]`

#### Scenario: Filter weak vector candidates before fusion
- **WHEN** vector or hybrid retrieval is configured with `VECTOR_SCORE_THRESHOLD` and a candidate score is lower than the threshold
- **THEN** that candidate does not contribute to fused results or final context

#### Scenario: Preserve BM25 behavior
- **WHEN** the retrieval mode is `bm25`
- **THEN** no vector threshold is applied and the existing keyword-only result behavior is preserved

#### Scenario: Disable vector threshold explicitly
- **WHEN** vector retrieval has no vector score threshold configured
- **THEN** vector candidates are not removed solely because of this new calibration feature

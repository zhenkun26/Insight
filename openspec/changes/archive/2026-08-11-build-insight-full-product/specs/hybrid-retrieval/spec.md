## MODIFIED Requirements

### Requirement: Hybrid candidate retrieval
系统 SHALL 对查询分别执行关键词召回和向量召回，并为每个候选结果保留文本块标识、来源元数据和各路检索分数；两路召回 SHALL 接受一致的文档过滤条件。

#### Scenario: Retrieve candidates from both indexes
- **WHEN** 用户提交非空搜索查询且两个索引均可用
- **THEN** 系统合并两路候选结果并返回可解释的分数与来源字段

#### Scenario: Vector service unavailable
- **WHEN** 向量服务不可用但关键词索引可用
- **THEN** 系统按明确的降级策略返回关键词结果，并标记向量召回不可用

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

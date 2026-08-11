## MODIFIED Requirements

### Requirement: Stage timing and fallback
系统 SHALL 记录 query_analysis、retrieval、rerank、relevance_check、generation 和 fallback 等已执行阶段的耗时与结果状态；搜索响应还 SHALL 暴露关键词召回、向量召回、融合、重排和总检索阶段的真实耗时与状态。

#### Scenario: Vector service fallback
- **WHEN** 向量服务不可用而关键词检索成功
- **THEN** 响应包含向量降级原因和检索阶段耗时，且不得伪造向量分数

#### Scenario: Disabled retrieval stage
- **WHEN** 请求未配置向量检索或重排
- **THEN** 响应将对应阶段标记为 disabled，并将其耗时表示为 null，而不是零毫秒

#### Scenario: Enabled retrieval stage
- **WHEN** 请求执行了关键词、向量、融合或重排阶段
- **THEN** 响应返回该阶段本次请求测得的非负毫秒耗时，并保留阶段状态

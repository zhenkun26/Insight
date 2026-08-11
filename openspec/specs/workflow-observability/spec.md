# workflow-observability Specification

## Purpose

为一次检索或问答请求提供不泄露敏感内容的追踪标识、阶段状态、耗时和降级原因，使本地运行者能够定位索引、检索、重排或模型服务问题。

## Requirements

### Requirement: Request traceability
系统 SHALL 为每次搜索、问答和索引任务生成或接收 trace_id，并在响应、结构化日志和任务记录中保持一致。

#### Scenario: Client supplied trace id
- **WHEN** 客户端提交合法的 X-Request-ID
- **THEN** 系统在响应和日志中返回同一追踪标识

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

### Requirement: Sensitive log protection
系统 SHALL 默认不记录完整用户问题、完整文档正文、模型密钥或外部服务认证信息。

#### Scenario: Request is logged
- **WHEN** 搜索或问答请求完成
- **THEN** 日志只包含 trace_id、路由、状态、耗时、结果数量和错误类别等脱敏字段

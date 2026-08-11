## Purpose

为文档解析、切分、向量化和索引写入提供可追踪、可重试且幂等的任务生命周期，避免长时间索引请求阻塞客户端或留下不可诊断的半成品状态。

## ADDED Requirements

### Requirement: Index task lifecycle

系统 SHALL 为每次上传、重建或重试操作创建可查询的索引任务，并维护 queued、running、succeeded、failed 和 cancelled 状态中的一种。

#### Scenario: Query a running task
- **WHEN** 客户端查询仍在执行的索引任务
- **THEN** 系统返回任务状态、文档标识、已处理块数、总块数和创建/更新时间

#### Scenario: Failed task is diagnosable
- **WHEN** 解析、Embedding 或向量写入失败
- **THEN** 任务进入 failed 状态，返回脱敏错误摘要和可重试标记，不保留不可用的索引内容

### Requirement: Idempotent indexing

系统 SHALL 使用文档内容指纹、索引配置和 Embedding 模型标识判断重复任务，重复提交不得产生重复文本块或重复向量。

#### Scenario: Repeated reindex request
- **WHEN** 客户端对相同文档和相同索引配置重复发起重建
- **THEN** 系统复用已有成功任务或返回等价结果，并保持索引内容唯一

### Requirement: Retry failed task

系统 SHALL 允许客户端对可恢复失败的任务发起重试，并为重试创建新的任务记录且保留原任务关联关系。

#### Scenario: Retry a recoverable failure
- **WHEN** 客户端重试一个可恢复的 failed 任务
- **THEN** 系统返回新的任务标识，原任务保持可审计，新的任务从 queued 状态开始

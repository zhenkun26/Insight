## MODIFIED Requirements

### Requirement: Index task lifecycle
系统 SHALL 为每次上传、重建或重试操作创建可查询的索引任务，并维护 queued、running、succeeded、failed、cancelled 状态中的一种；任务状态转换 SHALL 可审计且不得把未执行的任务误报为成功。

#### Scenario: Query a running task
- **WHEN** 客户端查询仍在执行的索引任务
- **THEN** 系统返回任务状态、文档标识、已处理块数、总块数和创建/更新时间

#### Scenario: Failed task is diagnosable
- **WHEN** 解析、Embedding 或向量写入失败
- **THEN** 任务进入 failed 状态，返回脱敏错误摘要和可重试标记，不保留不可用的索引内容

#### Scenario: Cancel a queued task
- **WHEN** 客户端取消尚未开始执行的 queued 任务
- **THEN** 任务进入 cancelled 状态，索引回调不被执行，并返回取消时间和 trace_id

#### Scenario: Reject cancellation of running task
- **WHEN** 客户端取消已经开始执行的 running 任务
- **THEN** API 返回明确的不可取消错误，任务继续由当前 worker 完成或失败，不伪造 cancelled 状态

## ADDED Requirements

### Requirement: Cancel task endpoint
系统 SHALL 提供任务取消操作，并保持取消请求幂等。

#### Scenario: Cancel an already cancelled task
- **WHEN** 客户端重复取消同一个 cancelled 任务
- **THEN** 系统返回该任务当前状态且不创建新任务

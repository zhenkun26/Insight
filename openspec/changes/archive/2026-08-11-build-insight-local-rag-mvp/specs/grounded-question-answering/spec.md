## Purpose

让问答结果严格受本地知识库证据约束，向用户返回可核验的来源引用，并在检索证据不足时安全拒答。

## ADDED Requirements

### Requirement: Grounded answer generation
系统 SHALL 只将通过相关性判断的检索文本块作为生成上下文，并要求生成回答引用一个或多个实际来源。

#### Scenario: Answer with evidence
- **WHEN** 查询获得达到阈值的检索上下文且模型调用成功
- **THEN** 系统返回回答、原始查询、延迟、检索结果和包含文件名及文本块标识的来源列表

### Requirement: Insufficient evidence refusal
系统 SHALL 在没有达到相关性阈值的检索结果时返回固定语义的拒答，明确说明当前知识库没有足够信息，并且不得调用生成模型生成猜测内容。

#### Scenario: No reliable context
- **WHEN** 检索结果为空或全部低于阈值
- **THEN** 系统返回“当前知识库中没有足够信息”语义的答案和空或明确标记为不可用的来源

### Requirement: Model and workflow failure handling
系统 SHALL 将模型超时、服务不可用和无效响应转换为可识别的 API 错误或安全 fallback，并不得把错误信息伪装成知识库答案。

#### Scenario: LLM unavailable
- **WHEN** Ollama 不可用或请求超时
- **THEN** 系统返回明确的服务不可用响应，保留可诊断的请求日志，不暴露敏感内容

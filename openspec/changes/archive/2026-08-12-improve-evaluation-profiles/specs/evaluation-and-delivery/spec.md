## ADDED Requirements

### Requirement: Comparable retrieval evaluation profiles
评估脚本 SHALL 提供默认无外部服务的 `disabled` profile，并支持显式选择 `keyword` 或 `ollama` 重排 profile；输出 SHALL 记录实际 profile、模型配置和请求参数。

#### Scenario: Run the default offline profile
- **WHEN** 用户不指定 profile 运行评估
- **THEN** 脚本只使用本地可复现检索路径，不调用 Ollama 或 Milvus，并将 profile 记录为 `disabled`

#### Scenario: Run keyword reranking profile
- **WHEN** 用户显式选择 `keyword` profile
- **THEN** 脚本使用确定性关键词重排，并在输出中记录该 profile 和真实测得指标

#### Scenario: Run Ollama reranking profile
- **WHEN** 用户显式选择 `ollama` profile 并提供可用的 Ollama 地址和模型
- **THEN** 脚本通过本地模型完成评估，并记录模型名、地址、超时和真实响应延迟

### Requirement: Stage-level retrieval timings
检索评估 SHALL 记录关键词召回、向量召回、融合、重排和总检索阶段耗时；每条问题和汇总结果都 SHALL 能区分可执行阶段与未启用阶段。

#### Scenario: Report disabled stages
- **WHEN** 运行默认 BM25-only profile
- **THEN** 输出标记向量和重排阶段为 disabled，并记录关键词与总耗时

#### Scenario: Report enabled rerank timing
- **WHEN** 运行启用重排的 profile
- **THEN** 每条问题和汇总输出包含重排阶段耗时，并且平均值来自本次实际运行

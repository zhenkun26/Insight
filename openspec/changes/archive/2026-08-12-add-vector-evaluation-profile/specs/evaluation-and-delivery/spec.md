## ADDED Requirements

### Requirement: Explicit vector retrieval evaluation
评估脚本 SHALL 支持 `bm25`、`vector` 和 `hybrid` 检索 profile；默认仍为无外部服务的 `bm25`。`vector`/`hybrid` profile SHALL 记录 Embedding 模型、向量后端、URI、集合和真实向量阶段耗时。

#### Scenario: Run the default BM25 profile
- **WHEN** 用户未指定向量 profile 运行评估
- **THEN** 脚本不调用 Ollama 或 Milvus，并保持现有 BM25 指标和输出字段

#### Scenario: Run vector profile with a fake or memory backend
- **WHEN** 测试或本地实验选择 `vector` profile 并提供可用 Embedding adapter 与内存向量后端
- **THEN** 评估只执行向量召回，并将 vector 阶段状态和耗时写入每条结果及汇总

#### Scenario: Run hybrid profile with Milvus Lite
- **WHEN** 用户显式提供 Ollama Embedding、Milvus Lite URI 和 `hybrid` profile
- **THEN** 脚本真实建立向量集合、执行混合检索，并记录模型、后端、URI、集合和实际指标

#### Scenario: Reject incomplete vector configuration
- **WHEN** 用户选择 `vector` 或 `hybrid` 但缺少 Embedding 模型、向量后端或必要 URI
- **THEN** 脚本快速返回明确配置错误，不输出成功评估指标

#### Scenario: Keep CI independent from external services
- **WHEN** CI 使用默认评估命令
- **THEN** 评估仅运行 BM25 profile，Ollama、Milvus 和外部网络均不是前置条件

# evaluation-and-delivery Specification

## Purpose

让项目可以在不依赖真实 Ollama、Milvus 或外部 API 的 CI 环境中验证核心行为，并通过可复现脚本记录真实检索评估结果和本地部署方式。

## Requirements

### Requirement: Deterministic automated tests
项目 SHALL 提供覆盖解析、切分、元数据、BM25、向量接口、混合融合、拒答、引用、健康检查、上传和 mock 问答的自动化测试，并覆盖任务生命周期、过滤、会话约束和流式事件。

#### Scenario: Run tests without external services
- **WHEN** CI 执行项目测试且 Ollama、Milvus 和外部 API 均不可用
- **THEN** 测试仍可完成核心逻辑验证，外部连接由 mock、fake 或内存实现替代

### Requirement: Reproducible retrieval evaluation
项目 SHALL 提供包含 10 至 20 条问题及期望命中内容的评估数据和脚本，计算至少一种命中率指标与平均响应时间，并记录模型、参数和测试日期；评估 SHALL 另外报告拒答样例和阶段耗时。

#### Scenario: Run evaluation
- **WHEN** 用户按 README 指令运行评估脚本
- **THEN** 脚本输出由实际运行计算得到的 Recall@K、MRR 或命中率、平均延迟和运行配置，不生成硬编码指标

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

### Requirement: Stage-level retrieval timings
检索评估 SHALL 记录关键词召回、向量召回、融合、重排和总检索阶段耗时；每条问题和汇总结果都 SHALL 能区分可执行阶段与未启用阶段。

#### Scenario: Report disabled stages
- **WHEN** 运行默认 BM25-only profile
- **THEN** 输出标记向量和重排阶段为 disabled，并记录关键词与总耗时

#### Scenario: Report enabled rerank timing
- **WHEN** 运行启用重排的 profile
- **THEN** 每条问题和汇总输出包含重排阶段耗时，并且平均值来自本次实际运行

### Requirement: Local delivery documentation
项目 SHALL 提供 README、`.env.example`、Dockerfile、Docker Compose 和 GitHub Actions CI，文档必须说明模型准备、Milvus 启动、导入、问答、测试、评估和已知限制；部署配置 SHALL 持久化目录并提供可验证的健康检查。

#### Scenario: Run CI
- **WHEN** GitHub Actions 在干净环境中运行
- **THEN** CI 安装依赖、执行格式检查、导入检查和 pytest，且不要求真实模型或向量数据库服务

#### Scenario: Persist local runtime state
- **WHEN** 用户重启 Docker Compose 服务
- **THEN** 文档目录、任务记录和向量数据从挂载目录恢复，不要求重新上传所有资料

### Requirement: Refusal calibration reporting
The retrieval evaluation SHALL record the effective vector score threshold for vector-capable profiles and SHALL report refusal calibration metrics for questions marked as requiring refusal, including refusal count, false-positive answer count, and false-positive rate. Metrics MUST be computed from the current run rather than hard-coded.

#### Scenario: Report calibrated refusal outcomes
- **WHEN** an evaluation run contains refusal questions
- **THEN** its output includes the configured vector threshold, refusal count, false-positive answer count, and calculated false-positive rate

#### Scenario: Evaluate a threshold without vector retrieval
- **WHEN** the default BM25 evaluation profile is run
- **THEN** the output preserves BM25 metrics and records that no vector threshold is active

#### Scenario: Sweep thresholds for local calibration
- **WHEN** a user reruns a vector or hybrid evaluation with different vector threshold values
- **THEN** each output records its own threshold and measured refusal calibration metrics so the runs can be compared

#### Scenario: Handle an evaluation set without refusal questions
- **WHEN** an evaluation run contains no refusal questions
- **THEN** the refusal calibration count is zero and the false-positive rate is reported as unavailable rather than fabricated
